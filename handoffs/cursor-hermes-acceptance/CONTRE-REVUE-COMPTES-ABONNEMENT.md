# Contre-revue comptes abonnement

Lecture seule du produit `7fb41bb`. Pas d'ACP, pas du raccordement local de Claude, pas d'exécution.

`non_api_authorized` n'exécute aucun modèle. `executedModelId` reste null, `monetaryUsd` reste null, `networkRequestSent` est faux. Ce n'est ni un coût zéro ni une mission réelle.

## Risques

1. Deux comptes du même fournisseur sont le même choix. `ServerCapability` n'a pas d'identifiant de compte (`src/server/ai/server-capability-catalog.ts`, lignes 27-38). `assessServerEmission` garde la première entrée de même `modelId`, `workspaceId` et `provider` (lignes 99-107). La seconde est ignorée. `generateHqStructuredJson` ne renvoie pas l'entrée retenue.

2. Un changement après approbation n'est pas lié. `LlmJsonProviderInput` n'a ni compte approuvé, ni modèle approuvé, ni hash (`src/server/ai/llm-json-provider.ts`, lignes 61-95). L'identité de réservation est workspace, sujet, appelant, fournisseur (`src/server/ai/call-reservation.ts`, lignes 67-71), sans modèle ni compte. Un abonnement sort avant toute réserve (lignes 388-389) et ne prend donc pas le droit d'émission. Un appel suivant peut porter un autre modèle ou un autre compte.

3. La classe d'accès contredit l'abonnement. Pour `claude-sonnet-4-6`, `accessClassForModel` répond `api` dès que l'id est callable (lignes 93-95). Le refus abonnement recopie cette classe alors que `reason` vaut `subscription` (`llm-json-provider.ts`, lignes 222-242). `chooseModel` refuse le palier non API ( `model-router.ts`, lignes 483-485) mais ne nomme pas le compte.

## Tests absents

Deux entrées `subscription`, même modèle, même workspace, comptes différents : la sortie ne peut pas dire lequel. Une approbation puis un second appel, autre modèle ou autre compte, même sujet : aucun refus de substitution. Un id API marqué `subscription` : `accessClass` ne doit pas être lu comme une émission API. Aucun de ces trois cas n'est dans `server-capability-catalog.test.mjs`.

## Contrat minimal de l'appelant

Fournir un `accountId` observé côté serveur, distinct du `provider`. Le workspace de l'appel doit être celui de ce compte. Au moment de `generateHqStructuredJson`, comparer le tuple approuvé `accountId`, `modelId`, `billingKind` et l'instant ou le hash du catalogue. Toute différence refuse, sans fetch. `requestedModelId` vient de ce tuple. `executedModelId` vient du corps fournisseur, sinon null. Pour `subscription` et `verified_free`, n'accepter que `non_api_authorized`, `executedModelId` null, `monetaryUsd` null. Ne pas traiter `assessServerEmission` `emit: true` ni `accessClass` `api` comme une exécution.
