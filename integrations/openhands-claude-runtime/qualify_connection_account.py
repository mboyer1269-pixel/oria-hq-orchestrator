"""Safe, redacted, testable classification of claude-agent-acp's official
`--version` and `--cli auth status --json` outputs.

Replaces an earlier shell+node probe that `cat`-ed stderr and `--version`
output raw despite a "no secrets" promise, and had no real exit-code
contract (it always ended on an `echo`, masking failure). Caught in review
before that probe was ever run against a built candidate.

Doctrine, enforced here, not just documented:
  - Only four field VALUES are ever printed: loggedIn, authMethod,
    apiProvider, subscriptionType - the same whitelist already reviewed in
    local-runtime-probe.ts (CLAUDE_AUTH_EVIDENCE_FIELDS). Every other field
    (email, orgId, orgName, anything else) is reported by NAME only, never
    by value.
  - A whitelisted field is still rejected (never printed) if its own VALUE
    doesn't match a short, safe shape (<=32 chars, plain charset) - this is
    exactly how a fake-secret-shaped value smuggled into a normally-safe
    field gets caught instead of leaked.
  - stderr is NEVER printed raw. Only a small set of known-safe message
    shapes get a named, safe summary; anything else is reported as
    "unclassified" by LENGTH only, and treated as a diagnostic failure
    (never guessed to be harmless).
  - --version output is validated against a strict pattern before being
    treated as safe to print; anything else is "unexpected_format", never
    printed raw.
  - Exit code is the real, authoritative signal to callers:
      0  = a FULLY CLASSIFIED diagnostic. connected=True and connected=False
           are BOTH success at this level - "not connected" is an honest,
           expected finding, never a script bug, and is never reported as
           anything resembling success when it is false.
      2  = either the auth-status command OR the --version command itself
           failed to run (non-zero exit, timeout, spawn error) - the two
           probes share this code since both mean "we could not even get a
           response to classify", distinct from getting a response that
           doesn't match the expected shape.
      3  = the command's stdout was not valid JSON.
      4  = stderr was present and could not be safely classified - refused,
           not guessed, not printed.
      5  = --version ran successfully but its output did not match the
           expected format (never a run failure - that is code 2).
"""
import json
import re
import subprocess
import sys

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+ \(Claude Code\)$")

# Only these fields' VALUES are ever printed.
VALUE_FIELDS = {
    "loggedIn": bool,
    "authMethod": str,
    "apiProvider": str,
    "subscriptionType": str,
}
SAFE_STRING_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{1,32}$")

# Anchored start-to-end so unexpected content before/within/after the known
# template is never mistaken for it - a loose substring match would let a
# stderr blob that merely CONTAINS these two phrases, interleaved with
# anything else, slip past as "safe". Observed in both the old (2.1.114,
# printed once) and candidate (2.1.284, printed twice back-to-back with a
# blank line between) CLI builds - same three-line message, just reworded
# (quoted `cp` restore command, timestamped backup filename) and repeated.
# Capped at exactly 1-2 occurrences: this is what both versions actually do,
# not a generalized "any number of repeats" - a third occurrence, or any
# content this does not exactly describe, must still refuse, not guess.
_KNOWN_SAFE_STDERR_BLOCK = (
    r"Claude configuration file not found at: [^\n]+\n"
    r"A backup file exists at: [^\n]+\n"
    r"You can manually restore it by running: [^\n]+"
)
KNOWN_SAFE_STDERR_PATTERN = re.compile(
    r"\A(" + _KNOWN_SAFE_STDERR_BLOCK + r")(?:\n+(" + _KNOWN_SAFE_STDERR_BLOCK + r"))?\Z"
)

EXIT_OK = 0
EXIT_COMMAND_FAILED = 2
EXIT_INVALID_JSON = 3
EXIT_UNCLASSIFIED_STDERR = 4
EXIT_UNEXPECTED_VERSION = 5


def run(args, timeout=20):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except OSError as error:
        return None, "", f"spawn_error:{type(error).__name__}"


def classify_version(exit_code, stdout):
    if exit_code != 0:
        return {"status": "command_failed", "exitCode": exit_code}
    stripped = stdout.strip()
    if VERSION_PATTERN.match(stripped):
        return {"status": "ok", "version": stripped}
    return {"status": "unexpected_format"}


def classify_stderr(stderr):
    """Never returns the raw text. Only a small, named set of KNOWN-SAFE
    shapes get a safe summary; anything else is reported as present-but-
    unclassified, by length only, never content."""
    text = stderr.strip()
    if not text:
        return {"kind": "none"}
    match = KNOWN_SAFE_STDERR_PATTERN.match(text)
    if match:
        occurrences = sum(1 for group in match.groups() if group is not None)
        return {"kind": "profile_cache_missing_backup_available", "occurrences": occurrences}
    return {"kind": "unclassified", "length": len(text)}


def classify_auth_status(exit_code, stdout, stderr):
    stderr_summary = classify_stderr(stderr)
    if exit_code != 0:
        return {"ok": False, "reason": "command_failed", "exitCode": exit_code, "stderr": stderr_summary}
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return {"ok": False, "reason": "invalid_json", "stderr": stderr_summary}
    if not isinstance(parsed, dict):
        return {"ok": False, "reason": "invalid_json", "stderr": stderr_summary}
    if stderr_summary["kind"] == "unclassified":
        # Refuse to proceed on an error channel that cannot be safely
        # classified - never guess that it is harmless, never print it.
        return {"ok": False, "reason": "unclassified_stderr", "stderr": stderr_summary}

    fields = {}
    for key, expected_type in VALUE_FIELDS.items():
        if key not in parsed:
            continue
        value = parsed[key]
        # bool is a subclass of int in Python, but never the reverse: this
        # guards both directions explicitly rather than relying on isinstance
        # alone, so a stray 0/1 int can never pass as the loggedIn boolean.
        type_ok = (
            isinstance(value, bool) if expected_type is bool
            else isinstance(value, expected_type) and not isinstance(value, bool)
        )
        if not type_ok:
            fields[key] = {"unexpectedType": True}
            continue
        if isinstance(value, str) and not SAFE_STRING_PATTERN.match(value):
            # A whitelisted field with an out-of-shape value (too long, odd
            # characters) is never printed raw - this is the "fake secret
            # smuggled into a normally-safe field" case.
            fields[key] = {"rejectedUnsafeShape": True, "length": len(value)}
            continue
        fields[key] = value

    other_present = sorted(set(parsed.keys()) - set(VALUE_FIELDS.keys()))
    return {
        "ok": True,
        "connected": fields.get("loggedIn") is True,
        "fields": fields,
        "otherFieldsPresent": other_present,  # names only, never values
        "stderr": stderr_summary,
    }


def main():
    version_exit, version_out, _version_err = run(["claude-agent-acp", "--cli", "--version"])
    version_result = classify_version(version_exit, version_out)
    print(json.dumps({"version": version_result}))

    auth_exit, auth_out, auth_err = run(["claude-agent-acp", "--cli", "auth", "status", "--json"])
    auth_result = classify_auth_status(auth_exit, auth_out, auth_err)
    print(json.dumps({"authStatus": auth_result}))

    print(json.dumps({
        "codex": "no login/doctor/auth subcommand exists in this image's codex-acp "
                 "binary (confirmed via --help in a prior lot) - not attempted here, "
                 "nothing to redact.",
    }))

    if version_result.get("status") == "command_failed":
        # The --version probe itself never ran successfully - this is a run
        # failure (code 2), never "garbled output" (code 5): the two must
        # stay distinguishable to a caller, not folded into one bucket.
        sys.exit(EXIT_COMMAND_FAILED)
    if version_result.get("status") != "ok":
        sys.exit(EXIT_UNEXPECTED_VERSION)
    if not auth_result.get("ok"):
        reason = auth_result.get("reason")
        if reason == "command_failed":
            sys.exit(EXIT_COMMAND_FAILED)
        if reason == "invalid_json":
            sys.exit(EXIT_INVALID_JSON)
        if reason == "unclassified_stderr":
            sys.exit(EXIT_UNCLASSIFIED_STDERR)
        sys.exit(1)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
