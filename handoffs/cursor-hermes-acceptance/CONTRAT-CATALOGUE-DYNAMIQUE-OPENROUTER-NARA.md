# Contrat — catalogue dynamique OpenRouter / NaraRouter

Document seul. Aucun fichier produit, aucun test ajouté, aucune dépendance, aucun appel de modèle.
Le patch compte est intégré par Codex. Codex rapporte 106 tests locaux verts sur la commande déjà connue. Ce cloud ne relance pas cette suite et n'a pas vu le localhost Windows.

`non_api_authorized` n'exécute aucun modèle. `executedModelId` reste null. `monetaryUsd` reste null, jamais 0. La mission réelle reste non prouvée.

Claude ferme le lancement : registre, profils, sonde du runner, révocation, ACP. Son arbre n'est pas lu. Antigravity reste la compatibilité ACP. Ni l'un ni l'autre ne reçoit un backend ici.

## Périmètre

Le routeur reste `src/server/ai`. La porte d'émission reste `generateHqStructuredJson` et `assessServerEmission`. Le descripteur HTTP existant reste `openrouter-http` (`RuntimeAdapterDescriptor`, `ledgerRequired: true`).

Ce contrat n'ajoute pas de routeur, pas de branche `resolveOrder`, pas de client Anthropic Messages, pas d'hôte image, pas de combo.

`executionTargetForModel` refuse déjà tout id `openrouter/` et tout id qui contient `:free`. Ce document ne les rend pas appelables.

## Sources lues, sans clé

Lecture du 2026-10-02. Aucune requête authentifiée. Aucun `POST` de complétion.

OpenRouter :

- `GET /api/v1/models` — [liste](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties). L'exemple porte `Authorization: Bearer`. Le guide [Models](https://openrouter.ai/docs/guides/overview/models) publie la même liste sans clé : « freely available ». Une liste publique n'est pas un droit de compte.
- `GET /models/user` — [liste filtrée](https://openrouter.ai/docs/api/api-reference/models/list-models-filtered-by-user-provider-preferences-privacy-settings-and-guardrails) par les préférences, la confidentialité et les garde-fous de la clé. Ce n'est pas la liste publique. Ce n'est pas un droit d'envoi. Non appelé.
- [Authentication](https://openrouter.ai/docs/api/reference/authentication) : Bearer. SDK OpenAI : `baseURL` `https://openrouter.ai/api/v1`, clé côté serveur. Ne pas commiter la clé.
- [Limites](https://openrouter.ai/docs/api_reference/limits) : pour un id qui finit par `:free`, la page publie 20 requêtes/minute ; 50/jour si moins de 10 crédits achetés au total ; 1 000/jour à partir de 10 crédits. Le compteur de compte est `GET /api/v1/key`, champ `free_model_daily_requests`. Non appelé.
- `GET /generation` : `tokens_prompt`, `tokens_completion`, `total_cost`. Coût après une génération, pas un prix de catalogue. Non appelé.
- `GET /credits` : crédits achetés et consommés, clé de management. Non appelé. Ce n'est pas le budget HQ.

NaraRouter, docs [router.bynara.id/docs](https://router.bynara.id/docs) (même famille que `router.naraya.ai/docs`) :

- Base chat : `https://router.bynara.id/v1`. Clé Bearer, préfixe `sk-nry-`, variable d'environnement serveur. Jamais dans un client.
- La page modèles est « Live from `/api/plans` ». `GET /v1/models` authentifié « returns exactly the aliases your own plan entitles ».
- Quota : par classe de modèle (`base`, `Lite`, `Mocin`, `Pro`), pas un plafond unique de compte. Classe épuisée : HTTP 429 `rate_limited` pour cette classe. Plafond null : fair-use, sans plafond journalier dur. Les docs ne donnent pas le chiffre 7 000 000.
- `POST /v1/messages` est un format sur la même base. Ce n'est pas un backend Claude HQ.

Lecture publique, toujours sans clé :

- `GET https://router.bynara.id/api/plans` a renvoyé, pour le plan `code: "free"`, `token_cap_daily: 7000000` et `rpm_limit: 15`. D'autres plans publics du même objet portent d'autres plafonds (25 000 000, 60 000 000, 200 000 000). Ce sont des annonces de plan. L'objet ne détaille pas les classes `base` / `Lite` / `Mocin` / `Pro`.
- [Pricing](https://router.bynara.id/pricing) : prix publics en rupiah et en USD par 1M tokens, « Billed per token at the same rate ». Le taux affiché ce jour-là était `1 USD = 17 970 IDR`. Un modèle dont le nom contient Free peut rester payant (MiMo V2.5 Free : 246 Rp / 0,01 USD en entrée sur cette page).

## Catalogue public et accès compte

| Observation | Source permise | État HQ | Droit |
| --- | --- | --- | --- |
| `public_list` | OpenRouter `GET /api/v1/models` ; Nara `GET /api/plans` ou la page pricing | `listed` | Aucun. `listed` et `connected` n'envoient pas |
| `account_entitlement` | OpenRouter `GET /models/user` ou `GET /api/v1/key` ; Nara `GET /v1/models` authentifié | `connected` au plus, tant que le binding n'a pas `authorized` | Aucun envoi. Le binding approuvé reste obligatoire |

`accountId` est le compte serveur. Il est distinct de `openrouter` et de `nara`. Absent sur une observation de compte : l'entrée n'est pas vérifiée. Deux comptes sans `accountId` : `account_ambiguous`. Un `accountId` absent du catalogue : `account_mismatch`.

Une observation de compte exige `source` (l'URL allowlist réellement lue), `observedAt`, et `catalogRevision`. L'âge maximal reste `TARIFF_MAX_AGE_MS` (24 h). Futur ou périmé : `capability_stale`. Le fichier `config/openrouter.free-models.json` (`generated_at` 2026-06-12) est périmé au 2026-10-02. Une page « live » n'est pas une observation tant que le serveur n'a pas enregistré `observedAt`.

## Prix, capacités, quota

Chaque champ est observé ou inconnu. Inconnu n'est pas 0, pas gratuit, pas illimité.

Prix OpenRouter. Le guide Models : toutes les valeurs de `pricing` sont en USD par token, par requête ou par unité. `"0"` signifie que cette dimension est gratuite chez OpenRouter. L'exemple de la référence est `prompt: "0.00003"`, `completion: "0.00006"`, `request: "0"`. Les filtres `min_price` / `max_price` sont, eux, en USD par million de tokens. `ModelPricingDescriptor` HQ est en USD par million. Copier la chaîne par token dans `promptUsdPerMTok` diviserait le prix par un million. Cette copie est interdite. Une chaîne publique n'est pas `notToExceedCents`.

`proven_zero` seulement si prompt, completion et request sont exactement `"0"`, et si aucune surcharge (`overrides`, image, web_search, cache) n'est un nombre positif. Même alors, `billingKind` `verified_free` donne `emit: false`. `monetaryUsd` reste null.

Prix Nara. La page pricing est une liste publique. Le USD affiché est une conversion de page, pas un devis serveur en cents. Tant qu'une observation de compte n'a pas figé un devis, le prix est `unknown`. Un nom qui contient Free ne prouve pas zéro.

Capacités. `supported_parameters` contient `tools` ou `structured_outputs` seulement si la charge le dit. Sinon la capacité est inconnue. Un appel qui exige les outils et dont `tools` n'est pas `true` reste `tools_unavailable`. Les modalités d'entrée et de sortie sont copiées ou inconnues. On ne les déduit pas du nom.

Quota. Seul un champ d'une réponse authentifiée de compte peut devenir `quota.observed` (entier, unité, portée). `per_request_limits: null` est inconnu. Les constantes OpenRouter de la page Limites sont annoncées, pas lues sur le compte. `token_cap_daily: 7000000` du plan public `free` est annoncé. Il n'est pas le quota du compte HQ, pas un plafond de classe, pas `notToExceedCents`, pas le budget mémoire, pas `relativeWeight`.

`relativeWeight` (0 / 1 / 5) n'est pas stocké, pas sommé, pas converti en argent. L'unité de réserve HQ reste le centime USD entier.

## Adaptateur, base URL, secret

Allowlist serveur. Une URL fournie par le client est refusée.

| Passerelle | `baseUrl` | Catalogue public | Catalogue compte | Nom de secret |
| --- | --- | --- | --- | --- |
| `openrouter` | `https://openrouter.ai/api/v1` | `https://openrouter.ai/api/v1/models` (query permise, déjà `OPENROUTER_MODELS_API_ENDPOINT`) | `https://openrouter.ai/api/v1/models/user` ou `https://openrouter.ai/api/v1/key` | `OPENROUTER_API_KEY` (déjà dans `server-env`, optionnel) |
| `nara` | `https://router.bynara.id/v1` | `https://router.bynara.id/api/plans` | `https://router.bynara.id/v1/models` | nom à déclarer, proposé `NARA_API_KEY`. Absent du produit aujourd'hui |

Le nom suit `isValidEnvVarName` : `/^[A-Z][A-Z0-9_]*$/`, 64 caractères au plus. `sk-or-…` et `sk-nry-…` sont des valeurs, refusées. La valeur ne traverse ni le client, ni le catalogue, ni ce document.

Hors allowlist : `https://api-images.bynara.id`, `https://router.bynara.web.id`, tout hôte OpenRouter autre que `openrouter.ai`, le scraping HTML, et `refreshPolicy` autre que `cached-only` ou `manual-refresh`. Le contrat registre actuel ne fetch pas. Ce lot non plus.

Nara réutilise la forme `http-api` OpenAI-compatible déjà portée par `openrouter-http`. Pas un second id de routeur. Pas de fournisseur `nara` dans le produit aujourd'hui : le déclarer est un lot ultérieur, hors de ce document.

## Delta minimal

Fonction pure proposée, non écrite : `projectDynamicCatalog`. Elle consomme un JSON injecté et produit des `ServerCapability` plus une liste d'annonces. Elle ne réserve pas, ne fetch pas, n'écrit pas de clé.

```ts
type GatewayId = "openrouter" | "nara";
type CatalogObservationClass = "public_list" | "account_entitlement";

type GatewayAllowlist = {
  gateway: GatewayId;
  baseUrl: "https://openrouter.ai/api/v1" | "https://router.bynara.id/v1";
  apiKeyEnvVar: string; // nom seul
};

type PriceObservation =
  | { kind: "unknown" }
  | { kind: "proven_zero" }
  | {
      kind: "positive_quote";
      // devis serveur déjà en USD par token, pas une chaîne copiée telle quelle
      promptUsdPerToken: string;
      completionUsdPerToken: string;
      perRequestUsd: string;
    };

type QuotaObservation =
  | { kind: "unknown" }
  | {
      kind: "observed";
      unit: "tokens_per_day" | "requests_per_minute" | "requests_per_day";
      amount: number; // entier sûr, positif
      scope: string; // classe Nara, ou "free_variant" OpenRouter
    };

type DynamicCatalogObservation = {
  allowlist: GatewayAllowlist;
  observationClass: CatalogObservationClass;
  accountId: string | null;
  source: string;
  observedAt: string;
  catalogRevision: string;
  models: Array<{
    modelId: string;
    tools: boolean | null;
    structuredJson: boolean | null;
    inputModalities: string[] | null;
    outputModalities: string[] | null;
    price: PriceObservation;
    quota: QuotaObservation;
    announcedQuota: { amount: number; unit: string; source: string } | null;
  }>;
};
```

Règles de projection :

1. `baseUrl` ou `source` hors allowlist de la passerelle : rejet, zéro capacité.
2. `apiKeyEnvVar` invalide ou semblable à un secret : rejet.
3. `public_list` : `state: "listed"`, `tariff: null`, pas de `billingKind: "api"`. Jamais `authorized`.
4. `account_entitlement` sans `accountId`, ou avec `accountId` égal à la passerelle : entrée non vérifiée.
5. `price.kind === "unknown"` ou `"positive_quote"` : pas `verified_free`. Un devis positif n'est pas converti en `notToExceedCents` ici.
6. `quota.kind === "unknown"` reste inconnu. `announcedQuota` n'est jamais copié dans `quota`, dans le tarif, ni dans la réserve.
7. `observedAt` hors fenêtre : la capacité n'est pas vérifiée.

L'émission, si un lot ultérieur l'autorise encore, repasse par `ApprovedServerBinding` et `authorizeCallAttempt`. Sans `HQ_CALL_RESERVATION=1`, une entrée `api` stricte ne part pas. Les id `openrouter/`, `:free` et `auto/bynara` restent non appelables : `model_unsupported`, zéro fetch. `auto/bynara` est l'alias public de la page d'accueil Nara, pas le mode `auto` HQ.

## Modes

Le mode choisit un candidat dans un budget déjà approuvé. Il ne crée pas de budget, ne bascule pas vers un modèle payant, ne pose pas `paidFallback`, et n'élargit pas `resolveOrder`. `auto` HQ essaie Anthropic seul, sauf repli OpenAI déjà autorisé pour le même `workspaceId`. Une passerelle n'accorde pas ce repli.

`decideLadder` : sans modèle `enabled && recommended`, l'étage gratuit reste gratuit (`free_unavailable`). Pas de montée économie.

| Mode | Sélection | Refus |
| --- | --- | --- |
| `manual` | `modelId` égal au binding approuvé | Autre modèle, compte, révision, workspace ou `billingKind` : `binding_mismatch` (compte absent du catalogue : `account_mismatch`) avant réserve et avant fetch |
| `recommended` | Premier id `enabled && recommended` dont le prix n'est pas positif et dont `billingKind` n'est pas `api` | Prix positif ou seul candidat `api` : `paid_switch_refused`. Aucun candidat : `free_unavailable`. Le candidat n'est pas un envoi |
| `auto` | Aucun id de passerelle. `resolveOrder` inchangé | Un candidat à prix positif ou `billingKind: "api"` : `paid_switch_refused`. Statut sans montée : `no_gateway_climb` |

`paid_switch_refused` et `no_gateway_climb` sont les statuts de ce sélecteur. Ils n'existent pas encore dans le produit. `openrouter/free` reste un tirage aléatoire OpenRouter parmi les modèles compatibles, pas « le meilleur », et pas un client. `response.model` serait l'id exécuté, seulement après une vraie réponse. Ce lot n'en produit pas.

## Tests requis

Fixtures JSON injectées. Zéro réseau, zéro clé, zéro installation. Non écrits par ce document.

Déjà présents, à ne pas rejouer comme une qualification de Claude :

- `model-provider-contract.test.mjs` : `OPENROUTER_API_KEY` accepté ; une valeur `sk-…` refusée ; un endpoint autre que `https://openrouter.ai/api/v1/models` refusé ; `costTier: "free"` sans trois zéros refusé.
- `execution-models.ts` : `openrouter/` et `:free` refusés, zéro fetch.
- Catalogue serveur : `listed` ne donne aucun droit ; binding divergent, zéro réserve, zéro fetch ; abonnement callable, `accessClass` `subscription`, `monetaryUsd` null.

À écrire avec le lot qui ajoutera `projectDynamicCatalog` :

1. `baseUrl` client, hôte image Nara, ou `router.bynara.web.id` : rejet, zéro capacité.
2. `apiKeyEnvVar` `sk-nry-xxxxxxxx` : rejet. `NARA_API_KEY` : nom accepté, valeur absente du résultat.
3. Fixture liste OpenRouter publique : `state` `listed`, assess `public_catalog_only`, 0 réserve, 0 fetch.
4. Fixture `GET /v1/models` Nara sans `accountId` : non autorisé. Deux comptes, même modèle : `account_ambiguous`.
5. `accountId` égal à `openrouter` ou `nara` : entrée non vérifiée.
6. `observedAt` de plus de 24 h, ou futur : `capability_stale`.
7. Chaîne `prompt: "0.00003"` : ni `promptUsdPerMTok`, ni `notToExceedCents`. Prix inconnu : pas gratuit, `monetaryUsd` null.
8. `"0"` sur prompt, completion et request : `proven_zero` possible, `emit` faux, `executedModelId` null, `monetaryUsd` null.
9. `token_cap_daily: 7000000` dans une fixture `/api/plans` : `announcedQuota` seulement. Le placer dans `quota.observed` ou dans `notToExceedCents` fait échouer le test.
10. `per_request_limits: null` : quota inconnu.
11. `recommended` et `auto` devant un prix positif ou `billingKind: "api"` : `paid_switch_refused`, `paidFallback` non posé, `resolveOrder` inchangé.
12. `manual` avec un autre `modelId` : `binding_mismatch`, 0 fetch, 0 réserve.
13. `openrouter/free`, un id `:free`, et `auto/bynara` : `model_unsupported`, 0 fetch.
14. Le test n'ouvre aucun socket et n'appelle pas `fetch`.

## Limites

Pas de facture, pas d'appel fournisseur, pas de découverte exécutée dans `src/server/ai` par ce document.
Le délai de corps et `emitted_unknown` sont inchangés. La facturation n'est pas réécrite.
Le chemin legacy sans catalogue reste compatible. Ce n'est pas une preuve de sécurité.
Aucun client JSON pour `openrouter/free`.
Claude ferme le lancement. Antigravity : compatibilité ACP.
Ce cloud n'a pas vu le localhost Windows.
