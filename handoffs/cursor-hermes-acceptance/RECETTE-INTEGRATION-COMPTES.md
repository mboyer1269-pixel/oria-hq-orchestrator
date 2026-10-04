# Recette d'intégration — comptes, binding, non-émission

Qualification indépendante. Aucun code produit n'est ajouté par ce document.
Codex intègre `cursor-routage-compte-approuve.patch`. Claude garde le registre, les profils, la sonde de compte du runner et la révocation atomique.
Ce texte ne lit pas l'arbre local de Claude et ne cite aucune commande à lui.
Pas de dépendance nouvelle, pas de login, pas d'API payante, pas de sous-agent.

`non_api_authorized` n'exécute aucun modèle. `executedModelId` reste null. `monetaryUsd` reste null, jamais 0. La mission réelle reste non prouvée. Ce cloud n'a pas vu le localhost Windows.

## Périmètre

| Rôle | Tient | Ne tient pas |
| --- | --- | --- |
| Codex | Appliquer le patch sur le produit, puis relancer la commande déjà connue | Registre, profils, sonde, révocation, ACP |
| Claude | Registre, profils, sonde du compte sur le runner, révocation atomique avant l'appel | `src/server/ai/` |
| Ce document | Scénarios, commande et fixtures déjà dans le produit | Un nouveau test, un appel réel, le code de Claude |

Patch à intégrer, parent `7fb41bb` :

- fichier `handoffs/cursor-hermes-acceptance/cursor-routage-compte-approuve.patch`
- SHA256 `49fe6534d5db0931f9e06c9143e4fec3e03422824382f3a7be4af7dc2a606aa4`
- commit produit de référence `86cc891`, arbre `4223d1c4f04e2c69ac044275728327e0a34ab2ba`
- `git am` sur `7fb41bb` reproduit cet arbre. Le hash de commit appliqué peut différer.

`proofs/hermes-hq-acceptance.mjs` est une autre recette. Son exit 0 n'est pas cette qualification.

## Contrat exact de l'appelant

Module `src/server/ai/server-capability-catalog.ts` et entrée `generateHqStructuredJson` dans `src/server/ai/llm-json-provider.ts`.
L'appelant importe. Il ne modifie pas ces fichiers.

Chaque appel strict fournit les cinq champs, tous non vides :

```ts
type ServerBillingKind = "api" | "verified_free" | "subscription";

type ApprovedServerBinding = {
  accountId: string;
  workspaceId: string;
  modelId: string;
  billingKind: ServerBillingKind;
  catalogRevision: string;
};
```

`generateHqStructuredJson` exige en plus `serverCatalog` (`source`, `observedAt`, `revision`, `entries`) , `modelId` et `workspaceId`.
`serverCatalog.revision` doit être égal à `approved.catalogRevision`.
`approved.workspaceId` doit être égal à `workspaceId`.
`approved.modelId` doit être égal à `modelId`.

Chaque entrée vérifiée a un `accountId` non vide et différent de `provider`.
L'entrée retenue doit répéter `accountId`, `workspaceId`, `modelId` et `billingKind` du binding.
`state` doit être `authorized`. `listed` et `connected` ne donnent aucun droit.

`billingKind` :

- `api` : `tariff` USD, `notToExceedCents` entier strictement positif, et `HQ_CALL_RESERVATION=1`. Sinon le chemin strict ne part pas.
- `verified_free` ou `subscription` : `tariff` null. Le résultat attendu est `non_api_authorized`, pas une émission. `emit: true` n'est pas une exécution de ces deux sortes.

Le routeur ne mémorise pas l'accord précédent. L'appelant ne remplace pas le tuple sans un nouvel accord serveur.
Le sujet d'appel ne remplace pas le tuple. L'identité de réservation reste workspace, sujet, appelant et fournisseur. Elle ne contient ni le compte ni le modèle. Le binding est contrôlé avant cette réservation.

Résultat à lire, jamais à déduire :

- `requestedModelId` est l'id de l'appel, égal au binding.
- `accountId` du résultat est le compte de l'entrée retenue, ou null si aucun binding n'a été retenu.
- `executedModelId` vient du champ `model` du corps fournisseur. Sans ce champ, il reste null. Ce n'est pas l'id de la requête.
- `cost.monetaryUsd` reste null. Des jetons observés ne sont pas un prix. Un refus n'est pas un zéro.
- `reservation.accessClass` pour un abonnement lié est `subscription`. Pour un gratuit vérifié, `unknown`. Jamais `api` sur ces deux refus, même si l'id est callable.

Refus avant réserve et avant fetch : `catalog_required`, `binding_required`, `binding_mismatch`, `account_mismatch`, `account_ambiguous`, `not_listed`, `public_catalog_only`, `not_authorized`, `workspace_mismatch`, `provider_mismatch`, `capability_stale`, `tools_unavailable`, `tariff_unknown`, `tariff_stale`.

`generateStructuredJson` sans catalogue reste le chemin legacy. Ce n'est pas une preuve de sécurité.

## Tests déjà exécutés

Machine de cette passe : Node v22.14.0. Pas Windows. Pas de fournisseur réel. Clé synthétique `ANTHROPIC_API_KEY=synthetic` seulement dans les tests. `fetch` injecté.

Commande, depuis la racine produit au commit `86cc891` :

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

Résultat observé ici : 106 tests, 0 échec, 0 skip, exit 0, environ 7,1 s. Ce n'est pas la qualification d'intégration. Codex relance la même commande après `git am`. Le compte de tests ne qualifie pas le registre de Claude.

Fixtures du fichier catalogue, déjà dans `src/server/ai/server-capability-catalog.test.mjs` :

- `HAIKU` = `claude-haiku-4-5-20251001`
- `WORKSPACE` = `ws-catalogue`
- `ACCOUNT` = `acct-server-1`
- `REVISION` = `rev-1`
- comptes `acct-a` et `acct-b`
- `HQ_CALL_RESERVATION=1`
- `closedGate` : `reserve`, `markEmitted`, `release` et `consume` lèvent si on les appelle

| Scénario couvert par un test existant | Fixture | Observé |
| --- | --- | --- |
| Deux comptes abonnement, même modèle, même workspace, sans `accountId` | `assessServerEmission` sur `acct-a` et `acct-b`, Haiku, `ws-catalogue` | `account_ambiguous`, `emit` faux |
| Compte lié nommé, pas le premier | `generateHqStructuredJson`, `approved.accountId` `acct-b`, `billingKind` `subscription`, sujet `subject-two-accounts` | `non_api_authorized`, `accountId` `acct-b`, pas `acct-a`, `accessClass` `subscription`, `executedModelId` null, `monetaryUsd` null, 0 fetch, 0 réserve, 0 mark |
| `accountId` égal au provider | `assess({ accountId: "anthropic" })` | `not_listed` |
| Après accord, second appel, autre modèle, même sujet | accord `acct-a` / Haiku / `subscription` / `rev-1`, puis `modelId` `gpt-4o-mini`, sujet `subject-binding` | `binding_mismatch`, 0 fetch, 0 réserve, 0 mark, 0 release |
| Après accord, autre compte absent du catalogue | `approved.accountId` `acct-b` alors que l'entrée est `acct-a` | `account_mismatch`, mêmes compteurs à 0 |
| Après accord, autre révision | catalogue `rev-2`, binding `rev-1` | `binding_mismatch` |
| Après accord, autre `billingKind` | binding `api` sur une entrée `subscription` | `binding_mismatch`, pas une émission API |
| Binding manquant | `generateHqStructuredJson` avec catalogue, sans `approved` | `binding_required` |
| Id callable facturé abonnement | Haiku, `billingKind` `subscription`, `tariff` null, sujet `subject-subscription-class` | `assess` `emit` faux, `disposition` `non_api`. Appel : `non_api_authorized`, `accessClass` `subscription` et non `api`, `executedModelId` null, `monetaryUsd` null et différent de 0, `networkRequestSent` faux, 0 fetch, 0 réserve |
| Gratuit vérifié | `billingKind` `verified_free`, `tariff` null | `non_api_authorized`, `monetaryUsd` null, 0 fetch |
| Catalogue public ou seulement connecté | `state` `listed` ou `connected` | `public_catalog_only` ou `not_authorized`. Le test `listed` avec gate ne réserve pas et ne fetch pas |
| Workspace de l'entrée différent de l'appel, sans second binding | `assess({}, { workspaceId: "other-workspace" })` | `workspace_mismatch`. Ce n'est pas le scénario « workspace changé après accord » |
| Corps sans champ `model` | `routing-execution.test.mjs`, id demandé `claude-sonnet-4-6`, réponse synthétique sans `model` | `requestedModelId` égal à l'id envoyé, `executedModelId` null |
| Réponse perdue | catalogue, sujet `subject-lost-response`, `AbortError` injecté | un socket, `executedModelId` null, `monetaryUsd` null, statut `emitted_unknown`. Le second appel ne rouvre pas de socket |
| Usage sans prix | réponse avec jetons, ou sans usage | `monetaryUsd` null. `unknown_cost` n'est pas 0 |
| Deux appels legacy simultanés, même sujet | `call-reservation.test.mjs`, `generateStructuredJson`, workspace `ws-a`, sujet `mission-1`, gate mémoire, sans catalogue ni `approved` | le second a 0 fetch, statut `lost`, raison `emit_right_held`. Le premier peut consommer. `ws-b` n'est pas bloqué par `ws-a` |

`chooseModel` avec deux entrées `gpt-4o-mini` abonnement et sans `accountId` refuse `account_ambiguous`, `executedModelId` null. Avec `accountId` `acct-b`, la raison est `subscription`. Ce n'est pas une émission.

## Recette restante

Ces scénarios ne sont pas exécutés. Aucune commande de Claude n'est inventée ici. Après intégration par Codex, la seule commande produit à relancer est celle de la section précédente. Elle ne couvre pas les trous ci-dessous.

| Scénario encore ouvert | Ce qui existe déjà | Ce qui manque |
| --- | --- | --- |
| Workspace changé après accord | Le contrat refuse `binding_mismatch` si `approved.workspaceId` diffère de `workspaceId`, avant réserve et avant fetch. La fixture étrangère existante répond `workspace_mismatch` au niveau `assess`, pas sur un second `generateHqStructuredJson` | Le cas n'est pas dans la boucle `subject-binding`. À observer au moment de l'intégration : même sujet, binding resté sur `ws-catalogue`, appel passé à un autre workspace, 0 fetch, 0 réserve, `executedModelId` null, `monetaryUsd` null |
| Deux demandes simultanées sur l'entrée stricte | Le droit d'émission legacy est prouvé pour `mission-1` / `ws-a` sans binding | Pas deux `generateHqStructuredJson` concurrents, pas deux comptes, pas un abonnement face à un appel API du même sujet. L'abonnement sort avant la réserve et ne prend donc pas le droit d'émission. Le routeur ne retient pas l'accord d'un appel à l'autre |
| Révocation atomique avant réservation | Si l'entrée présentée n'est plus `authorized`, les fixtures existantes donnent `not_authorized`, `public_catalog_only`, `not_listed` ou `account_mismatch`, avec 0 réserve sur le blocage catalogue | Personne ici n'a révoqué un compte de runner. La sonde, le registre et l'atomicité sont à Claude. Tant que l'appelant présente encore l'ancienne entrée `authorized`, le routeur ne révoque rien |
| `non_api_authorized` traité comme une émission par l'appelant | Le routeur injecté refuse l'émission | Le branchement réel de Claude n'est pas lu et n'est pas qualifié. Un `emit: true` ou un `accessClass` `api` ne doit pas lancer l'abonnement |
| Coût ou modèle inconnu sans réponse réelle | Les fixtures injectées gardent null sans corps, sans champ `model`, ou sans prix | Aucune réponse fournisseur réelle n'a été reçue. Null n'est pas un coût zéro et n'est pas une mission exécutée |

## Hors qualification

Pas de facture, pas de login, pas de secret, pas de VPS, pas de déploiement, pas de réécriture de la facturation.
Le délai de corps et `emitted_unknown` ne sont pas repris dans ce lot.
Sans `HQ_CALL_RESERVATION=1`, une entrée `api` stricte ne part pas.
Le chemin legacy sans catalogue qui fetch une fois n'est pas une preuve.
Exit 0 de la commande produit, ou de la recette Hermes, ne raccorde pas un compte et n'exécute pas de modèle.
