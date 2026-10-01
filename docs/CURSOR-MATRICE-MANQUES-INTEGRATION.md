# Matrice des manques — Discuter, admission, autorisation, OpenHands

1er octobre 2026. Qualification indépendante en lecture. Aucune preuve n'a été fabriquée. Aucun rapport JSON n'est traité comme une chaîne validée. Le validateur de `integrations/qualification-evidence/` ne fait pas partie de cette chaîne : il juge la forme d'un rapport, pas l'exécution.

Le commit `be61d26` n'est pas un objet de ce clone. Le backend, le harness et l'assemblage isolé restent à Antigravity. Aucun fichier sous `integrations/antigravity/` n'a été modifié.

## Matrice

| Étape | Présent dans ce dépôt | Manque pour une mission essayable | Propriétaire |
|---|---|---|---|
| Discuter, Hermes | Direction fixée. Inventaire VPS du 29 septembre : service nommé Hermes 0.15.2, Node 20.19.2, Claude non connecté. `integrations/` ne contient pas d'adaptateur Hermes. | Identité du binaire 0.15.2. Preuve qu'il est, ou n'est pas, Nous `hermes-agent`. Session serveur plutôt qu'historique complet. Aucun appel modèle n'est autorisé ici. | Hors de ce lot. Pas un second adaptateur à coder. |
| Admission HQ | Schéma `admission-report` version 2 et contrôleur hors ligne. Critères dans `docs/CURSOR-CRITERES-ACCEPTATION-PONT.md`. `prepare_job.py` écrit `durableLaunchReserved=false`. | Rapport collecté sur PostgreSQL/PostgREST jetable, pas une `Map`. Contrainte SQL observée, comptes avant/après redémarrage, perte de réponse après commit. L'artefact `be61d26` est absent. | Antigravity pour le harness. Ce dépôt ne reçoit le rapport qu'après coup. |
| Autorisation | Le schéma distingue admission, autorisation et exécution. `operator_status.py` laisse `independentValidationPassed` à false. | Contexte protégé réellement lu, pas un champ du corps. Décision durable distincte de l'admission. Le bridge SDK qualifié choisit encore une option tout seul (`docs/OPENHANDS-QUALIFICATION-2026-09-30.md`). | HQ pour l'autorité. OpenHands runner pour la consommation. |
| OpenHands | Runner et qualification SDK 1.50.0, exercices synthétiques, sans modèle. | Version relue dans le conteneur. Exécution d'un dossier autorisé, pas d'un agent synthétique. Pas d'installation de 1.50.1 dans ce lot. | Runner déjà dans `integrations/openhands-runner`. Pas le harness Antigravity. |
| Résultat et tests | Sorties synthétiques et `independentValidationPassed=false` dans les rapports du runner. | Diff utile, tests de la mission, revue indépendante. Un `reviewable` du validateur ne compte pas. | Après une exécution réelle autorisée. Interdit tant qu'aucun appel modèle n'est permis. |

## Conséquence

La première mission réelle n'est pas essayable depuis ce clone. Le jalon utilisable livré ici est le contrôleur version 2, qui empêche un rapport aux assertions échouées de rester `reviewable`. Il ne remplace pas le parcours.

## Dépendances précises

1. Rapport d'admission version 2 collecté par le harness Antigravity sur un vrai PostgreSQL/PostgREST jetable. Sans ce fichier, le contrôleur n'a rien de réel à lire.
2. Identité du service Hermes 0.15.2. Sans elle, Discuter ne se branche pas.
3. Contrat figé des créations concurrentes, toujours absent de `integrations/`.
4. Autorisation explicite avant tout appel modèle. Elle n'est pas donnée.

## Limite résiduelle du contrôleur

Même en version 2, `expected` égal à `observed` dans un JSON ne prouve pas que la commande a tourné. Une chaîne vide égale à une chaîne vide passerait la comparaison de type. Ce n'est pas une authentification. Le verdict `reviewable` reste une lecture humaine, sortie 4, jamais prêt pour la production.
