"""Offline consistency check for a bridge admission report.

The verdict never authenticates that a command ran, and it is never
ready_for_production. Exit 0 is intentionally unused.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1
VERDICTS = ("incomplete", "refused", "reviewable")
EXIT_CODES = {"incomplete": 2, "refused": 3, "reviewable": 4}
REQUIRED_SCENARIOS = (
    "same_request_concurrent",
    "divergent_payload",
    "lost_response_after_commit",
    "restart",
    "protected_identity",
    "admission_authorization_execution",
)
STATUSES = {"simulated", "real", "not_run", "failed"}
BACKENDS = {"postgresql", "map", "mock", "http-in-process", "unspecified"}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNIQUENESS_RE = re.compile(r"\b(UNIQUE|PRIMARY KEY|EXCLUDE)\b", re.IGNORECASE)
MAP_RE = re.compile(r"\bMap\b")
LOOKUP_PROCEDURES = {"lookup", "lookup_before_create"}
LOST_RESPONSE_PROCEDURE = "commit_then_drop_response_then_replay"
LIMITS = (
    "Ce contrôle ne prouve pas qu'une commande a été exécutée.",
    "Un JSON cohérent n'authentifie pas le pont et n'est pas une preuve cryptographique.",
    "Le verdict reviewable signifie seulement qu'un humain peut lire le paquet.",
    "ready_for_production n'est pas un verdict de cet outil.",
)


def reason(code, message):
    return {"code": code, "message": message}


def is_int(value):
    return type(value) is int


def unique_reasons(reasons):
    unique = []
    for item in reasons:
        if item not in unique:
            unique.append(item)
    return unique


def verdict_document(verdict, reasons):
    if verdict not in VERDICTS:
        raise RuntimeError("verdict hors contrat")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "verdict": verdict,
        "readyForProduction": False,
        "authenticatesExecution": False,
        "reasons": unique_reasons(reasons),
        "limits": list(LIMITS),
    }


def load_report(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, reason("schema_invalid", f"JSON illisible : {error}")
    if type(data) is not dict:
        return None, reason("schema_invalid", "Le rapport doit être un objet JSON.")
    return data, None


def validate_report(report):
    if type(report) is not dict:
        return verdict_document("incomplete", [reason("schema_invalid", "Le rapport doit être un objet JSON.")])
    if report.get("schemaVersion") != SCHEMA_VERSION:
        return verdict_document("incomplete", [reason("schema_invalid", "schemaVersion doit valoir 1.")])

    refused = []
    incomplete = []
    if report.get("readyForProduction") is True:
        refused.append(reason("self_certified_production", "Le rapport se déclare prêt pour la production."))
    if report.get("authenticatesExecution") is True:
        refused.append(reason("self_certified_authentication", "Le rapport prétend authentifier l'exécution."))
    if report.get("verdict") == "ready_for_production":
        refused.append(reason("self_certified_production", "Le rapport annonce le verdict ready_for_production."))

    commit = report.get("testedCommit")
    if not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
        incomplete.append(reason("schema_invalid", "testedCommit doit être quarante hexadécimaux minuscules."))
        commit = None
    if type(report.get("limits")) is not list or not report.get("limits") or any(type(item) is not str or not item for item in report.get("limits", [])):
        incomplete.append(reason("missing_limits", "Les limites du rapport sont absentes."))
    fixture_class = report.get("fixtureClass")
    if fixture_class not in {"synthetic", "collected"}:
        incomplete.append(reason("schema_invalid", "fixtureClass doit valoir synthetic ou collected."))

    database = report.get("database")
    scenarios = report.get("scenarios")
    if type(scenarios) is not list:
        incomplete.append(reason("schema_invalid", "scenarios doit être une liste."))
        scenarios = []
    by_id = {}
    for scenario in scenarios:
        if type(scenario) is not dict or not isinstance(scenario.get("id"), str):
            incomplete.append(reason("schema_invalid", "Chaque scénario doit avoir un id."))
            continue
        if scenario["id"] in by_id:
            incomplete.append(reason("schema_invalid", f"Scénario dupliqué : {scenario['id']}."))
        by_id[scenario["id"]] = scenario

    claims_real = any(item.get("status") == "real" for item in by_id.values())
    if claims_real:
        refused.extend(database_refusals(database))
        if fixture_class == "synthetic":
            refused.append(reason("synthetic_labeled_real", "Une fixture synthétique ne peut pas être marquée real."))

    for scenario_id in REQUIRED_SCENARIOS:
        scenario = by_id.get(scenario_id)
        if scenario is None:
            incomplete.append(reason("missing_scenario", f"Scénario absent : {scenario_id}."))
            continue
        status = scenario.get("status")
        if status not in STATUSES:
            incomplete.append(reason("schema_invalid", f"Statut illisible pour {scenario_id}."))
            continue
        if commit is not None and scenario.get("testedCommit") not in {None, commit}:
            refused.append(reason("mixed_commits", f"{scenario_id} cite un autre commit que le rapport."))
        if status == "not_run":
            incomplete.append(reason("scenario_not_run", f"{scenario_id} n'a pas été exécuté."))
        elif status == "failed":
            incomplete.append(reason("scenario_failed", f"{scenario_id} est en échec observé."))
        elif status == "simulated":
            incomplete.append(reason("scenario_simulated", f"{scenario_id} est une simulation identifiée."))
        elif status == "real":
            refused.extend(real_scenario_refusals(scenario_id, scenario, commit))

    if refused:
        return verdict_document("refused", refused + incomplete)
    if incomplete or not claims_real:
        return verdict_document("incomplete", incomplete or [reason("scenario_not_run", "Aucun scénario real cohérent.")])
    return verdict_document("reviewable", [])


def database_refusals(database):
    if type(database) is not dict:
        return [reason("missing_database_identity", "La section database est absente.")]
    reasons = []
    backend = database.get("backendKind")
    if backend not in BACKENDS:
        reasons.append(reason("schema_invalid", "backendKind est illisible."))
    if backend in {"map", "mock", "http-in-process", "unspecified"}:
        reasons.append(reason("backend_map_or_mock", "Le backend déclaré n'est pas PostgreSQL."))
    if database.get("engine") != "postgresql" or database.get("implementation") != "postgresql+postgrest":
        reasons.append(reason("backend_not_postgresql", "engine ou implementation n'est pas postgresql+postgrest."))
    blob = " ".join(str(database.get(key, "")) for key in ("backendKind", "engine", "implementation", "selectVersion", "notes"))
    if "createserver" in blob.lower() or MAP_RE.search(blob):
        reasons.append(reason("backend_map_or_mock", "Le rapport décrit Map ou createServer."))
    select_version = database.get("selectVersion")
    if not isinstance(select_version, str) or "PostgreSQL" not in select_version:
        reasons.append(reason("missing_database_identity", "SELECT version() observé est absent."))
    if not isinstance(database.get("postgrestVersion"), str) or not database.get("postgrestVersion"):
        reasons.append(reason("missing_database_identity", "La version PostgREST observée est absente."))
    digests = database.get("imageDigests")
    if type(digests) is not list or not digests or any(not isinstance(item, str) or DIGEST_RE.fullmatch(item) is None for item in digests):
        reasons.append(reason("missing_image_digest", "Aucun digest sha256 observé."))
    migrations = database.get("migrationsApplied")
    if type(migrations) is not list or not migrations or any(not isinstance(item, str) or not item.endswith(".sql") for item in migrations):
        reasons.append(reason("missing_migrations", "Les migrations appliquées ne sont pas nommées."))
    if type(database.get("migrationHistoryComplete")) is not bool:
        reasons.append(reason("missing_migrations", "migrationHistoryComplete doit être un booléen."))
    constraint = database.get("sqlConstraint")
    if type(constraint) is not dict:
        reasons.append(reason("constraint_not_observed", "La contrainte SQL observée est absente."))
    else:
        definition = constraint.get("definition")
        if not isinstance(constraint.get("name"), str) or not constraint.get("name") or not isinstance(definition, str) or not definition:
            reasons.append(reason("constraint_not_observed", "Le nom ou la définition de contrainte est vide."))
        elif constraint.get("catalogSource") != "pg_constraint":
            reasons.append(reason("constraint_not_observed", "La contrainte n'a pas été lue dans pg_constraint."))
        elif UNIQUENESS_RE.search(definition) is None or "lookup" in definition.lower():
            reasons.append(reason("constraint_not_unique", "La définition observée n'est pas une unicité SQL."))
    return reasons


def real_scenario_refusals(scenario_id, scenario, commit):
    reasons = []
    if scenario.get("testedCommit") != commit:
        reasons.append(reason("mixed_commits", f"{scenario_id} n'a pas le commit du rapport."))
    if type(scenario.get("limits")) is not list or not scenario.get("limits"):
        reasons.append(reason("missing_limits", f"{scenario_id} n'a pas de limites."))
    outputs = scenario.get("outputs")
    if type(outputs) is not list or not outputs:
        reasons.append(reason("missing_outputs", f"{scenario_id} n'a pas de sorties."))
        outputs = []
    for output in outputs:
        if type(output) is not dict or not isinstance(output.get("command"), str) or not output.get("command") or not is_int(output.get("exitCode")):
            reasons.append(reason("missing_outputs", f"Sortie incomplète pour {scenario_id}."))
            continue
        if output.get("testedCommit") != commit:
            reasons.append(reason("mixed_commits", f"Une sortie de {scenario_id} cite un autre commit."))
    assertions = assertion_ids(scenario.get("assertions"))
    if scenario_id == "same_request_concurrent":
        reasons.extend(expect_ids(scenario_id, assertions, {"single_row", "both_callers_same_row"}))
        if scenario.get("rowCount") != 1 or scenario.get("secondExecutionStarted") is not False:
            reasons.append(reason("second_execution", "La concurrence real ne montre pas une seule ligne sans seconde exécution."))
    elif scenario_id == "divergent_payload":
        reasons.extend(expect_ids(scenario_id, assertions, {"payload_conflict_refused", "stored_payload_unchanged"}))
        if scenario.get("secondPayloadStored") is not False:
            reasons.append(reason("payload_overwritten", "Le payload divergent real ne prouve pas le refus."))
    elif scenario_id == "lost_response_after_commit":
        reasons.extend(lost_response_refusals(scenario, assertions, outputs))
    elif scenario_id == "restart":
        reasons.extend(restart_refusals(scenario, outputs))
    elif scenario_id == "protected_identity":
        reasons.extend(expect_ids(scenario_id, assertions, {"workspace_from_protected_context", "foreign_workspace_denied"}))
        if scenario.get("bodyWorkspaceUsed") is not False:
            reasons.append(reason("protected_context_not_used", "L'espace real vient encore du corps de la requête."))
    elif scenario_id == "admission_authorization_execution":
        reasons.extend(admission_refusals(scenario, assertions))
    return reasons


def assertion_ids(assertions):
    if type(assertions) is not list:
        return set()
    return {item.get("id") for item in assertions if type(item) is dict and isinstance(item.get("id"), str)}


def expect_ids(scenario_id, present, required):
    missing = required - present
    if not missing:
        return []
    names = ", ".join(sorted(missing))
    return [reason("missing_assertion", f"{scenario_id} n'a pas les assertions {names}.")]


def lost_response_refusals(scenario, assertions, outputs):
    reasons = []
    procedure = scenario.get("procedure")
    phases = {item.get("phase") for item in outputs if type(item) is dict}
    lookup_labeled = procedure in LOOKUP_PROCEDURES or "lookup_before_create" in assertions or phases == {"lookup"} or (phases and phases <= {"lookup"})
    if lookup_labeled or procedure != LOST_RESPONSE_PROCEDURE:
        reasons.append(reason("simple_lookup_labeled_lost_response", "lost_response real est un lookup, pas une perte après commit."))
    missing = {"committed_before_loss", "response_dropped_after_commit", "replay_creates_nothing"} - assertions
    if missing or not {"commit", "drop_response", "replay"} <= phases:
        reasons.append(reason("simple_lookup_labeled_lost_response", "Les phases commit, perte de réponse et reprise sont incomplètes."))
    return reasons


def restart_refusals(scenario, outputs):
    reasons = []
    counts = {}
    assertions = scenario.get("assertions")
    if type(assertions) is not list:
        assertions = []
    for assertion_id in ("sql_count_before_restart", "sql_count_after_restart"):
        matches = [item for item in assertions if type(item) is dict and item.get("id") == assertion_id and is_int(item.get("rowCount"))]
        if len(matches) != 1:
            reasons.append(reason("restart_count_assertion_missing", f"Assertion {assertion_id} absente."))
        else:
            counts[assertion_id] = matches[0]["rowCount"]
    phases = {item.get("phase") for item in outputs if type(item) is dict}
    if not {"count_before_restart", "restart_database", "count_after_restart"} <= phases:
        reasons.append(reason("restart_count_assertion_missing", "Les sorties avant et après redémarrage sont absentes."))
    if len(counts) == 2 and counts["sql_count_before_restart"] != counts["sql_count_after_restart"]:
        reasons.append(reason("restart_counts_disagree", "Les comptes SQL avant et après redémarrage diffèrent."))
    return reasons


def admission_refusals(scenario, assertions):
    reasons = []
    counts = scenario.get("stateCounts")
    keys = {"admitted", "authorized", "executed"}
    if type(counts) is not dict or set(counts) < keys or any(not is_int(counts.get(key)) for key in keys):
        reasons.append(reason("admission_confused_with_execution", "Les trois comptes admission, autorisation et exécution sont absents."))
    if scenario.get("admissionMeansExecution") is not False or "admission_is_execution" in assertions or "states_observed_separately" not in assertions:
        reasons.append(reason("admission_confused_with_execution", "L'admission real est confondue avec l'exécution."))
    return reasons


def main(argv):
    parser = argparse.ArgumentParser(description="Valide la cohérence d'un rapport d'admission. Ne prouve pas l'exécution.")
    parser.add_argument("report", help="Chemin du JSON collecté ou de la fixture")
    args = parser.parse_args(argv)
    report, error = load_report(args.report)
    document = verdict_document("incomplete", [error]) if error else validate_report(report)
    json.dump(document, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_CODES[document["verdict"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
