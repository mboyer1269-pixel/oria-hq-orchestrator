# Preparation-only dossier receiver

## Container mission entry point (not connected to HQ launch yet)

`run_mission.py` accepts a trusted host-supplied dossier, workspace identity,
checkout and separate results directory. It verifies the full dossier, exact
clean HEAD and SDK contract1.50.0 before constructing the Claude ACP agent.
An exclusive started.json blocks a second invocation using the same results
directory. SDK persistence is retained; outcome.json records the observed SDK
status and explicitly denies independent validation. No commit/push/deploy.

This local guard is not cross-container deduplication or authorization. The
host-side durable claim, controlled mounts, provider credentials, scoped tool
approval callback, external deadline and reconciliation remain required. The
candidate defaults to denying permission requests; it must not be advertised as
an autonomous coding executor until those controls and a real mission are proven.
Files written inside an agent container are evidence to inspect, not an independent
attestation. Provider token/cost ceilings are not guaranteed by this entry point.

VPS image qualified on2026-09-30:
`sha256:152df564b18fd7381e0bdfdd18ff57918eb9fa9a6e1d47a4820318e34c159da2`.
Resolved parent budget runtime:
`sha256:7ef7880436d4a7738e6c527ea16dad8c62e16efceb8c0b1fb34099c0c49becb8`.
`qualify_run_mission.py` uses the real SDK and BudgetPermissionAgent with the
synthetic metadata peer, networknone, UID10001, read-only root, cap-drop ALL,
bounded tmpfs/RAM/CPU. It confirms persisted conversation, returned finished
status classified as agent_returned (not mission success), and repeat refusal.
No model/credential/project-active access. The fixture peer emits no usage update;
the SDK warning is expected and no usage measurement is claimed.

Unit tests also reject a dirty checkout and tampered dossier before agent creation,
and preserve an execution error without retrying it. Real provider execution and
restart/resume after a host failure remain outstanding.

## Qualification PostgreSQL isolée

`qualify_postgres_cas.py` exécuté sur VPS contre PostgreSQL17.11 en conteneur
jetable, sans réseau externe/port publié/volume persistant, image locale fixée
par ID. Deux UPDATE concurrents sur les prédicats id/workspace/status/version/
JSONB donnent un gagnant; retry ancienneversion et workspaceétranger refusés.
Les données sont synthétiques et le conteneur est supprimé en finally.
Premier essai a atteint le serveur socket temporaire d'initialisation; readiness
TCP loopback corrige cette course puis qualification réussie code0.
Cela vérifie la sémantique SQL du CAS, pas le store TypeScript via PostgREST,
les politiques Supabase, les autorisations réelles ni une exécution exactly-once.

## Supervision opérateur distincte

`supervisor.supervise` est une primitive d'exécution distincte du récepteur de
préparation. Elle n'est reliée à aucune route HQ. L'appelant doit déjà détenir
l'autorisation et la réservation durable, puis fournir l'identifiant Docker
complet obtenu côté serveur. Un label n'est pas une autorisation.

Le superviseur accepte uniquement un conteneur neuf portant le label dédié,
borne l'attente de `docker start --attach`, puis vérifie l'état dans le daemon.
Au dépassement, Docker arrête le conteneur avec un délai de grâce borné. Le
conteneur, ses fichiers et ses journaux sont conservés; aucune suppression ni
relance automatique. Il faut réserver et sécuriser les montages lors de la
création, en amont. Le double lancement concurrent doit être empêché par la
réservation durable, pas par le contrôle d'état seul.

Les erreurs Docker remontent : un daemon inaccessible signifie résultat inconnu,
pas arrêt garanti. Le délai total inclut la grâce et les commandes de contrôle.
L'arrêt local ne démontre ni l'annulation côté fournisseur ni un plafond strict
de tokens/coût. Une panne du superviseur lui-même reste à traiter par un service
de réconciliation indépendant avant une mise en production.

Qualification VPS `qualify_supervisor.py` : travail réussi code0, échec code7
préservé, relance d'un conteneur terminé refusée; processus ignorant SIGTERM
arrêté code137 après deadline2s + grâce1s, durée observée3,134s. Aucun réseau,
credential, projet actif ou modèle. Trois conteneurs de preuve arrêtés conservés
avec les labels `oria.purpose=openhands-supervised-job` et
`oria.qualification=deadline`. Ceci qualifie le superviseur, pas une mission HQ.

`dossier.prepare(dossier, expected_workspace=..., expected_executor_version=...,
checkout=...)` validates the strict HQ contract and returns prepared/nonexecuting.
Workspace and executor expectations and checkout must be supplied by a trusted
server boundary, never taken from incoming request fields in production.

Git verification checks the explicit worktree root and existence of the exact
commit object via argument-vector subprocesses, five-second deadlines, replacement
objects disabled and inherited GIT_* overrides removed. No fetch or checkout.
It does NOT prove HEAD matches that commit, worktree cleanliness, approval,
repository provenance, or permission to execute. Those gates remain outstanding.

Hashing reconstructs fixed builder insertion order. Allowed values contain only
strings, bounded integers, booleans and fixed objects. Compact UTF-8 JSON preserves
Unicode (including emoji), and string lengths use UTF-16 units like JavaScript.
Unpaired surrogates are rejected. No general-purpose JavaScript JSON canonicalizer
is claimed. A real TypeScript builder Unicode fixture is in fixtures/hq-dossier.json.
Fixture integrity is an unkeyed checksum, not authentication or authorization.

Run `python -m unittest discover -s integrations/openhands-runner -v` from the
Orchestrator root. Tests create disposable Git repositories and no model calls.
The parent-generated original fixture was also accepted against its explicit
local fixture repository, proving this fixture's JS/Python hash compatibility.

## Isolated runtime checkout

`workspace.prepare_workspace(source=..., commit=..., server_root=..., job_name=...)`
creates a separate local clone with `--no-local --no-hardlinks --no-checkout`,
then checks out the exact detached commit and verifies clean Git status. Source
HEAD, tracked changes and untracked files are untouched. It never launches code,
fetches an external remote, initializes submodules, or invokes LFS smudge.
Hooks/templates and external Git config are disabled during preparation.

The destination root must already exist and be selected by the server. The job
name is one simple component, reserved by an atomic mkdir. Existing destinations
are refused. Failed preparations remain inspectable; no recursive cleanup runs.
The server must own the root exclusively to prevent symlink/race replacement.
This is a local clone rather than a chat-managed Git worktree.

Cost: a separate object database and checkout consume disk and local transfer
time; the current clone copies history, not just one commit. Clone/checkout each
have a 120-second timeout, other Git commands 30 seconds. Large repositories may
fail visibly and leave their partial destination. No retry is automatic.

This preparation assumes a trusted, operator-controlled source Git repository
and trusted Git binary. Source-local repository config is not a general hostile
repository sandbox. Committed files may contain symlinks, submodule entries,
LFS pointers, malicious code or instructions. They are not executed here; the
future executor must enforce filesystem/network isolation before using them.
Clean Git status is not a security attestation or permission to execute.

## Entrée opérateur de préparation
prepare_job.py lit un fichier JSON borné à128Kio, refuse champs JSON dupliqués et nombres non finis, vérifie le dossier, puis crée un clone isolé. Paramètres requis : --dossier, --workspace, --executor-version, --source, --jobs-root. Ces paramètres doivent provenir de configuration serveur fiable, pas du navigateur. Une destination déterministe déjà présente provoque un refus; ce n'est pas encore une réservation durable de lancement. Aucun modèle ni enforcement de budget. Le résultat indique explicitement durableLaunchReserved=false et budgetsEnforced=false.
# Memory-bearing dossier contract

The preparation receiver accepts unchanged v1 dossiers and v2 dossiers with an exact
Memex snapshot. Snapshot metadata and content participate in the approved payload
hash. Validation does not turn retrieved text into instructions or authorization.
No model is invoked. Project ownership is a server-side HQ responsibility; the runner
checks workspace binding and integrity, not the database project registry.

`export_hq_memory_fixture.mjs <HQ-root> <output-json>` generates a synthetic v2 fixture
using the actual HQ development-mission, Memex context and dossier builders. The
committed fixture contains only synthetic data, including Unicode for cross-language
hash/length checks. Regenerate it after intentional contract changes. Tests cover
tampering, missing memory, invalid metadata, legacy v1 and the isolated Git workflow.

# Host container creation boundary

`session_permissions.SessionPermissions` sequences instance-local ACP requests:
first obtain confirmed durable host registration for the actual ACP session ID,
then ask the decision callback. Unknown/cancelled registration is never retried;
another session cannot inherit registration. `execute(..., permission_callback=)`
can inject this trusted callback before conversation creation. The CLI still
supplies none and remains default-deny; no socket/service or credentials are
introduced by this seam. Async tests cover concurrent first calls, changed
session, unknown registration and cancellation. Actual callback-to-HQ transport,
authenticated UI and process-stop coordination are still pending.

`hq_transition.lifecycle_transition(host_argv)` translates supervisor results to
the strict HQ transition contract and invokes the local HQ script
`src/scripts/openhands-lifecycle.mjs <server-selected-job-config.json>` over stdin.
It requires a confirmed matching state/container response; unknown responses and
timeouts are never retried. The script uses the existing canonical Supabase store,
has no in-memory fallback, and accepts no browser authority or credentials in stdin.
The host config contains `{context:{workspaceId,actorId,runnerId},missionId,launchId,config}`.
Protect the config and parent directories from agent writes. The future worker
must derive its image, workspace and deadline from this SAME canonical config;
do not independently accept execution options from a mission payload.
Use a host-selected invocation inside the HQ service context to keep database
credentials outside the agent container. This bridge has not yet been exercised
against real persistence or installed as a live worker.

`dispatch.py` orders creation and supervision through a required durable CAS
callback: claimed → creation_requested → container_created → start_requested
→ execution_finished. It never treats process exit as independent validation.
Uncertain creation/persistence requires reconciliation, with no automatic retry.
Four tests cover replay and uncertain writes/creation. The callback is not yet
wired to HQ: its launch schema/store must support the additional states and
container identity, bind every CAS to canonical authorization/config/runner,
and enforce authorization expiry before creation and start. Do not expose this
helper directly as an HTTP endpoint or use the test's in-memory store in service.

`container_job.create_job` creates (never starts) a deterministic container from
an operator-selected pinned image and a prepared job directory containing
`checkout/`, `results/`, and `dossier.json`. The caller must already hold the
durable HQ launch claim and record the returned container ID before supervision.
An ambiguous Docker response requires inspection by name; never automatically
create another job. This helper does not implement that durable bridge yet.

The current qualification profile has no network or credentials. It therefore
cannot execute a real Claude mission. Provider access still requires an explicit
host-controlled profile, account authorization, and scoped tool permissions.
Provision writable paths for UID 10001 before creation. Host path ownership and
protection against concurrent mount replacement remain caller responsibilities.
Three unit tests cover command construction, image pinning, and ambiguous
results. `qualify_container_job.py --image <pinned-ID>` passed on the VPS using
image `sha256:152df564b18fd7381e0bdfdd18ff57918eb9fa9a6e1d47a4820318e34c159da2`:
actual creation, network none, read-only root and dossier, bounded CPU/RAM,
three expected mounts, and supervised rejection of an invalid dossier before
agent creation. Observed exit 1 after 0.384 seconds; this is a rejection-path
measurement, not mission performance. The disposable container was removed by
the qualifier after supervision. No credentials, network or model call used.
The first assertion expected the wrong exception name; actual logs showed
`dossier.InvalidDossier`, and the corrected specific assertion passed.
