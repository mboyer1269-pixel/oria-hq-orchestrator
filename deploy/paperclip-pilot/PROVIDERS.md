# Connexion fournisseur du pilote

Le propriétaire Paperclip a été créé par l'utilisateur ; les inscriptions sont refermées.

La connexion Claude Code a été effectuée dans un conteneur temporaire officiel, utilisateur node, racine readonly, ressources bornées, sans ports. Seul le sous-répertoire d'identifiants de cette connexion était monté. Le conteneur a terminé avec succès et a été supprimé automatiquement. Aucun code OAuth ni token ne doit être conservé dans les rapports.

Paperclip valide ensuite le token par une requête de quotas Anthropic ; le réseau exclusivement interne bloquait cette étape. L'overlay `compose.providers.json` ajoute au seul service paperclip un réseau dédié avec sortie Internet. La base conserve seulement son réseau interne. Aucun port n'est publié. Cette sortie n'est PAS une liste blanche de domaines : le durcissement par proxy et l'isolation des futurs workers restent à réaliser avant de confier des tâches non fiables.

Configuration active : `docker compose -f compose.json -f compose.providers.json --env-file .env up -d`. Une commande utilisant seulement le fichier de base revient au mode sans sortie fournisseur. Ne pas réexécuter `onboard --yes` pour réparer une connexion sur cette instance existante.

Les clés de connexion persistent dans le volume privé de Paperclip ; inclure ce volume et la configuration privée dans la sauvegarde protégée. Ni identifiants ni mémoire runtime dans AgentMemory local.
