# ApprovedServerBinding — raccordement requis, non implémenté (par périmètre)

2 octobre 2026. Mandat : `docs/CLAUDE-REPRISE-BACKEND-2026-10-02.md`, point 4
("Préserver budgets existants... Contrat Cursor ApprovedServerBinding...
patch pas encore intégré... Documenter raccordement requis sans modifier
son code"). Constat fait pendant ce lot, pas anticipé : Cursor modifie
`src/server/ai/` **en ce moment même**, dans le même worktree
`hq-acces-reprise`, en parallèle de ce lot. Ce document décrit l'état exact
observé et ce qui resterait à faire côté HQ — sans toucher à un seul fichier
sous `src/server/ai/`.

## Ce qui a changé côté Cursor (observé, pas supposé)

`src/server/ai/server-capability-catalog.ts` définit maintenant :

```ts
export type ServerCapability = {
  accountId: string;   // nouveau champ requis
  modelId: string;
  provider: string;
  // ...
};

export type ServerCapabilityCatalog = {
  source: string;
  observedAt: string;
  revision: string;    // nouveau champ requis
  entries: readonly ServerCapability[];
};

export type ApprovedServerBinding = {
  accountId: string;
  workspaceId: string;
  modelId: string;
  billingKind: ServerBillingKind;
  catalogRevision: string;
};

export type ServerEmissionAssessment =
  | { emit: true; capability: ServerCapability; billingKind: "api"; notToExceedCents: number }
  | { emit: false; disposition: "non_api"; capability: ServerCapability;
      billingKind: "verified_free" | "subscription"; requestedModelId: string }
  | { emit: false; block: ServerEmissionBlock; requestedModelId: string };
```

`assessServerEmission()` refuse désormais toute entrée dont `accountId` est
absent, vide, ou égal à `provider` (`verifiedEntry()`), et accepte un
`accountId` optionnel en entrée pour filtrer par compte avant d'évaluer
`billingKind`/état. Le cas "authorized, billing non-api" (abonnement ou
gratuit vérifié) est maintenant un variant distinct `disposition: "non_api"`
— explicitement **pas** `emit: true`. C'est la phrase du mandat rendue
concrète dans le type lui-même : *"non_api_authorized ne vaut pas
exécution"* — ce variant EST littéralement le refus structurel de confondre
"authorized" avec "émissible", même pour un abonnement.

## Conséquence mesurée, pas modifiée

`src/server/missions/model-emission-gate.ts` (dépendance de
`model-emission-launch-gate.ts`, **hors périmètre élargi explicite de ce
lot** — seul `model-emission-launch-gate.ts` y figure) construit encore ses
objets `ServerCapability`/`ServerCapabilityCatalog` sans `accountId` ni
`revision`. Résultat vérifié :

- `npx tsc --noEmit` sur tout le dépôt : **14 erreurs, stables, confinées à
  3 fichiers** : `src/server/ai/llm-json-provider.ts` (9),
  `src/server/ai/model-router.ts` (3, consomment leur propre contrat mis à
  jour de façon incohérente entre eux — travail Cursor en cours, pas
  analysé plus loin ici), `src/server/missions/model-emission-gate.ts` (2 —
  `accountId`/`revision` manquants).
- `node --test src/server/missions/model-emission-gate.test.mjs` : **11 des
  11 tests de ce fichier (jamais touché par ce lot) échouent**, pour la
  même cause runtime (`verifiedEntry()` refuse toute entrée sans
  `accountId`, donc tout devient `not_listed` indépendamment de l'état de
  connexion réel).
- `node --test src/server/missions/model-emission-launch-gate.test.mjs` :
  **4 tests préexistants (non écrits par ce lot) échouent pour la même
  cause**, confirmé par comparaison avant/après avec `git stash` ciblé puis
  restauré intégralement (aucune perte). Tous les tests ajoutés ou modifiés
  par CE lot passent (voir rapport principal) : la logique ajoutée a été
  isolée dans une fonction pure (`approvalStillAuthorizes`) testée
  indépendamment, précisément pour ne pas dépendre de ce chantier en cours.

Rien de ce qui précède n'a été corrigé par ce lot : ni
`model-emission-gate.ts` (hors périmètre nommé), ni évidemment
`src/server/ai/*` (propriété exclusive de Cursor, mandat explicite de ne pas
y toucher).

## Raccordement que `evaluateModelEmissionGate` devrait faire, une fois le patch Cursor intégré

Décrit ici pour que l'intégration future n'ait pas à redécouvrir le
problème — aucune ligne ci-dessous n'a été écrite dans le code :

1. **`accountId` de la capability** — doit venir d'une identité de compte
   réellement observée, jamais inventée. Candidat naturel une fois qu'un
   vrai probe existe (`runner-executor-connection-probe.ts`, ce lot) :
   dériver un `accountId` stable depuis la preuve de connexion elle-même
   (p.ex. un hash de l'évidence redactée côté `claude auth status --json`,
   ou un identifiant que la sonde expose explicitement) — jamais le
   `provider.id` lui-même (`verifiedEntry()` l'interdit déjà explicitement :
   `accountId !== provider`).
2. **`revision` du catalogue** — candidat naturel déjà présent dans ce
   dépôt : `providerProfile.policySha256` (le digest de policy déjà
   verrouillé par `providerProfileSchema` et par
   `integrations/openhands-runner/provider_policy.py` côté Orchestrator).
   Lier `catalogRevision` à ce digest attacherait la fraîcheur du catalogue
   à la policy réellement qualifiée pour CE lancement — pas une métrique
   indépendante à inventer.
3. **`ModelEmissionGateRequest`** (`model-emission-gate.ts`) n'a aujourd'hui
   aucun champ `accountId`. Il en faudrait un, dérivé du MÊME probe que la
   connexion (jamais un second axe de vérité), transmis par
   `createGatedOpenHandsLaunch` à `evaluateModelEmissionGate`, exactement
   comme `invokedProviderId` l'est déjà.
4. **Le nouveau variant `disposition: "non_api"`** — `model-emission-gate.ts`
   et `model-emission-launch-gate.ts` devront le distinguer explicitement
   de `emit: true` partout où `gate.assessment.emit` est lu aujourd'hui
   (actuellement une seule lecture, `gate.assessment.emit !== true`, qui
   reste correcte techniquement puisque `disposition: "non_api"` a déjà
   `emit: false` — mais le statut `model_emission_blocked` retourné
   devrait probablement distinguer ce cas d'un vrai blocage pour que
   l'appelant (la route HQ) sache qu'il s'agit d'une exécution non-API
   correctement reconnue mais toujours refusée, pas d'un probe cassé).

## Ce que ce lot n'a PAS fait, explicitement

Aucune ligne de `src/server/ai/*` modifiée. Aucune ligne de
`model-emission-gate.ts` modifiée (hors périmètre nommé par le mandat).
Aucun `accountId`/`revision` inventé ou codé en dur nulle part. Aucune
tentative de faire passer les 11+4 tests préexistants cassés par ce
chantier Cursor en cours — ce serait soit modifier du code hors périmètre,
soit masquer un échec réel derrière un mock qui ne prouverait rien.
