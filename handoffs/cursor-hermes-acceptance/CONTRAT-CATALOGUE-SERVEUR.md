# Contrat catalogue serveur

Module produit : `src/server/ai/server-capability-catalog.ts`.
Claude l'importe. Il ne modifie pas `src/server/ai/`.

Entrée HQ obligatoire : `generateHqStructuredJson` dans `src/server/ai/llm-json-provider.ts`.
Sans `serverCatalog`, `workspaceId` et `modelId`, le résultat est `catalog_required`, zéro fetch.
`generateStructuredJson` sans catalogue reste le chemin des appelants déjà livrés. Ce n'est pas une preuve de sécurité.

## Objet

`ServerCapability` : `modelId`, `provider`, `state` (`listed` | `connected` | `authorized`), `source`, `observedAt`, `tools`, `billingKind`, `tariff`, `workspaceId`.

`billingKind` :

- `api` : `tariff` USD, `notToExceedCents` entier strictement positif. Ce plafond est passé à `authorizeCallAttempt`. Une retenue serveur plus haute est libérée avant `mark`, sans socket.
- `verified_free` : `tariff` null. Pas un coût observé de 0.
- `subscription` : `tariff` null. Pas un coût observé de 0.

`notToExceedCents` 0, ou un tarif posé sur le gratuit ou l'abonnement, donne `tariff_unknown`.
`observedAt` de l'entrée et du tarif : âge maximal `TARIFF_MAX_AGE_MS` (24 h). Futur ou périmé : `capability_stale` ou `tariff_stale`.
`provider` doit être celui de l'adaptateur réellement invoqué. Sinon `provider_mismatch`. Une autorisation OpenAI ne couvre pas un appel Anthropic du même `modelId`.

## Décision

`assessServerEmission({ catalog, modelId, workspaceId, requiresTools, nowMs, invokedProvider })`.

Blocages : `not_listed`, `public_catalog_only`, `not_authorized`, `workspace_mismatch`, `provider_mismatch`, `capability_stale`, `tools_unavailable`, `tariff_unknown`, `tariff_stale`, `catalog_required`.

`listed` et `connected` ne donnent aucun droit. Le catalogue public ne suffit pas.
Gratuit ou abonnement autorisé : `non_api_authorized`, `monetaryUsd` null, zéro fetch. Pas de descente vers l'API payante.

## Commande

```
node --test --test-concurrency=1 \
  src/server/ai/server-capability-catalog.test.mjs \
  src/server/ai/call-reservation.test.mjs
```

## Limites

Pas de facture, pas d'appel fournisseur réel, pas de découverte dans ce dossier.
Le délai de corps et `emitted_unknown` sont inchangés. La facturation n'est pas réécrite.
Sans `HQ_CALL_RESERVATION=1`, une entrée `api` du chemin strict ne part pas : le plafond ne peut pas être appliqué.
Aucun client JSON pour `openrouter/free`.
Ce cloud n'a pas vu le localhost Windows.
