# Contrat catalogue serveur

Module produit : `src/server/ai/server-capability-catalog.ts`.
Claude l'importe. Il ne modifie pas `src/server/ai/`. L'ACP reste hors de ce dossier.

Entrée HQ stricte : `generateHqStructuredJson` dans `src/server/ai/llm-json-provider.ts`.
Elle exige `ApprovedServerBinding`, `serverCatalog.revision`, `workspaceId` et `modelId`.
Sans catalogue, workspace ou modèle : `catalog_required`, zéro fetch.
Sans binding, ou avec un champ vide : `binding_required`, zéro réserve, zéro fetch.
`generateStructuredJson` sans ce drapeau reste le chemin des appelants déjà livrés. Ce n'est pas une preuve de sécurité.

## Objet

`ServerCapability` : `accountId`, `modelId`, `provider`, `state` (`listed` | `connected` | `authorized`), `source`, `observedAt`, `tools`, `billingKind`, `tariff`, `workspaceId`.

`accountId` est le compte serveur. Il n'est pas le nom du fournisseur. Une entrée dont `accountId` égale `provider` n'est pas vérifiée.

`ServerCapabilityCatalog.revision` est la révision que le binding doit répéter.

`ApprovedServerBinding` : `accountId`, `workspaceId`, `modelId`, `billingKind`, `catalogRevision`.

`billingKind` :

- `api` : `tariff` USD, `notToExceedCents` entier strictement positif. Ce plafond est passé à `authorizeCallAttempt` seulement après que le binding égale l'entrée. Une retenue serveur plus haute est libérée avant `mark`, sans socket.
- `verified_free` : `tariff` null. `emit` est faux, `disposition` est `non_api`. Pas un coût observé de 0. Pas une exécution.
- `subscription` : `tariff` null. `emit` est faux, `disposition` est `non_api`. Pas un coût observé de 0. Pas une exécution. `emit: true` ne lance pas un abonnement.

`notToExceedCents` 0, ou un tarif posé sur le gratuit ou l'abonnement, donne `tariff_unknown`.
`observedAt` de l'entrée et du tarif : âge maximal `TARIFF_MAX_AGE_MS` (24 h). Futur ou périmé : `capability_stale` ou `tariff_stale`.
`provider` doit être celui de l'adaptateur réellement invoqué. Sinon `provider_mismatch`. Une autorisation OpenAI ne couvre pas un appel Anthropic du même `modelId`.

## Décision

`assessServerEmission({ catalog, modelId, workspaceId, requiresTools, nowMs, invokedProvider, accountId })`.

Sans `accountId`, deux comptes du même modèle, du même workspace et du même fournisseur donnent `account_ambiguous`. Un `accountId` absent du catalogue donne `account_mismatch`. La première entrée n'est plus choisie à leur place.

Blocages : `not_listed`, `public_catalog_only`, `not_authorized`, `workspace_mismatch`, `provider_mismatch`, `capability_stale`, `tools_unavailable`, `tariff_unknown`, `tariff_stale`, `catalog_required`, `account_mismatch`, `account_ambiguous`, `binding_required`, `binding_mismatch`.

`listed` et `connected` ne donnent aucun droit. Le catalogue public ne suffit pas.

Sur le chemin strict, `catalogRevision`, `workspaceId` ou `modelId` différent du binding : `binding_mismatch` avant toute réserve et avant tout fetch. Un `billingKind` approuvé qui n'est pas celui de l'entrée donne le même refus. Le sujet d'appel ne remplace pas ce tuple.

Gratuit ou abonnement autorisé et lié : `non_api_authorized`. `accountId` est celui de l'entrée retenue. `reservation.accessClass` est `subscription` ou `unknown`, jamais `api`, même si l'identifiant de modèle est callable. `executedModelId` null. `monetaryUsd` null, jamais 0. `networkRequestSent` faux. Zéro fetch. Pas de descente vers l'API payante.

`requestedModelId` vient de l'appel, qui doit égaler le binding. `executedModelId` vient du corps fournisseur, sinon null. Le coût monétaire reste inconnu sans réponse réelle.

## Commande

```
node --test --test-concurrency=1 \
  src/server/ai/server-capability-catalog.test.mjs \
  src/server/ai/cost-ladder.test.mjs \
  src/server/ai/model-router.test.mjs \
  src/server/ai/llm-json-provider.test.mjs \
  src/server/ai/routing-execution.test.mjs \
  src/server/ai/anthropic-json-client.test.mjs \
  src/server/ai/openai-json-client.test.mjs \
  src/server/ai/json-client-deadline.test.mjs \
  src/server/ai/call-reservation.test.mjs
```

## Limites

Pas de facture, pas d'appel fournisseur réel, pas de découverte dans ce dossier.
Le délai de corps et `emitted_unknown` sont inchangés. La facturation n'est pas réécrite.
Sans `HQ_CALL_RESERVATION=1`, une entrée `api` du chemin strict ne part pas : le plafond ne peut pas être appliqué.
Aucun client JSON pour `openrouter/free`.
`non_api_authorized` n'exécute aucun modèle. La mission réelle reste non prouvée.
Ce cloud n'a pas vu le localhost Windows.
