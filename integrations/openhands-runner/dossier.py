"""Preparation-only receiver. No network, checkout, inference or execution."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import os
from datetime import datetime
from uuid import UUID


class InvalidDossier(ValueError):
    pass


def exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise InvalidDossier("Unexpected contract fields")


def text(value, maximum):
    if not isinstance(value, str) or not value.strip():
        raise InvalidDossier("Expected nonempty string")
    try:
        length = len(value.encode("utf-16-le")) // 2
    except UnicodeEncodeError as error:
        raise InvalidDossier("Unpaired Unicode surrogate unsupported") from error
    if length > maximum:
        raise InvalidDossier("String exceeds UTF-16 length limit")


def digest(value):
    # Fixed key insertion order, valid Unicode, booleans and bounded integers.
    # No floats/nonfinite values or JavaScript property-order numeric keys exist.
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def prepare(dossier, *, expected_workspace, expected_executor_version, checkout):
    if type(dossier) is not dict:
        raise InvalidDossier("Expected dossier object")
    contract_version = dossier.get("contractVersion")
    memory_fields = ("memory",) if type(contract_version) is int and contract_version == 2 else ()
    exact(dossier, ("contractVersion", "executor", "executorVersion", "mission", "source", "budget",
                    "approvalRequired", "executionRequested", "idempotencyKey", "payloadHash") + memory_fields)
    if type(contract_version) is not int or contract_version not in (1, 2):
        raise InvalidDossier("Unsupported contract version")
    if dossier["executor"] != "openhands" or dossier["executorVersion"] != expected_executor_version:
        raise InvalidDossier("Executor mismatch")
    version = dossier["executorVersion"]
    if not isinstance(version, str) or len(version) > 64 or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", version, re.ASCII):
        raise InvalidDossier("Invalid executor version")
    if dossier["executionRequested"] is not False or dossier["approvalRequired"] is not True:
        raise InvalidDossier("Preparation requires unapproved, non-executing mission")
    mission_keys = ("id", "workspaceId", "modeId", "version", "title", "objective", "scope",
                    "acceptanceCriteria", "expectedOutput", "createdBy")
    mission = dossier["mission"]
    exact(mission, mission_keys)
    for key, limit in (("workspaceId",160),("modeId",160),("createdBy",160),("title",200),
                       ("objective",4000),("scope",1000),("acceptanceCriteria",2000),("expectedOutput",4000)):
        text(mission[key], limit)
    if mission["workspaceId"] != expected_workspace:
        raise InvalidDossier("Workspace mismatch")
    try:
        if str(UUID(mission["id"])) != mission["id"].lower():
            raise ValueError()
        if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", mission["version"], re.ASCII):
            raise ValueError()
        datetime.fromisoformat(mission["version"].replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as error:
        raise InvalidDossier("Invalid mission identity/version") from error
    exact(dossier["source"], ("commitSha", "commitVerification"))
    commit = dossier["source"]["commitSha"]
    if not isinstance(commit, str) or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})",commit) or set(commit)=={"0"}:
        raise InvalidDossier("Invalid commit")
    if dossier["source"]["commitVerification"] != "not_verified":
        raise InvalidDossier("Sender cannot attest commit verification")
    limits = {"maxCostCents":10000,"maxTokens":200000,"maxIterations":100,"timeoutSeconds":1800}
    exact(dossier["budget"], limits)
    for key, maximum in limits.items():
        value = dossier["budget"][key]
        if type(value) is not int or not 1 <= value <= maximum:
            raise InvalidDossier("Invalid budget")
    payload = {"contractVersion":contract_version,"executor":"openhands","executorVersion":version,
               "mission":{key:mission[key] for key in mission_keys},
               "source":{"commitSha":commit,"commitVerification":"not_verified"},
               "budget":{key:dossier["budget"][key] for key in limits},
               "approvalRequired":True,"executionRequested":False}
    if contract_version == 2:
        payload["memory"] = validate_memory(dossier["memory"], expected_workspace)
    expected_key = "hq-openhands-v1-" + digest([expected_workspace,mission["id"],mission["version"]])
    if dossier["idempotencyKey"] != expected_key or dossier["payloadHash"] != digest(payload):
        raise InvalidDossier("Integrity mismatch")
    directory = Path(checkout).resolve(strict=True)
    # Explicit local repository only: do not search parent repositories or allow
    # a bare object store to masquerade as the intended worktree.
    command = ["git", "--no-replace-objects", "-C", str(directory)]
    environment = {key:value for key,value in os.environ.items() if not key.upper().startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    top = subprocess.run(command+["rev-parse","--show-toplevel"], capture_output=True, text=True, timeout=5, check=True, env=environment)
    if Path(top.stdout.strip()).resolve() != directory:
        raise InvalidDossier("Checkout root mismatch")
    result = subprocess.run(command+["cat-file","-t",commit], capture_output=True,text=True,timeout=5,env=environment)
    if result.returncode or result.stdout.strip() != "commit":
        raise InvalidDossier("Commit unavailable in checkout")
    return {"status":"prepared","executionRequested":False,"approvalSatisfied":False,
            "commitVerification":"verified_local_object","commitSha":commit,
            "idempotencyKey":expected_key,"payloadHash":dossier["payloadHash"]}


def validate_memory(memory, expected_workspace):
    """Bounded data/integrity check, not project authorization or trusted instructions."""
    keys = ("contractVersion", "sourceTool", "workspaceId", "projectId", "namespace", "centerEntityId",
            "retrievedAtIso", "content", "contentChars", "redactionsApplied", "snapshotHash")
    exact(memory, keys)
    if type(memory["contractVersion"]) is not int or memory["contractVersion"] != 1:
        raise InvalidDossier("Unsupported memory version")
    if memory["sourceTool"] != "agentmemory_context_pack" or memory["workspaceId"] != expected_workspace:
        raise InvalidDossier("Memory source/workspace mismatch")
    for key in ("workspaceId", "projectId", "centerEntityId"):
        text(memory[key], 160)
    text(memory["namespace"], 256)
    if not memory["namespace"].startswith("org:"):
        raise InvalidDossier("Invalid memory namespace")
    text(memory["content"], 4000)
    if type(memory["contentChars"]) is not int or memory["contentChars"] != len(memory["content"].encode("utf-16-le")) // 2:
        raise InvalidDossier("Memory length mismatch")
    if type(memory["redactionsApplied"]) is not int or not 0 <= memory["redactionsApplied"] <= 9007199254740991:
        raise InvalidDossier("Invalid memory redaction count")
    try:
        stamp = memory["retrievedAtIso"]
        if not isinstance(stamp, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", stamp, re.ASCII):
            raise ValueError()
        datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        content = json.loads(memory["content"])
        exact(content, ("centerEntity", "entities", "relations", "provenance"))
        if type(content["centerEntity"]) is not dict or content["centerEntity"].get("id") != memory["centerEntityId"]:
            raise ValueError()
    except (ValueError, TypeError) as error:
        raise InvalidDossier("Invalid memory content/timestamp") from error
    hash_keys = ("contractVersion", "sourceTool", "workspaceId", "projectId", "namespace", "centerEntityId",
                 "retrievedAtIso", "content", "redactionsApplied")
    if memory["snapshotHash"] != digest({key: memory[key] for key in hash_keys}):
        raise InvalidDossier("Memory integrity mismatch")
    return {key: memory[key] for key in keys}
