# Patch: persistent account-identity binding (HQ, separate, not applied)

Delivered per `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`'s "Prochaine
livraison utile" section. Supersedes an earlier in-memory-only version of
this patch (removed from here - "ne pas s'arrêter à un helper inutilisé",
don't stop at an unused helper): that version was correctly flagged as not
an operational connection/binding, stable only within one process's
lifetime. This version is real, persistent, production-capable.

## What this is

`account-identity-repository.patch` adds exactly two NEW files to the live
Oria.HQ repository:

```
src/server/agents/models/account-identity-repository.ts
src/server/agents/models/account-identity-repository.test.mjs
```

Purely additive. Reuses the **existing, already-trusted persistence
pattern** from `approval-record-repository.ts` (`mission_approvals`): a
real Supabase-backed table in production, with an explicitly gated
in-memory fallback for local development that fails closed in production
rather than silently persisting nowhere - never a new, separately-invented
storage mechanism.

Key design, unchanged from the prior version: the store is keyed by
`(provider, workspaceId, email)`, never `email` alone - the same email
under two different providers or workspaces must never merge into one
`accountId`. `accountId` itself is `crypto.randomUUID()`, never derived
from the email - nothing to reverse by dictionary/rainbow-table, unlike a
hash.

## Proof - exact output of this pass

```
$ cd hq-acces-reprise && npx tsc --noEmit
(no output, exit 0 - whole repository, real @/* path-alias resolution,
 written in place this time for a genuine type-check, not a standalone
 approximation)

$ node --test src/server/agents/models/account-identity-repository.test.mjs
  -> 12/12 passed, in place

$ git status --short -- src/server/agents/models/account-identity-repository.*
?? src/server/agents/models/account-identity-repository.ts
?? src/server/agents/models/account-identity-repository.test.mjs
(nothing else in the worktree touched - verified by full status count
 before and after)
```

Tests cover exactly what was asked: stable identity (same key -> same
accountId), restart (a fresh lookup for an already-persisted key returns
the original accountId, not a new one - the same guarantee
`approval-record-repository.test.mjs` already accepts for its own
Supabase-backed repository, since neither test suite has a live Supabase
connection), account change (different provider, different workspace,
different email - each produces a different accountId), and unknown
refusal (empty/non-string provider, workspaceId, or email throws, never
silently coerced) - plus the non-determinism, no-email-leak, normalization,
and production-fail-closed tests carried over from the prior version.

## What this patch deliberately does NOT do

- Does not create the `account_identities` Supabase table itself - a
  database migration, a separate deployment step, exactly like
  `mission_approvals`'s own table is not created by
  `approval-record-repository.ts` either.
- Does not modify `local-runtime-probe.ts` to call `resolveOpaqueAccountId`
  from `classifyClaudeCodeProbe` - the one-line integration point is
  described in the proposal doc.
- Does not decide the email-rotation question - a different email is
  always a different accountId, deliberately, documented as an open
  decision.
- Does not call, activate, or reach any model/provider API.
- Is not itself an execution authorization. Real mission execution stays
  gated behind the approved account/model/mission chain this patch does
  not touch.

## How to apply

From the Oria.HQ repository root:

```
git apply patches/hq-account-identity-binding/account-identity-repository.patch
```
