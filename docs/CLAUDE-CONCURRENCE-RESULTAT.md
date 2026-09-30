# Reprise Codex : coordination lancement / réconciliation

Travail repris après interruption de Claude, 30 septembre 2026. Aucune publication ni installation dans les services actifs.

## Implémentation finalisée

Le verrou Linux interprocessus commencé par Claude est partagé par permission_worker et reconcile_launch dans le répertoire de contrôle du lancement. Il est acquis avant toute décision et conservé pendant le dispatch/supervision ou toute la réconciliation. Un concurrent reçoit launch_busy sans effet. Après libération, le worker relit le claim : un lancement cancelled ne peut pas être réexécuté. Le fichier de verrou reste en place, le noyau libère le verrou à la mort du processus. Contrôles de chemin réel, propriétaire, permissions, fichier régulier et absence de liens multiples ajoutés. launch_lease.py est inclus dans le paquet hôte.

Un verrou n'annule PAS une requête déjà reçue par Docker quand le client meurt. Codex a donc interdit la clôture fondée uniquement sur l'absence du conteneur depuis creation_requested, start_requested ou running. Ces cas renvoient docker_effect_unresolved, sans transition ni nettoyage. Une réobservation après écriture ne sert plus de prétendue garantie. Le résultat terminé d'un conteneur identifié reste récupérable ; un container_created dont la création a été enregistrée reste clôturable avant démarrage sous verrou.

## Vérifications exécutées

- Suite hôte Linux : 165 tests, zéro exclusion, zéro échec.
- Tests de coordination : vrai flock, deux processus avec barrière, exclusion avant observation Docker, second détenteur refusé, libération après kill, refus de clôturer une absence ambiguë, worker concurrent refusé, ancien exécutant refusé après clôture.
- Qualification connectée --interrupted-run --reconcile : consommateur tué pendant exécution, résultat récupéré avec exitCode 0, identité inchangée, aucune seconde exécution, répétition sans nouvel effet, passerelle libérée, état conservé après redémarrage PostgreSQL. Agent synthétique ; independentValidationPassed reste false.
- Qualification nominale --operator-provider : réussie, processus de qualification terminé en code 0, persistance vérifiée après redémarrage de la base.
- git diff --check passe.

Racine isolée : /opt/oria-openhands-qualification/concurrency-codex-20260930. Logs codex-tests.log, codex-connected.log, codex-nominal.log. Le code partagé HQ n'a pas été modifié par cette reprise.

## Limites exactes

Coordination entre chemins coopératifs sur un seul hôte, pas verrou distribué ni protection contre un administrateur pilotant Docker directement. Les requêtes Docker orphelines ambiguës exigent une résolution opérateur : aucune procédure automatique pour les déclarer terminées n'est fournie. Les tests ne prouvent pas tous les entrelacements internes du daemon, ni une panne noyau ou réseau. Le défaut de fausse clôture sur simple absence est empêché par refus explicite ; cela ne constitue pas une récupération automatique universelle.

Aucun compte fournisseur, appel modèle ou mission de coding réelle exécuté. La connexion fournisseur et la première mission réelle avec revue indépendante restent à qualifier. Ne pas présenter ces résultats comme une application complète ou une garantie zéro bogue.
