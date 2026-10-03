"""Fixture-only tests for qualify_trivial_mission.py's gate logic. Never
spawns claude-agent-acp, never touches a real authorization/budget file
outside a temporary fixture - proves the authorization/budget gate refuses
precisely and deterministically before any real model call could happen.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import qualify_trivial_mission as qtm

VALID_AUTHORIZATION = {
    "profileId": "claude-local-candidate",
    "policySha256": "a" * 64,
    "policyRoot": "/etc/oria-hq/provider-policies",
    "gatewayRoot": "/etc/oria-hq/provider-gateway",
}
VALID_BUDGET = {"maxCostCents": 1, "maxTokens": 1, "maxIterations": 1, "timeoutSeconds": 30}


class _EnvVar:
    """Context manager: set (or unset) one env var for the block's duration,
    always restoring the prior value afterward - never leaks across tests."""

    def __init__(self, name, value):
        self._name = name
        self._value = value
        self._had_prior = name in os.environ
        self._prior = os.environ.get(name)

    def __enter__(self):
        if self._value is None:
            os.environ.pop(self._name, None)
        else:
            os.environ[self._name] = self._value
        return self

    def __exit__(self, *exc):
        if self._had_prior:
            os.environ[self._name] = self._prior
        else:
            os.environ.pop(self._name, None)
        return False


class LoadAuthorizationTests(unittest.TestCase):
    def test_missing_env_var_is_named_exactly(self):
        with _EnvVar(qtm.AUTH_FILE_ENV, None):
            result, error = qtm.load_authorization()
        self.assertIsNone(result)
        self.assertIn(qtm.AUTH_FILE_ENV, error)
        self.assertIn("not set", error)

    def test_valid_authorization_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "authorization.json"
            path.write_text(json.dumps(VALID_AUTHORIZATION))
            with _EnvVar(qtm.AUTH_FILE_ENV, str(path)):
                result, error = qtm.load_authorization()
            self.assertIsNone(error)
            self.assertEqual(result["profileId"], "claude-local-candidate")

    def test_invalid_shape_is_refused_not_coerced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "authorization.json"
            path.write_text(json.dumps({"profileId": "x"}))  # missing required fields
            with _EnvVar(qtm.AUTH_FILE_ENV, str(path)):
                result, error = qtm.load_authorization()
            self.assertIsNone(result)
            self.assertIn("validate_authorization", error)

    def test_malformed_json_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "authorization.json"
            path.write_text("not json")
            with _EnvVar(qtm.AUTH_FILE_ENV, str(path)):
                result, error = qtm.load_authorization()
            self.assertIsNone(result)
            self.assertIn("not valid JSON", error)


class LoadBudgetTests(unittest.TestCase):
    def test_missing_env_var_is_named_exactly(self):
        with _EnvVar(qtm.BUDGET_FILE_ENV, None):
            result, error = qtm.load_budget()
        self.assertIsNone(result)
        self.assertIn(qtm.BUDGET_FILE_ENV, error)

    def test_valid_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            path.write_text(json.dumps(VALID_BUDGET))
            with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                result, error = qtm.load_budget()
            self.assertIsNone(error)
            self.assertEqual(result, VALID_BUDGET)

    def test_missing_required_field_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            incomplete = dict(VALID_BUDGET)
            del incomplete["maxTokens"]
            path.write_text(json.dumps(incomplete))
            with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                result, error = qtm.load_budget()
            self.assertIsNone(result)

    def test_extra_field_is_refused_never_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            extra = dict(VALID_BUDGET, unexpectedField=1)
            path.write_text(json.dumps(extra))
            with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                result, error = qtm.load_budget()
            self.assertIsNone(result)

    def test_non_positive_values_are_refused(self):
        for field in ("maxCostCents", "maxTokens", "maxIterations", "timeoutSeconds"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "budget.json"
                    bad = dict(VALID_BUDGET, **{field: 0})
                    path.write_text(json.dumps(bad))
                    with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                        result, error = qtm.load_budget()
                    self.assertIsNone(result, f"{field}=0 must be refused")

    def test_boolean_is_refused_even_though_it_is_an_int_subclass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            bad = dict(VALID_BUDGET, maxIterations=True)
            path.write_text(json.dumps(bad))
            with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                result, error = qtm.load_budget()
            self.assertIsNone(result)

    def test_max_iterations_above_one_is_refused_because_script_sends_exactly_one_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.json"
            bad = dict(VALID_BUDGET, maxIterations=5)
            path.write_text(json.dumps(bad))
            with _EnvVar(qtm.BUDGET_FILE_ENV, str(path)):
                result, error = qtm.load_budget()
            self.assertIsNone(result)
            self.assertIn("exactly one session/prompt", error)


class VerifyMissionTests(unittest.TestCase):
    def test_missing_file_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, detail = qtm.verify_mission(Path(tmp))
            self.assertFalse(ok)
            self.assertIn("not created", detail)

    def test_wrong_content_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / qtm.EXPECTED_FILENAME).write_text("something else")
            ok, detail = qtm.verify_mission(Path(tmp))
            self.assertFalse(ok)

    def test_exact_expected_content_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / qtm.EXPECTED_FILENAME).write_text(qtm.EXPECTED_CONTENT)
            ok, detail = qtm.verify_mission(Path(tmp))
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
