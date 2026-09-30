# Recovery diagnostic staging — 2026-09-30

Owner-route test added and passed in canonical HQ: unauthenticated 401, non-owner403, malformed mission/query400 before reader access; successful request uses only authenticated actor and server-selected workspace, private/no-store response; internal errors return503 without details. Reader scope/freshness tests also passed. These use auth fixtures, not a real browser session.

Fresh canonical source export:1144 files,305 test files,170 excluded. VPS build verifies each manifest hash/size and exact package/lock equality before reusing existing dependencies. Source image `sha256:501aee05ffaf05ef94927cc5cf5b100c938b709b5adad9d6f4f0a398ecfac59b`. Source directory `/opt/oria-openhands-qualification/hq-recovery-source`; local `.validation/hq-recovery-source`.

Web build succeeded with only public browser configuration. Runtime image `sha256:f4cce277ac346c3063c835eac0b550efcfae869873985e4f49edb476c71c307c`. Candidate `oria-hq-recovery-staging`, container `b4b36aff71ec9200599acaabc45e0d8bfb09b31faaca6d6ba1236b5758c63b3b`, listens on VPS loopback3335 only. `/login` returned200. Existing owner/Supabase configuration reused privately; this is the existing database, not disposable. Do not submit qualification mutations to it.

Protected `/opt/oria-openhands-qualification/recovery-reports` mounted read-only at `/run/oria-hq-reports`. No report published yet. No provider credentials copied, no agent execution, no active HQ replacement. Inngest/model API configuration warnings remain expected; scheduled jobs/model execution not qualified.

Next: local SSH forward3335 and real browser read-only qualification. No authenticated render or successful report display has yet been observed. Do not invent a production mission/report to obtain a screenshot. If no eligible canonical launch exists, qualify unavailable state and use isolated fixture infrastructure for valid report rendering.

## Browser observation

The Windows SSH forward3335 was started (observed PID30764). In-app browser tab19 opened `/hq/missions` with the existing authenticated session and rendered the server-backed mission list. The only displayed mission was `107f0991-c063-52ff-b717-2d6f8db38af3`, still a draft with no reported result or visible OpenHands launch. The recovery panel is correctly not offered before a launch exists. No form or confirmation was submitted.

Direct navigation to that mission's recovery API was blocked by the browser client (`ERR_BLOCKED_BY_CLIENT`). No API result or HTTP authorization outcome can be inferred from this attempt. Returned to the mission page; the authenticated render was observed again. Actual report rendering remains unqualified because there is no eligible launch in this database. Next use disposable qualification data for the positive rendering case, without fabricating an execution in the existing HQ database.
