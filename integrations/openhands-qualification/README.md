# OpenHands SDK qualification without inference

Run `python qualify.py`, then `python qualify_conversation.py` with exactly
`openhands-sdk==1.50.0` inside a no-network, no-credential container. Mount this
directory read-only and provide a writable temporary directory. The parent
operator supplies the reviewed image; these scripts install nothing.

`qualify.py` observes the real upstream private permission bridge and checks a
qualification-only default-deny override. That override is **not integrated**
with ACPAgent. Neither a tool title nor an allow-list of Read/Edit/Write safely
authorizes paths or side effects. A future production policy requires a public
bridge callback/factory, canonical requests, scoped paths and durable decisions.

`qualify_conversation.py` uses the actual SDK conversation lifecycle and a local
synthetic ACP stdio peer. It proves initialize/new-session/prompt/update/finish,
not Claude authentication, inference, cancellation or crash recovery.

Pinned upstream source: `OpenHands/software-agent-sdk` release `v1.50.0`, commit
`dcf401af7a9a302ef92cb7d092e1df9bb659daa5`. In
`openhands-sdk/openhands/sdk/agent/acp_agent.py`, `_OpenHandsACPBridge` is private;
`request_permission` auto-selects the first permission option (1602–1619).
ACPAgent constructs it directly (2914). Its default Claude session mode is
`bypassPermissions` (1748–1755). Setting mode to `default` alone does not fix
automatic permission responses.

No execution results are asserted by this document: use script output as evidence.

Run `python qualify_permissions_conversation.py` on Linux for complete synthetic
permission exchanges. It runs upstream and deny cases in separate processes,
with 35-second in-process and 45-second supervisor deadlines. The peer requests
permission over real ACP JSON-RPC and reports the actual response. Each case
persists a SDK conversation and reloads its events using the public constructor.
No remote session is resumed. The deny case monkeypatches the private bridge
symbol **only in its isolated qualification process**, restoring it in finally.
This is evidence for a future upstream extension, not a production integration
or a thread-safe customization API.

`python qualify_cancellation.py` exercises public `Conversation.arun()` and
`interrupt()` against a synthetic prompt kept open until `session/cancel`.
The peer records the actual notification in a temporary receipt and replies
`stopReason=cancelled`. The driver requires a finished run, paused state, and
peer process exit after `close()`. It has bounded waits and a 40-second hard
deadline; retain the external container timeout as the final cleanup boundary.
This does not qualify Claude, descendant tool processes, or provider resume.
The existing simple and permission peer modes remain unchanged.
