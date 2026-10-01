# UI modèles V2 — matrice sur le routeur existant

Aucun produit, routeur ou écran n'est modifié. Aucun clic n'a été vérifié. Les lignes « exemple UI » ne sont pas des appels. Badge connecté interdit tant qu'une session réelle n'est pas prouvée. `relativeWeight` 0/1/5 n'est pas un dollar. Réglages d'usage inchangés.

Politique : téléphone d'abord. Deux espaces, Discuter et Atelier. Hermes orchestre ; HQ autorise. Ordre affiché : gratuit compatible, puis abonnement réellement connecté, puis API payante seulement avec accord explicite. Jamais de repli payant silencieux. Un changement de modèle vaut pour la prochaine demande, pas pour le run déjà parti. Mission fermée par défaut ; ouvrir/fermer retrouve fil, scroll et brouillon. Artefacts : plan, aperçu, diff, tests.

Sources lues, sans clé ni appel : OpenRouter `openrouter/free` choisit au hasard parmi les modèles gratuits compatibles avec la demande (outils, image, sortie structurée) ; le modèle utilisé est `response.model` ; ce n'est pas « le meilleur ». Hermes : au moins un fournisseur ; `hermes model` change fournisseur et modèle ; OpenRouter par clé ou OAuth ; Codex par OAuth ChatGPT. Cela ne prouve pas qu'ils sont connectés ici.

## Champs existants

| Vision | Code actuel | État prouvable sans réseau |
| --- | --- | --- |
| Modèle demandé | `chooseModel` → `chosenModelId` ; `executedModelId` toujours `null` | Sélection seulement |
| Modèle utilisé | `generateStructuredJson` → `executedModelId` après réponse client | Absent tant qu'aucun appel |
| Gratuit | `config/openrouter.free-models.json` ; `eligibleFreeModels` = `enabled && recommended` | 26 lignes, 0 éligible, `generated_at` 2026-06-12 |
| Appel réel | `executionTargetForModel` : seulement `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`, `gpt-4o`, `gpt-4o-mini` | `openrouter/`, `:free`, `gemini-flash`, abonnement, local → `callable: false` |
| Accord payant | `paidFallback.authorized === true` et même `workspaceId` | Sinon `auto` reste Anthropic seul |
| Quota | `decideLadder.currentSpend` / budget mémoire | Pas un quota OpenRouter |
| Accès | `accessClassForModel` | `api` si callable ; sinon le mot `subscription` ou `local` dans l'id ; sinon `unknown` |

## Cas prioritaires

Chaque ligne se vérifie en appelant la fonction nommée, sans fetch. L'exemple UI affiche l'état ; il n'envoie rien.

| Cas | Appel existant | État attendu aujourd'hui | Écart minimal V2 |
| --- | --- | --- | --- |
| Gratuit sans outils, mission | `executionTargetForModel` sur un id `:free` ou `openrouter/free` | `refused`, aucun fetch. Le catalogue ne connaît pas les outils | Montrer « non appelé ». Ne pas badger connecté. Le filtre outils est celui d'OpenRouter, pas de HQ |
| Quota épuisé ou inconnu | `decideLadder` avec `currentSpend >= dailyBudget` | Peut viser `free`, puis économie si aucun gratuit. Aucun 429 observé | Afficher `inconnu` tant qu'aucune réponse fournisseur ne dit épuisé |
| Catalogue périmé | `parseFreeModelCatalogText` du fichier du 2026-06-12 | 0 éligible | Étiquette « catalogue périmé », pas une liste live |
| Aucun compatible | `decideLadder` si `selectFreeModel` est vide | `rung` économie, raison « repli économie » | V2 doit rester « aucun compatible » et refuser. Ne pas monter en payant |
| Abonnement déconnecté | `accessClassForModel` | Une sous-chaîne, pas une session Codex/Hermes | Pas de badge. Claude prouve la capacité ; cet écran ne l'affirme pas |
| API payante demandée / refus | `resolveOrder` sans `paidFallback` conforme | Un seul fournisseur, pas de second payant | L'accord est ce champ serveur. Un interrupteur d'exemple ne l'arme pas |
| Demandé vs utilisé | `chooseModel` puis, plus tard seulement, `generateStructuredJson` | Demandé ≠ utilisé. Utilisé reste nul ici | Deux libellés. « Utilisé » vide tant que `executedModelId` est nul |
| Changement pendant un run | aucun champ HQ | Rien n'est appliqué en cours de run | La prochaine demande prend le nouveau choix. Le run parti garde le sien |
| Reprise après réseau | réservation `emitted_unknown` / réconciliation, déjà qualifiée | Pas un changement de modèle | Retrouver brouillon et fil. Ne pas relancer un payant |
| Artefact, retour, 360×800 et 390×844, clavier, focus | aucun écran | Non vérifié | Atelier : plan / aperçu / diff / tests. Mission fermée. Ouvrir/fermer restaure fil, scroll, brouillon. Clics à demander quand le commit UI existera |

## Contradictions

Le commentaire du catalogue et de `seed.ts` présente OpenRouter comme repli. `executionTargetForModel` refuse tout id `openrouter/` et `:free`. `decideLadder`, sans modèle `enabled && recommended`, devient économie : c'est un repli payant de politique, interdit par cette vision. `selectFreeModel` trie par contexte puis id ; OpenRouter `openrouter/free` tire au hasard parmi les compatibles. Le JSON a `router_fallback: openrouter/free` : ce n'est pas un client. `gpt-4o-mini` est décrit comme fallback ; `auto` ne l'atteint pas sans accord. Le poids relatif et le budget mémoire ne sont ni un quota ni une connexion. Hermes et Codex listés sur la page fournisseurs ne sont pas des sessions HQ.

Écarts à ne pas coder ici : pas de nouveau routeur ; l'UI lit ces états ; séparer exemple et appel ; catalogue vide ou périmé = aucun compatible ; payant visible seulement après accord explicite, défaut fermé.
