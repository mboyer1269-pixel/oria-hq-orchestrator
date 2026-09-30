# Canonical lifecycle observation

The trusted HQ lifecycle CLI accepts `{"next":"read"}`. It rereads the mission
and submission ledger and checks the same launch, workspace, actor, runner,
image and dossier bindings as transitions. Observation does not renew authority
or mutate the mission, and remains possible after authorization expires.

`hq_transition.lifecycle_reader(command)` supplies the callback expected by
`dispatch(..., read_claim=...)`. The command must use the same protected job
configuration as `lifecycle_transition(command)`. The Docker/PostgREST
qualification harness now wires both from the same command.

After the process stops, dispatch accepts completion only from the observed
`start_requested` or `running` state with the exact container identity. The
completion service still rereads and compares the canonical mission; a race or
uncertain response requires reconciliation, never a second agent execution.

Local validation: 11 HQ launch/lifecycle tests and 12 Python dispatch/bridge
tests pass. VPS qualification with `--valid-dossier` subsequently passed using
real Docker and PostgreSQL/PostgREST. The canonical read preceded completion;
the exact dossier and commit reached the runner, which exited 1 with
`Authentication required` after 8.717 seconds. The recorded execution state
survived PostgreSQL restart (six ledger rows). Temporary resources were cleaned
up; no public ports, production database, provider account or model call.
This run exercised completion from `start_requested`; completion from `running`
is covered locally, not yet with an authenticated provider session.
The active HQ image was not updated. It does not implement the pending permission transport,
owner review interface, provider authentication or a successful model mission.
