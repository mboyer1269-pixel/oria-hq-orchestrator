# Mission-container provider relay integration

Implemented and qualified 2026-09-30. Not activated in the installed consumer or HQ deployment; explicit provider profiles still fail closed there. This adds a tested execution mechanism, not account authorization.

`create_job` accepts an optional host-provided gateway, checks its runtime image, exact launch-owned paths, relay hash and socket permissions, then inspects the live proxy's image and launch/purpose labels. It keeps agent networking at `none` and mounts only the socket directory and verified relay file read-only. It adds the fixed `--provider-relay` entry-point flag. No provider executable, environment or arbitrary Docker option is taken from the mission dossier.

The runtime guardian in `provider_relay.py` starts the fixed Node relay, requires its readiness message within five seconds, then starts the ordinary mission entry point as a child. It sets HTTP/HTTPS proxies to loopback, clears proxy bypasses, and sets `ENABLE_CLAUDEAI_MCP_SERVERS=false`. The worker runs in its own process group. Relay exit returns70 and triggers worker cleanup; worker exit propagates its code. Cleanup of one process cannot skip cleanup of the other. The external host deadline remains mandatory. Proxy-container expiry remains independently enforced.

## Real qualification and exact limits

The regular candidate image is `sha256:fce8f3aacbadcb87f63556d87199ca81725ab52e89791b091c11cb63b3235159`. Its parent was resolved and verified as the existing `3d8c97...` image before build. Docker build did not accept a bare `sha256:` image ID as FROM; a verified local tag was used with pull disabled. Execution uses recorded image IDs.

A separately labelled synthetic-ACP image, `sha256:ecfafc87bc148d922dd4d43c3c5d3bb80f4a0828e4ff9af22ef80b7bd5c2924d`, derives from that candidate and replaces only the Claude adapter with the explicit test peer. It is never presented as authenticated Claude. `../openhands-provider-proxy/qualify_mission_relay.py` prepares a synthetic v2 memory dossier and clean fixture Git commit, derives a test-only policy binding this image, calls the actual host gateway and container factory, and runs the actual supervisor/mission entry point/OpenHands SDK.

`mission-relay-evidence.json` records: normal process exit, persistent start/outcome/conversation, `agent_returned` with independentValidationPassed=false, proxy environment and connector-disable flag observed by the peer, real certificate-verified TLS through the relay, foreign-domain403, and gateway cleanup. Three changed bindings (runtime image, relay hash, launch identity) are refused. No credentials or model requests occur. Fixture memory is not a real published project snapshot. The test performs no coding, independent code review, production deployment, actual Claude connector inventory or account refresh.

Validation: five relay tests passed on Linux, including an actual short-lived relay process whose exit causes a long-running worker process to be terminated. Full host suite: 87 passed,19 Windows-platform skips. The real container qualification also passed. No HQ source changed, and no new HQ build claim is made.

Remaining before automatic provider execution: bind this helper to canonical worker authorization and a shared deadline, implement/qualify account credential storage and refresh after explicit consent, reconcile interrupted runtime state, qualify actual tool review and real Memex project context, then execute and independently review a real development mission. The installed services and unsupported-profile guards remain unchanged.
