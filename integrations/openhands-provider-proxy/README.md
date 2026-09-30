# Provider network qualification — 2026-09-30

This is a tested network candidate, **not an enabled HQ provider**. The existing consumer and worker still reject explicit provider profiles. No Claude consent, credential mount, account connector, model request, mission or production deployment is performed here.

## Arrangement

The existing pinned agent image runs as UID 10001 with Docker `network=none`. A small Node loopback relay forwards raw bytes from `127.0.0.1:3129` to a read-only mounted Unix socket. A separate non-root proxy container receives that socket through socat and passes it to Squid on its own loopback interface. Only that proxy container has an egress network. It publishes no port and shares no network with the agent or application services. Squid handles the HTTP protocol and destination rules; the relay is not the policy boundary.

Squid accepts only CONNECT on port 443 to the four exact named Claude/Anthropic hosts, denies private destinations, and finishes with deny-all. No TLS interception occurs. Certificate verification remains with the client. This is destination restriction, not inspection of HTTP paths or prevention of data transfer to an allowed provider. Proxy hostname/DNS policy is not proof against every DNS or CDN abuse scenario. Agent commands can use the same permitted tunnel; there is no claim of per-tool network attribution.

`qualify.py` builds an image, records its exact digest and installed package inventory, creates uniquely named disposable containers/network, inspects Docker settings, runs the real probe, and removes its containers/network in `finally`. The image and evidence directory remain for inspection. Build-time Debian packages are not version-pinned; run-time image digests are recorded, and a rebuild must be requalified. This candidate is not part of automatic startup.

## Verified result

See `qualification-evidence.json` and `qualified-policy.json`, copied from the VPS run `hq-provider-probe-eeff823ee0db`.

- Six disallowed requests receive HTTP 403: foreign domain, loopback IP, metadata IP, wrong port, deceptive hostname suffix, plain HTTP method.
- TLS 1.3 and certificate verification succeed for `api.anthropic.com`, `claude.ai`, `claude.com`, `platform.claude.com`.
- Direct connections to a public IP and metadata IP fail from the agent container.
- The loopback relay passes permitted TLS and retains denial of the foreign host.
- Actual Docker inspect confirms non-root users, read-only root filesystems, dropped capabilities, no-new-privileges, no published ports and no Docker socket. Agent mounts are read-only.
- Single-run connection durations: 38, 27, 28, 26 ms respectively. These include proxy connection and TLS establishment, not model latency or a controlled before/after benchmark. Proxy snapshot: approximately 12.4 MiB, three processes; not a load test.
- Cleanup inspection found no remaining qualification container or network. No active application container was changed.

The first probe attempt failed because the runtime image's real entrypoint is `python /runner/run_mission.py`, not bare Python. Qualification now overrides its entrypoint explicitly; it does not alter the mission image or weaken launch checks.

## Policy identity and remaining integration

The canonical JSON candidate manifest includes both image digests, hashes of the Squid config/entrypoint/relay, and the intended transport. Its SHA-256 is `0e89f8c258736ce30e465244f56c99cf2a7afc7e455b0887bddef634584c29ba`. This now identifies real tested artifacts; it is not yet loaded or enforced by the HQ host registry. `authentication: subscription` and disabled account connectors express intended future policy, not authenticated CLI evidence.

Next: add protected manifest loading and digest verification to the host; bind per-mission proxy/relay lifecycle and actual settings; preserve refusal until those match. Then qualify the pinned CLI through this path, approved account storage/refresh, tool inventory/review, cancellation and restart behavior. Keep the pending account-consent decision separate. Retain Memex project isolation and exact approved mission binding.

## Sources

- [Claude Code network configuration](https://code.claude.com/docs/en/network-config): documented proxy variables and provider endpoints. This does not itself prove our CLI uses the relay.
- [Secure agent deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment): outside-boundary proxy patterns.
- [Squid access policy](https://www.squid-cache.org/Doc/config/http_access/) and [ACL reference](https://www.squid-cache.org/Doc/config/acl/): explicit deny rules, domain matching and destination restrictions.

Operator qualification command on the isolated VPS source directory: `python3 qualify.py`. Requires Docker and the exact locally available runtime image; do not attach an account or production workspace to this probe.
