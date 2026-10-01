# Écart de routage et de coûts

Lecture seule du dépôt produit `Oria.HQ.Michael.HQ-APP`, commit `e9ff840` (`codex/hq-mission-dossier`). Les fichiers `model-router.ts`, `cost-ladder.ts`, `model-config.ts` et `llm-json-provider.ts` sont identiques sur `main` (`6efb47b`). Ce n'est pas une fonctionnalité livrée et cela ne bloque pas une mission réelle. Aucun appel modèle, aucune modification du produit.

## Écart

Le budget interne n'est pas un coût durable. `cost-ladder.ts` compte des poids `0 / 1 / 5` (`RUNG_COST_WEIGHT`) dans une `Map` par agent et jour UTC, plafond `100`. `getCostLadderSnapshot` porte la base `estimated/in-memory only`. Le registre produit marque `cost_ladder` en `display_only`.

L'appel qui peut facturer est ailleurs. `generateJorisReply` appelle `generateStructuredJson` sans le `modelId` choisi par `chooseModel`. Le client Anthropic défaut est `claude-haiku-4-5-20251001` ; s'il échoue, OpenAI `gpt-4o-mini` est essayé. `tokenUsage` n'est pas écrit dans le store. Quand l'appel réussit, `brain.ts` affiche ce modèle et force `costMode: "economy"`. Quand il échoue, la réponse déterministe affiche quand même le modèle routé, souvent `claude-sonnet-4-6`.

Le poids mémoire et la facture API ne se comparent donc pas. Il n'y a pas de table de prix dans le routeur.

## Catalogue

| Voie | Dans le routeur lu | Facturation |
|---|---|---|
| Abonnement Claude, Codex, Cursor, Antigravity | Aucun profil. Le plan orchestrateur rappelle déjà qu'un support de modèle n'est pas un quota d'abonnement. | Non branché. Ne pas le compter. |
| API | `claude-sonnet-4-6` (anthropic), `gpt-4o-mini` et `gpt-4o` (openai), `gemini-flash` (google), deux profils `openrouter/…`, plus le catalogue `config/openrouter.free-models.json` (`enabled` et `recommended`). | Clé API. Le gratuit OpenRouter n'est pas un abonnement. |
| Local | Aucun identifiant dans `modelProfiles` ni dans l'échelle. | Absent. |

## Règle : aucun repli payant silencieux

Trois chemins actuels la violent ou la rendent invisible.

- `pickAvailableModelId` : économie indisponible enchaîne `gemini-flash` puis `claude-sonnet-4-6`. Si toute la chaîne est indisponible, le retour reste `gpt-4o-mini`.
- `applyCostLadder` : un modèle gratuit présent dans `unavailableModelIds` devient l'étage économie, mais la raison peut encore dire « zéro coût ».
- `generateStructuredJson` en `auto` appelle OpenAI si Anthropic échoue. `fallbackUsed` existe sur le résultat provider, pas sur la réponse Joris.

Le plancher `client_audit` vers premium est explicite. Ce n'est pas le repli silencieux. Il reste un choix d'affichage tant que l'appel live ne reçoit pas ce `modelId`.

## Fichiers et appelants

- `src/server/ai/model-router.ts` — `chooseModel`. Appelé par `src/server/joris/brain.ts` (deux fois par commande) et `src/server/missions/mission-draft-control.ts` (`buildRoute`).
- `src/server/ai/cost-ladder.ts` — politique pure et store mémoire. Lu par le routeur, `src/app/hq/runtime/page.tsx` (`getCostLadderSnapshot`) et le doctor.
- `src/server/ai/model-config.ts` — identifiants et chaîne de repli.
- `src/server/ai/llm-json-provider.ts` — Anthropic puis OpenAI. Appelé par `joris-reply-generator.ts`, `daily-direction-generator.ts`, `llm-cash-action-packet-generator.ts`, `venture-score-shadow-runner.ts`.
- `src/features/hq/seed.ts` — catalogue de profils. `src/features/hq/capability-status.ts` — statut `display_only`.

## Cinq changements proposés, non faits

1. Ne débiter `BudgetStore.add` que pour un appel qui a renvoyé `tokenUsage`. Garder les poids `0/1/5` hors de toute somme présentée comme une dépense.
2. `pickAvailableModelId` ne monte pas d'étage payant. S'il ne reste qu'un modèle indisponible, le choix échoue au lieu de renvoyer `gpt-4o-mini`.
3. Si le modèle gratuit est indisponible, la raison ne dit plus « zéro coût » et aucun modèle payant n'est substitué sans un drapeau explicite, absent par défaut.
4. `generateStructuredJson` en `auto` n'enchaîne pas le second fournisseur payant sans ce même drapeau. `fallbackUsed` reste vrai seulement dans ce cas autorisé.
5. Une réponse `generation: "fallback"` ne publie pas `claude-sonnet-4-6`. Elle publie l'absence d'appel.

## Tests de recette, à écrire dans le produit

- Économie indisponible : le choix n'est ni `gpt-4o` ni `claude-sonnet-4-6`, et ce n'est pas non plus `gpt-4o-mini` marqué indisponible.
- Catalogue gratuit vide ou modèle gratuit indisponible : pas de raison « zéro coût », pas de modèle OpenAI ou Anthropic à la place.
- Anthropic en échec, drapeau absent : OpenAI n'est pas appelé.
- Aucun `tokenUsage` : le spend mémoire du jour ne change pas.
- Réponse déterministe : `modelId` n'est pas le modèle premium routé.

Les tests existants `model-router.test.mjs` attendent encore le repli vers `gpt-4o` et le passage gratuit vers économie. Les changer fait partie du changement 2 et 3, pas de ce lot.
