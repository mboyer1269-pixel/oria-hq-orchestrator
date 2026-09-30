# Recovery component visual qualification

2026-09-30: in-app browser exercised the unchanged real `OpenHandsRecovery` component inside a local disposable source snapshot, with an explicitly labelled synthetic page and synthetic API responses. No real mission, account, model, or production database used.

Three buttons were clicked. While requests were pending, buttons were disabled and the live status showed loading. After responses, the recent case displayed stopped proxy/absent network and observation time; stale case displayed verification needed, unknown proxy and incomplete inspection; unavailable503 displayed that unavailability proves neither failure nor success. Buttons re-enabled. Screenshot inspection confirmed desktop readability. Mobile viewport and authenticated positive-report UI remain unqualified.

Local fixture: `.validation/hq-recovery-source`, intentionally modified after its source-image export; DO-NOT-DEPLOY.md warns its manifest is now stale. Canonical HQ source/API and previously built VPS images are unchanged. Dev server used webpack on127.0.0.1:3350 (Turbopack rejected the external node_modules junction), then was stopped; temporary browser tab20 closed.

Combined evidence remains scoped: browser verifies actual component interaction with fixtureAPI; disposable VPS harness separately verifies actual Memex/HQ/worker/report publication and HQ file reader. This does not claim a single authenticated browser-to-model mission.
