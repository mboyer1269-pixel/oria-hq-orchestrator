# Contrat catalogue serveur

Module produit : `src/server/ai/server-capability-catalog.ts`.
Claude l'importe. Il ne modifie pas `src/server/ai/`.

## Objet

`ServerCapabilityCatalog` : `{ source, observedAt, entries }`.

Chaque entrée : `modelId`, `provider`, `state` (`listed` | `connected` | `authorized`), `source`, `observedAt`, `tools`, `tariff`, `workspaceId`.

`tariff` : `{ currency: "USD", notToExceedCents, source, observedAt }` ou `null`.
Âge maximal : `TARIFF_MAX_AGE_MS` (24 h), constante serveur.

## Décision

`assessServerEmission({ catalog, modelId, workspaceId, requiresTools, nowMs })`.

Blocages : `not_listed`, `public_catalog_only`, `not_authorized`, `workspace_mismatch`, `tools_unavailable`, `tariff_unknown`, `tariff_stale`.

Seul `authorized`, même workspace, outils si `requiresTools`, tarif USD entier frais, autorise. Le catalogue public, passé en `listed`, ne donne aucun droit. Aucun prix ni accord ne vient du navigateur.

## Branchements

`chooseModel` et `generateStructuredJson` acceptent `serverCatalog`, `requiresTools`, `nowMs` en option.
Catalogue absent : les quatre ids API statiques restent sur le chemin déjà qualifié.
Catalogue présent : même un id statique doit passer `assessServerEmission` avant fetch et avant réservation.
Un id autorisé sans client JSON reste `model_unsupported`, zéro fetch, sans repli payant.
Étage gratuit sans modèle éligible : `block` `free_unavailable`, poids 0, exécution refusée.

## Retour d'émission

`requestedModelId` : l'id demandé, sinon `null`.
`executedModelId` : champ `model` du corps fournisseur, sinon `null`. Jamais recopié depuis le choix.
`provider`, `usage` : `null` si absents.
`costSource` : `provider_usage`, `refused`, `unknown` ou `estimation`.
`chooseModel` reste une estimation (`executedModelId` null). La consommation est seulement `generateStructuredJson`.

## Commande

```
node --test --test-concurrency=1 \
  src/server/ai/server-capability-catalog.test.mjs \
  src/server/ai/cost-ladder.test.mjs \
  src/server/ai/model-router.test.mjs \
  src/server/ai/llm-json-provider.test.mjs \
  src/server/ai/routing-execution.test.mjs
```

## Limites

Pas de facture, pas d'appel fournisseur réel, pas de découverte de compte dans ce dossier.
Le délai de corps reste dans les handlers HTTP, non modifiés.
`emitted_unknown` n'est pas libéré. `HQ_CALL_RESERVATION` et la facturation sont inchangés.
Aucun client JSON pour `openrouter/free`, même si un catalogue futur l'autorise.
Ce cloud n'a pas vu le localhost Windows.
