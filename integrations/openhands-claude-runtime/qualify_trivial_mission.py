"""REJECTED as a delivery path - kept only as a documented dead end, never
executed, never developed further. See
docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md's "Revue du script trivial en
cours": raw ACP stdio (this file) bypasses BudgetPermissionAgent entirely -
it cannot impose maxCostCents/maxTokens no matter what this file's own
budget-shape validation claims to check (confirmed: this candidate's
bundled claude-agent-acp exposes no maxTurns/maxBudgetUsd/meta passthrough
at the raw ACP layer - see the module docstring below, unchanged). That
makes it structurally unable to serve as proof of a budget-respecting
mission, even though it enforces timeoutSeconds and a single iteration for
real.

The real, already-built, already-designed path is
integrations/openhands-runner/run_mission.py's execute() (invoked via
qualify_run_mission.py for local, isolated, no-model qualification, or via
dispatch.py/prepare_host_job.py for the real durable launch contract) -
it constructs a REAL openhands.sdk.Conversation with a REAL
BudgetPermissionAgent, which DOES forward maxTurns/maxBudgetUsd into the
real Claude Code CLI session through the SDK's own ACPSessionMeta
mechanism (see integrations/openhands-permission-extension/budget_agent.py)
- something raw ACP stdio cannot reach at all. Do not build a second raw-
ACP path to work around this; reuse that existing contract instead. This
file is left in place, non-executable by default (its env-var gates are
unset), purely so the dead end and the reason for it stay documented
rather than silently disappearing.

--- Original docstring, unchanged, describing what this script DOES do
--- (never claims proof of budget enforcement beyond what is listed below):

Ready, gated recipe for a real trivial mission (create a text file, verify
its content) via claude-agent-acp's REAL ACP protocol - never the diagnostic
override used by qualify_connection_account.py.

Reuses, never duplicates:
  - The reviewed initialize/session/new handshake pattern already qualified
    in qualify_initialize.py (same subprocess, same stdio JSON-RPC shape).
  - provider_policy.validate_authorization (../openhands-runner) for the
    authorization object - never a second, ad hoc authorization check.

This script sends EXACTLY ONE real session/prompt - a genuine model
invocation under the existing authorized subscription, never a billed
separate API, never a second call, never a loop. It will only reach that
point if BOTH of the following are real, explicit, operator-provided
artifacts - neither is defaulted, guessed, or fabricated by this script:

  ORIA_TRIVIAL_MISSION_AUTHORIZATION_FILE
      Path to a JSON file shaped exactly like provider_policy.py's
      AUTHORIZATION dict: profileId, policySha256, policyRoot, gatewayRoot.
      Validated with the SAME validate_authorization() the real runner uses
      - never a second, looser check invented for this script alone.

  ORIA_TRIVIAL_MISSION_BUDGET_FILE
      Path to a JSON file with exactly four required fields: maxCostCents,
      maxTokens, maxIterations, timeoutSeconds (all positive integers).
      maxIterations must be exactly 1 - this script only ever sends one
      prompt, by construction, and refuses to proceed if the budget claims
      more than that is allowed (it would be an unused allowance, not a
      real bound this script enforces).

Honesty about what is and is not actually enforced, not just declared:
  - timeoutSeconds IS enforced for real (asyncio.wait_for on the prompt
    step).
  - maxIterations IS enforced for real, structurally: exactly one
    session/prompt call exists in this file's code, never a loop.
  - maxCostCents and maxTokens are validated for SHAPE only. Searched this
    candidate's own bundled claude-agent-acp source
    (@agentclientprotocol/claude-agent-acp/dist/index.js) for a
    maxTurns/maxBudgetUsd/meta passthrough matching
    integrations/openhands-permission-extension/budget_agent.py's
    ACPSessionMeta mechanism: absent. That mechanism is OpenHands-SDK-level
    (ACPAgent.build_acp_session_meta), reached only through a real SDK
    agent session, not through raw ACP stdio as this script (and
    qualify_initialize.py) speaks it. So maxCostCents/maxTokens are
    recorded as the operator's declared bound, NOT technically enforced by
    this script's own transport. Real enforcement of those two fields
    requires going through integrations/openhands-permission-extension's
    BudgetPermissionAgent end-to-end, which requires a qualified OpenHands
    runner host - not deployed today.

Never assumes an unknown cost is zero. A genuinely connected, authorized
run below is a REAL model call consuming the existing Claude subscription's
usage - never a separate billed API, but never free either.

Exit codes:
  0  = mission executed, file created and verified, exactly as specified.
  10 = ORIA_TRIVIAL_MISSION_AUTHORIZATION_FILE missing, unreadable, invalid
       JSON, or failing provider_policy.validate_authorization.
  11 = ORIA_TRIVIAL_MISSION_BUDGET_FILE missing, unreadable, invalid JSON,
       or failing this script's own budget shape check (incl. maxIterations
       != 1).
  12 = the real ACP handshake (initialize/session/new) failed - same
       failure classes as qualify_initialize.py.
  13 = the model's turn ended but the file was not created with the exact
       expected content - the model did not do what was asked, or did
       something else; never silently accepted as success.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openhands-runner"))
from provider_policy import validate_authorization  # noqa: E402

AUTH_FILE_ENV = "ORIA_TRIVIAL_MISSION_AUTHORIZATION_FILE"
BUDGET_FILE_ENV = "ORIA_TRIVIAL_MISSION_BUDGET_FILE"
BUDGET_FIELDS = {"maxCostCents", "maxTokens", "maxIterations", "timeoutSeconds"}

EXIT_OK = 0
EXIT_AUTHORIZATION_INVALID = 10
EXIT_BUDGET_INVALID = 11
EXIT_HANDSHAKE_FAILED = 12
EXIT_MISSION_NOT_VERIFIED = 13

EXPECTED_FILENAME = "oria-hq-trivial-mission.txt"
EXPECTED_CONTENT = "ORIA-HQ-TRIVIAL-MISSION-OK"


def load_json_file(env_var):
    path = os.environ.get(env_var)
    if not path:
        return None, f"{env_var} is not set"
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        return None, f"{env_var} ({path}) unreadable: {type(error).__name__}"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, f"{env_var} ({path}) is not valid JSON"


def load_authorization():
    data, error = load_json_file(AUTH_FILE_ENV)
    if error:
        return None, error
    try:
        return validate_authorization(data), None
    except (ValueError, TypeError):
        return None, f"{AUTH_FILE_ENV} failed provider_policy.validate_authorization"


def load_budget():
    data, error = load_json_file(BUDGET_FILE_ENV)
    if error:
        return None, error
    if not isinstance(data, dict) or set(data) != BUDGET_FIELDS:
        return None, f"{BUDGET_FILE_ENV} must have exactly {sorted(BUDGET_FIELDS)}"
    for field in BUDGET_FIELDS:
        value = data[field]
        if type(value) is not int or isinstance(value, bool) or value <= 0:
            return None, f"{BUDGET_FILE_ENV}.{field} must be a positive integer"
    if data["maxIterations"] != 1:
        return None, (
            f"{BUDGET_FILE_ENV}.maxIterations is {data['maxIterations']}, "
            "but this script structurally sends exactly one session/prompt - "
            "an allowance beyond 1 would be unenforced by this script, refusing"
        )
    return data, None


async def run_mission(budget, workdir):
    process = await asyncio.create_subprocess_exec(
        "claude-agent-acp", stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    try:
        async def send(message):
            process.stdin.write((json.dumps(message) + "\n").encode())
            await process.stdin.drain()

        async def receive(expected_id, timeout):
            async def _read():
                for _ in range(40):
                    line = await process.stdout.readline()
                    if not line:
                        raise RuntimeError("Adapter closed before expected response")
                    response = json.loads(line)
                    if response.get("id") == expected_id:
                        return response
                raise RuntimeError("Expected response not received")
            return await asyncio.wait_for(_read(), timeout=timeout)

        await send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": 1, "clientCapabilities": {},
            "clientInfo": {"name": "hq-trivial-mission", "version": "1.0.0"}}})
        init_response = await receive(1, timeout=15)
        if "error" in init_response:
            raise RuntimeError("Initialize rejected")

        await send({"jsonrpc": "2.0", "id": 2, "method": "session/new",
                    "params": {"cwd": str(workdir), "mcpServers": []}})
        session_response = await receive(2, timeout=10)
        if "error" in session_response:
            raise RuntimeError("Session creation rejected")
        session_id = session_response["result"].get("sessionId")
        if not isinstance(session_id, str) or not session_id.strip():
            raise RuntimeError("Missing session identity")

        prompt_text = (
            f"Create a file named exactly '{EXPECTED_FILENAME}' in the current "
            f"working directory, containing exactly this text with no extra "
            f"whitespace or trailing newline: {EXPECTED_CONTENT}"
        )
        await send({"jsonrpc": "2.0", "id": 3, "method": "session/prompt", "params": {
            "sessionId": session_id,
            "prompt": [{"type": "text", "text": prompt_text}],
        }})
        prompt_response = await receive(3, timeout=budget["timeoutSeconds"])
        if "error" in prompt_response:
            raise RuntimeError("Prompt rejected")
        return prompt_response["result"]
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except TimeoutError:
                process.kill()
                await process.wait()


def verify_mission(workdir):
    target = workdir / EXPECTED_FILENAME
    if not target.is_file():
        return False, "expected file was not created"
    actual = target.read_text(encoding="utf-8")
    if actual != EXPECTED_CONTENT:
        return False, f"file content did not match exactly (length {len(actual)})"
    return True, "file created with exact expected content"


def main():
    authorization, auth_error = load_authorization()
    if auth_error:
        print(json.dumps({"ok": False, "blocker": auth_error}))
        sys.exit(EXIT_AUTHORIZATION_INVALID)

    budget, budget_error = load_budget()
    if budget_error:
        print(json.dumps({"ok": False, "blocker": budget_error}))
        sys.exit(EXIT_BUDGET_INVALID)

    with tempfile.TemporaryDirectory(prefix="oria-hq-trivial-mission-") as work:
        workdir = Path(work)
        try:
            result = asyncio.run(run_mission(budget, workdir))
        except (RuntimeError, asyncio.TimeoutError, OSError) as error:
            print(json.dumps({"ok": False, "blocker": f"handshake_failed: {error}"}))
            sys.exit(EXIT_HANDSHAKE_FAILED)

        verified, detail = verify_mission(workdir)
        print(json.dumps({
            "ok": verified,
            "stopReason": result.get("stopReason"),
            "verification": detail,
            "authorizationProfileId": authorization["profileId"],
            "budgetDeclared": budget,
        }))
        sys.exit(EXIT_OK if verified else EXIT_MISSION_NOT_VERIFIED)


if __name__ == "__main__":
    main()
