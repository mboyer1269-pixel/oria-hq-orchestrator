# Grille V2 mobile — contrôles réutilisables

Réutilise `UI-MODELES-V2.md`. Aucun fichier d'Antigravity ou de Claude, aucun backend, aucune UI. La preview `http://127.0.0.1:3350/hq/hermes-cockpit` est injoignable depuis ce cloud (connexion refusée). Ses clics ne sont pas faits. Aucun coût ni latence de modèle : aucun appel.

Commande, produit inchangé sous `HQ_PRODUCT_ROOT` (défaut `/tmp/hq-hermes`) :

`node --test --test-concurrency=1 handoffs/cursor-hermes-acceptance/v2-mobile-contracts.test.mjs`

Ici : 6 tests, 0 échec, 625 ms, exit 0. `fetch` n'a pas été appelé.

| Scénario | État initial | Action | Résultat observable | Preuve | Contrat |
| --- | --- | --- | --- | --- | --- |
| Discuter par défaut | écran non chargé ici | ouvrir le cockpit | non observé | — | aucun écran dans cet arbre |
| Mission fermé | idem | lire le panneau | non observé | — | idem |
| Brouillon, scroll, projet, artefact, Atelier | idem | aller-retour | non observé. Aucun champ HQ pour le scroll | — | la continuité d'id est seulement celle de la mission |
| Demandé ≠ exécuté | message `bonjour` | `chooseModel` | `chosenModelId` `gpt-4o-mini`, `executedModelId` null, `monetaryUsd` null | test 1 | `model-router.ts` |
| Quota inconnu | catalogue libre vide, dépense locale 0 | `decideLadder` tâche `draft` | pas de quota fournisseur. Écart bloquant : le palier devient `economy` (« aucun modèle free éligible »). Ne pas l'afficher comme quota épuisé ni comme envoi payant autorisé | test 4 | `cost-ladder.ts` |
| Modèle incompatible | id `openrouter/free` ou `:free` | `generateStructuredJson` | `model_unsupported`, `executedModelId` null, 0 tentative, aucun réseau | test 2 | `execution-models.ts` |
| Pas de repli payant non autorisé | `auto`, sans accord ou avec un autre workspace | `generateStructuredJson`, clés absentes | une tentative `anthropic` seulement. Avec accord du même workspace : `anthropic` puis `openai`, toujours sans socket | test 3 | `paidFallback` dans `llm-json-provider.ts` |
| Reconnexion, une mission | même `requestId`, écriture puis erreur | `create` puis `lookup` puis `create` | `outcome_unknown`, puis le même id, une ligne, `executionRequested` false | test 5 | `development-mission.ts` |

## Prérequis pour le commit UI, non exécutés ici

Commit UI d'Antigravity identifié, servi sur le poste de Michael à `http://127.0.0.1:3350/hq/hermes-cockpit`. Pas le port 3337 ni un ancien hash. Deux largeurs : 360×800 et 390×844, plus clavier et focus.

À constater, sans les inventer : l'ouverture est Discuter ; Mission est fermé ; un brouillon, le scroll et le projet survivent à un artefact puis à Atelier et au retour ; une seule mission ; le modèle demandé et le modèle exécuté sont deux libellés, le second vide tant qu'il n'y a pas d'appel ; le quota sans réponse fournisseur reste inconnu ; un id incompatible est refusé sans bascule payante ; aucun badge connecté. Les contrôles ci-dessus restent la partie modèle et mission.
