# Objectif autonome : terminer proprement une mission interrompue

## Résultat attendu

Faire passer le parcours HQ/OpenHands de « interruption détectée, intervention nécessaire » à un parcours opérateur réellement utilisable : comprendre l'état, récupérer un résultat déjà produit ou clôturer explicitement un lancement interrompu, sans nouvelle exécution involontaire et sans perdre le travail. Le résultat doit être observable et durable dans HQ. Une exécution terminée ne vaut jamais validation indépendante.

## Point de départ vérifié

Codex a confirmé 142 tests Linux sans exclusion et rejoué la qualification de réponse perdue après exécution. Les corrections de la revue sont présentes. Les qualifications restent synthétiques ; aucune mission modèle réelle n'est prouvée. Le prochain manque est la réconciliation effective, pas davantage de tests répétant le refus de relancer.

## Autonomie sur les moyens

Inspecter les contrats actuels et décider de l'implémentation minimale cohérente. Réutiliser les mécanismes existants avant d'ajouter une abstraction. Choisir et ajuster les étapes selon les découvertes, implémenter, tester et corriger jusqu'au résultat vérifiable. Ne pas s'arrêter à un plan ou à une liste de recommandations. Si /goal existe réellement dans cette installation, l'utiliser pour cet objectif ; sinon garder cet objectif explicite sans prétendre avoir activé une fonctionnalité absente.

Le dépôt Orchestrator est le périmètre principal. Des modifications ciblées de contrats et tests dans C:/Users/micha/Dev/Oria.HQ sont permises uniquement si nécessaires à la persistance du résultat. Préserver toutes les modifications existantes. Ne pas ajouter d'autre orchestrateur, de chantier visuel ni de nouvelle dépendance sans nécessité démontrée.

## Preuves de réussite

- Résultat déjà terminé : relire les preuves retenues et produire un état exploitable sans exécuter à nouveau.
- Interruption au démarrage : distinguer un conteneur créé, en cours et arrêté ; aucune relance aveugle. Une opération explicite et liée à l'état observé permet de clôturer ou de récupérer ce qui est récupérable.
- Requête répétée et concurrence pertinente : pas de second effet ; identités exactes et état durable vérifiés. Refuser une preuve obsolète ou appartenant à un autre lancement/projet.
- État réellement incertain : motif compréhensible et prochaine action précise, sans succès inventé. Préserver les fichiers de travail et preuves ; tout nettoyage est limité aux ressources attribuées à la qualification.
- Rejouer le parcours réel de qualification Linux avec Docker et base jetables, puis le redémarrage de la base. Ajouter les tests correspondant aux risques nouveaux, pas au volume de lignes.

## Limites maintenues

SSH de qualification existant autorisé ; nouveau dossier isolé sous /opt/oria-openhands-qualification. Aucun service actif, base opérationnelle, compte ou credential modifié. Aucun appel modèle supplémentaire, octroi OAuth, port public, publication Git ou déploiement de production. Aucun effacement du travail utilisateur. Un blocage d'authentification fournisseur n'empêche pas cette qualification synthétique. Ne pas créer d'autres agents.

## Mémoire et livraison

AgentMemory-Hub est confirmé connecté par l'utilisateur. Lire le contexte partagé et consigner uniquement les faits durables de développement avec preuves et limites. Le serveur a été aligné avec celui de Codex en read_write ; aucune donnée de production ni secret en mémoire. En cas d'échec MCP, décrire l'erreur exacte sans interrompre les tâches indépendantes.

Livrer docs/CLAUDE-RECONCILIATION-RESULTAT.md : comportement avant/après, décisions, fichiers, validations effectivement exécutées, ressources nettoyées, limites et chemin restant vers une mission réelle. Codex fait la revue indépendante. Ne pas revendiquer zéro bogue ou une mission autonome réelle sur la base d'un agent simulé.
