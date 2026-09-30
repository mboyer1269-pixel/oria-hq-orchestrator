# Critères d'acceptation du pont

30 septembre 2026. Revue des critères seulement. Aucun code de pont, aucune installation, aucun test rejoué.

## Limite

Le commit `be61d26` n'est pas un objet de ce clone (`git cat-file` : objet inconnu). Ce dépôt ne contient pas le dernier code annoncé. Cette note ne le relit pas et ne le déclare ni accepté ni refusé au vu du source.

Entrée reçue, non revérifiée ici : le banc appelé « real disposable DB » utilise `http.createServer` et une `Map`. Codex le classe comme simulation, pas comme PostgreSQL. La correction vers un PostgreSQL/PostgREST jetable est annoncée, pas livrée dans cet arbre.

`integrations/openhands-runner/HQ-POSTGREST-RESULTS.md` décrit un autre parcours, déjà clos. Ces sorties ne cocheraient aucun critère du pont absent. `docs/REVUE-CLAUDE-PREUVE-OPERATEUR.md` rappelle qu'un consommateur tué à la création du conteneur n'est pas une perte de réponse après exécution terminée.

Un serveur HTTP dans le processus et une `Map` échouent à tous les critères de durabilité ci-dessous, même si les codes de sortie sont zéro.

## Preuve exigée pour cocher

Chaque case exige, dans le rapport du correctif, les quatre éléments suivants. Une case sans l'un d'eux reste ouverte.

- Versions : résultat de `SELECT version()`, version de PostgREST, identifiants d'image par digest.
- Migrations : noms des fichiers appliqués. Si l'historique de production n'est pas complet, l'écrire.
- Contraintes SQL : nom et définition lus dans le catalogue (`pg_constraint` ou équivalent), pas seulement le code du test.
- Sorties : commande, code de sortie, compte de lignes, et la limite de ce qui n'a pas tourné.

L'unicité doit être une contrainte SQL. Un lookup puis un insert dans l'application ne suffit pas sous concurrence.

## Checklist

- [ ] **Même requête, deux fois en parallèle.** Deux créations se chevauchent, même identité, même payload. Une seule ligne reste. Les deux appelants observent cette ligne. Aucune seconde exécution ne démarre.
- [ ] **Même identité, payload divergent.** Le second payload est refusé. La ligne conservée reste le premier payload. Pas d'écrasement, pas de fusion silencieuse, pas de succès qui rangerait le second contenu sous le premier identifiant.
- [ ] **Réponse perdue après commit.** La ligne est commitée, puis seule la réponse au client disparaît. La reprise relit cette ligne et ne crée rien. Échec de la case si le test tue le processus avant le commit, ou s'il tue le consommateur dès la création du conteneur.
- [ ] **Redémarrage de la base.** PostgreSQL est arrêté puis relancé. Un nouveau processus client relit la même ligne et le même hash de payload. Le redémarrage ne crée pas un second enregistrement et ne lance pas l'exécution.
- [ ] **Identité et workspace protégés.** L'espace et l'acteur écrits viennent du contexte serveur déjà authentifié, pas du corps de la requête. Un corps qui nomme un autre espace est ignoré ou refusé. Une lecture dans un espace étranger ne renvoie pas la ligne.
- [ ] **Admission, autorisation, exécution.** Trois états observables restent distincts. Une admission commitée n'est pas une autorisation. Une autorisation n'est pas une exécution. Une admission sans exécution reste non exécutée après la reprise. `prepare_job.py` laisse `durableLaunchReserved` et `budgetsEnforced` à false : ce drapeau du runner n'est pas cette preuve.

## Échec immédiat

- Présenter `http.createServer` ou une `Map` comme base réelle.
- Cocher une case avec une sortie d'un parcours antérieur.
- Appeler qualifié un SDK, ou un agent synthétique, mission réelle validée.
- Prétendre que cette note a relu `be61d26`.
