"""Fixture-only tests: no subprocess actually runs, no network, no model.
Proves the redaction/classification contract in qualify_connection_account.py
- in particular that a fake secret never leaks, invalid JSON and command
failure produce an explicit failure status and non-zero exit, and "not
connected" is reported honestly rather than as a false success.
"""
import json
import unittest
from unittest.mock import patch

import qualify_connection_account as qca


class ClassifyVersionTests(unittest.TestCase):
    def test_matching_version_is_ok(self):
        self.assertEqual(qca.classify_version(0, "2.1.114 (Claude Code)\n"), {"status": "ok", "version": "2.1.114 (Claude Code)"})

    def test_command_failure_never_becomes_ok(self):
        self.assertEqual(qca.classify_version(1, "2.1.114 (Claude Code)"), {"status": "command_failed", "exitCode": 1})

    def test_garbage_output_is_unexpected_format_never_printed_raw(self):
        result = qca.classify_version(0, "not a version string at all")
        self.assertEqual(result, {"status": "unexpected_format"})
        self.assertNotIn("not a version string", json.dumps(result))


class ClassifyStderrTests(unittest.TestCase):
    def test_empty_stderr_is_none(self):
        self.assertEqual(qca.classify_stderr(""), {"kind": "none"})

    def test_known_safe_missing_profile_message_is_classified_safely(self):
        text = (
            "Claude configuration file not found at: /home/openhands/.claude.json\n"
            "A backup file exists at: /home/openhands/.claude/backups/x\n"
            "You can manually restore it by running: cp ... ...\n"
        )
        self.assertEqual(qca.classify_stderr(text), {"kind": "profile_cache_missing_backup_available", "occurrences": 1})

    def test_candidate_cli_double_message_with_quoted_restore_command_is_classified_safely(self):
        # Observed shape from the candidate's newer claude-agent-acp/CLI
        # (0.84.0/2.1.284): the same benign message, reworded (quoted `cp`
        # command, timestamped backup name) and printed twice with a blank
        # line between - never a secret, only fixed file paths.
        text = (
            "Claude configuration file not found at: /home/runner/.claude.json\n"
            "A backup file exists at: /home/runner/.claude/backups/.claude.json.backup.1234567890123\n"
            'You can manually restore it by running: cp "/home/runner/.claude/backups/.claude.json.backup.1234567890123" "/home/runner/.claude.json"\n'
            "\n"
            "Claude configuration file not found at: /home/runner/.claude.json\n"
            "A backup file exists at: /home/runner/.claude/backups/.claude.json.backup.1234567890123\n"
            'You can manually restore it by running: cp "/home/runner/.claude/backups/.claude.json.backup.1234567890123" "/home/runner/.claude.json"\n'
        )
        self.assertEqual(qca.classify_stderr(text), {"kind": "profile_cache_missing_backup_available", "occurrences": 2})

    def test_three_repeats_of_the_known_safe_block_are_not_classified_safe(self):
        # The known-safe pattern is capped at the 1-2 occurrences actually
        # observed - a third repeat (or any shape not exactly described) must
        # still refuse rather than being generalized into "any number is fine".
        block = (
            "Claude configuration file not found at: /x\n"
            "A backup file exists at: /y\n"
            "You can manually restore it by running: cp /y /x"
        )
        text = "\n\n".join([block, block, block])
        result = qca.classify_stderr(text)
        self.assertEqual(result["kind"], "unclassified")

    def test_known_safe_substrings_with_unexpected_interleaved_content_are_not_classified_safe(self):
        # Review-caught regression: a loose "both substrings present
        # anywhere" check would wrongly accept this as the known-safe
        # template even though it carries an injected, unverified line.
        text = (
            "Claude configuration file not found at: /x\n"
            "unexpected injected line that was never verified\n"
            "A backup file exists at: /y\n"
            "You can manually restore it by running: cp\n"
        )
        result = qca.classify_stderr(text)
        self.assertEqual(result["kind"], "unclassified")
        self.assertEqual(result["length"], len(text.strip()))

    def test_unrecognized_stderr_is_unclassified_by_length_only_never_content(self):
        fake_secret = "sk-ant-totally-fake-secret-oauth-token-abc123"
        text = f"provider error: invalid credential {fake_secret}"
        result = qca.classify_stderr(text)
        self.assertEqual(result["kind"], "unclassified")
        self.assertEqual(result["length"], len(text))
        self.assertNotIn(fake_secret, json.dumps(result))


class ClassifyAuthStatusTests(unittest.TestCase):
    def test_connected_pro_subscription_reports_whitelisted_values_only(self):
        stdout = json.dumps({
            "loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
            "subscriptionType": "pro", "email": "someone@example.com",
            "orgId": "06e7421e-6478-4124-b2fa-3aff4368260a", "orgName": "Someone's Org",
        })
        result = qca.classify_auth_status(0, stdout, "")
        self.assertTrue(result["ok"])
        self.assertTrue(result["connected"])
        self.assertEqual(result["fields"], {
            "loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro",
        })
        self.assertEqual(result["otherFieldsPresent"], ["email", "orgId", "orgName"])
        # Decisive leak check: none of the raw personal/org values appear anywhere.
        dumped = json.dumps(result)
        self.assertNotIn("someone@example.com", dumped)
        self.assertNotIn("06e7421e", dumped)
        self.assertNotIn("Someone's Org", dumped)

    def test_not_connected_is_reported_honestly_never_as_false_success(self):
        stdout = json.dumps({"loggedIn": False, "authMethod": None})
        result = qca.classify_auth_status(0, stdout, "")
        self.assertTrue(result["ok"], "a clean, valid, not-connected response is still a fully classified diagnostic")
        self.assertFalse(result["connected"])
        self.assertEqual(result["fields"]["loggedIn"], False)

    def test_fake_secret_smuggled_into_a_whitelisted_field_is_rejected_not_leaked(self):
        fake_secret = "eyJhbGciOiJIUzI1NiJ9.fake.jwt.payload.that.is.way.too.long.to.be.a.real.category"
        stdout = json.dumps({"loggedIn": True, "authMethod": fake_secret, "apiProvider": "firstParty", "subscriptionType": "pro"})
        result = qca.classify_auth_status(0, stdout, "")
        self.assertTrue(result["ok"])
        self.assertEqual(result["fields"]["authMethod"], {"rejectedUnsafeShape": True, "length": len(fake_secret)})
        self.assertNotIn(fake_secret, json.dumps(result))

    def test_command_failure_is_explicit_and_never_ok(self):
        result = qca.classify_auth_status(1, "", "some provider error")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "command_failed")
        self.assertEqual(result["exitCode"], 1)

    def test_invalid_json_is_explicit_and_never_ok(self):
        for bad_stdout in ("not json", "{broken", "[1,2,3]", "", "null", '"just a string"'):
            with self.subTest(bad_stdout=bad_stdout):
                result = qca.classify_auth_status(0, bad_stdout, "")
                self.assertFalse(result["ok"])
                self.assertEqual(result["reason"], "invalid_json")

    def test_unclassified_stderr_refuses_even_with_valid_json_and_never_leaks_it(self):
        stdout = json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"})
        fake_secret = "sk-totally-fake-leaked-value-123456789"
        result = qca.classify_auth_status(0, stdout, f"unexpected provider error containing {fake_secret}")
        self.assertFalse(result["ok"], "an unclassified stderr must block a clean result even when stdout looks fine")
        self.assertEqual(result["reason"], "unclassified_stderr")
        self.assertNotIn(fake_secret, json.dumps(result))


class MainExitCodeTests(unittest.TestCase):
    """Patches qualify_connection_account.run so no real subprocess ever
    spawns - fixtures only, never a real claude-agent-acp invocation."""

    def _run_main_with(self, version_outcome, auth_outcome):
        calls = {"n": 0}

        def fake_run(args, timeout=20):
            calls["n"] += 1
            return version_outcome if "--version" in args else auth_outcome

        with patch.object(qca, "run", side_effect=fake_run):
            with self.assertRaises(SystemExit) as caught:
                qca.main()
        return caught.exception.code

    def test_clean_connected_result_exits_ok(self):
        code = self._run_main_with(
            (0, "2.1.114 (Claude Code)\n", ""),
            (0, json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"}), ""),
        )
        self.assertEqual(code, qca.EXIT_OK)

    def test_clean_not_connected_result_also_exits_ok_not_an_error(self):
        code = self._run_main_with(
            (0, "2.1.114 (Claude Code)\n", ""),
            (0, json.dumps({"loggedIn": False}), ""),
        )
        self.assertEqual(code, qca.EXIT_OK)

    def test_auth_command_failure_is_nonzero_exit(self):
        code = self._run_main_with(
            (0, "2.1.114 (Claude Code)\n", ""),
            (1, "", "boom"),
        )
        self.assertEqual(code, qca.EXIT_COMMAND_FAILED)

    def test_invalid_json_is_nonzero_exit(self):
        code = self._run_main_with(
            (0, "2.1.114 (Claude Code)\n", ""),
            (0, "not json", ""),
        )
        self.assertEqual(code, qca.EXIT_INVALID_JSON)

    def test_unclassified_stderr_is_nonzero_exit(self):
        code = self._run_main_with(
            (0, "2.1.114 (Claude Code)\n", ""),
            (0, json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"}), "weird provider text"),
        )
        self.assertEqual(code, qca.EXIT_UNCLASSIFIED_STDERR)

    def test_unexpected_version_format_is_nonzero_exit_before_even_checking_auth(self):
        code = self._run_main_with(
            (0, "garbage", ""),
            (0, json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"}), ""),
        )
        self.assertEqual(code, qca.EXIT_UNEXPECTED_VERSION)

    def test_version_command_run_failure_is_command_failed_exit_never_unexpected_format(self):
        # Review-caught regression: a non-zero/failed --version invocation
        # must report EXIT_COMMAND_FAILED, not be folded into the same
        # EXIT_UNEXPECTED_VERSION bucket as garbled-but-successful output.
        code = self._run_main_with(
            (1, "", "boom"),
            (0, json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"}), ""),
        )
        self.assertEqual(code, qca.EXIT_COMMAND_FAILED)

    def test_main_never_prints_a_fake_secret_anywhere_on_stdout(self):
        fake_secret = "sk-ant-totally-fake-should-never-appear-9999999999"
        calls = {"n": 0}

        def fake_run(args, timeout=20):
            calls["n"] += 1
            if "--version" in args:
                return (0, "2.1.114 (Claude Code)\n", "")
            return (0, json.dumps({"loggedIn": True, "authMethod": fake_secret, "apiProvider": "firstParty", "subscriptionType": "pro"}), "")

        import io
        import contextlib
        output = io.StringIO()
        with patch.object(qca, "run", side_effect=fake_run), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit):
                qca.main()
        self.assertNotIn(fake_secret, output.getvalue())


if __name__ == "__main__":
    unittest.main()
