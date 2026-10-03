# Patch: opaque account-identity binding (HQ, separate, not applied)

Delivered per `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, point 2, after its
"Clarification du responsable". Full design rationale, stability/rotation
discussion and prerequisites:
`docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RACCORDEMENT-COMPTE-PROPOSITION-2026-10-03.md`.

## What this is

`account-identity-binding.patch` is a real, unified git diff adding exactly
two NEW files to the live Oria.HQ repository:

```
src/server/agents/models/account-identity-binding.ts
src/server/agents/models/account-identity-binding.test.mjs
```

Both are purely additive - the patch creates these two files and touches
nothing else. It was generated from, and tested directly in, the live HQ
worktree (`C:\Users\micha\Dev\Oria.HQ\.claude\worktrees\hq-acces-reprise`),
then extracted back out, specifically so it could be produced and proven
without modifying or conflicting with the substantial, unrelated work
already in progress and uncommitted there (Cursor's `src/server/ai/*`
contract change and its own already-wired `accountId`/`catalogRevision`
plumbing through `model-emission-gate.ts`/`model-emission-launch-gate.ts` -
see the proposal doc). The two new files were left untracked (`??`) in that
worktree exactly as found, matching this project's standing rule never to
commit in a worktree not entered via the dedicated tool.

## Proof it is real, not aspirational

A bounded, read-only review (one subagent, scoped to just these two files)
found two real defects in the first version of this patch, both fixed
before delivery:
1. The "not a hash" test only checked the result against one specific
   deterministic function (sha256); it did not prove true randomness. Fixed
   by adding a test that resolves the SAME email against two independent
   fresh stores and asserts the two results differ - this would catch ANY
   swapped-in deterministic derivation, not just sha256.
2. The email was not normalized before use as the store's lookup key, so
   the same real account returning its email with different casing or
   incidental whitespace across two probes would have silently minted two
   different `accountId`s for one account - breaking the "same email ->
   same accountId" stability guarantee this module exists to provide.
   Fixed: `resolveOpaqueAccountId` now trims and lower-cases the email
   before every lookup/store operation, and that is what gets persisted.

Run directly in `hq-acces-reprise` after both fixes, before being extracted
into this patch:

```
node --test src/server/agents/models/account-identity-binding.test.mjs
  -> 12/12 passed

npx tsc --noEmit
  -> zero new errors (same pre-existing Cursor-internal errors as before,
     unrelated to this addition)
```

## What this patch deliberately does NOT do

- Does not modify `local-runtime-probe.ts` to actually call
  `resolveOpaqueAccountId` from `classifyClaudeCodeProbe` - that file is
  being actively, substantially modified uncommitted by other work right
  now; wiring it in here would be exactly the "concurrent modification"
  this lot was told to avoid. The one-line integration point (which
  branch, roughly which line, at the time this was written) is described
  in the proposal doc instead, for whoever applies this once that work
  lands.
- Does not create a real, protected, persistent store. Only
  `createInMemoryAccountIdentityStore()` (test/fixture-only) is provided.
  A real file-backed store needs an explicit decision from Michael first
  (new server-side personal-data storage, even if minimal) - see the
  proposal doc's prerequisites.
- Does not decide the email-rotation question - documented as an open
  decision, not resolved here.

## How to apply (once the prerequisites in the proposal doc are met)

From the Oria.HQ repository root:

```
git apply patches/hq-account-identity-binding/account-identity-binding.patch
```
