# Résultats réels — 30 septembre 2026

SDK 1.50.0 installé depuis PyPI dans une image dédiée. Image Python officielle épinglée par digest dans `deploy/openhands-qualification/Dockerfile`; dépendances résolues enregistrées dans `packages-observed.txt` (inventaire observé, pas lock cryptographique).

Les trois scripts décrits ci-dessous ont terminé avec code 0 sur le VPS, sous UID10001, réseau désactivé, racine en lecture seule, capacités retirées, aucun secret et aucun montage applicatif. Le répertoire du banc est monté en lecture seule; seul un espace temporaire borné est inscriptible.

## Permissions

Le vrai `_OpenHandsACPBridge` choisit l'option allow-once d'une demande synthétique. L'override expérimental retourne cancelled pour tous les titres testés et une liste d'options vide. Cet override n'est PAS raccordé à ACPAgent : aucune protection de production n'est revendiquée.

## Conversation

Le vrai SDK Conversation initialise le pair ACP synthétique, crée une session, envoie le message et reçoit le marqueur attendu. Quatre événements observés. Aucun appel de modèle, aucune connexion Claude testée. Ce premier scénario ne qualifie pas la persistance; l'extension ci-dessous la vérifie après fermeture normale. L'arrêt brutal et la reprise après panne restent non qualifiés.

## Constats utiles

- LiteLLM tente au démarrage de lire sa table de coûts distante, échoue avec réseau désactivé puis utilise sa copie locale. Aucun accès réseau n'a été autorisé pour faire passer le test.
- Le SDK avertit qu'en l'absence de persistence_dir les événements restent en mémoire. La prochaine qualification devra fournir un magasin explicite pour éprouver la reprise.
- Le pair ne produit pas de rapport d'usage : le SDK attend brièvement puis avertit. Des compteurs zéro dans ce scénario synthétique ne permettent pas de prévoir le coût d'une vraie mission.

## Extension : permissions en conversation et persistance

`qualify_permissions_conversation.py` termine avec code 0 dans le même confinement. Deux processus indépendants exécutent un vrai échange ACP de demande de permission : le bridge upstream renvoie allowed, le remplacement expérimental renvoie cancelled et le pair confirme denied. Dans les deux cas, quatre événements sont retrouvés après fermeture et rechargement du stockage explicite de Conversation.

Le remplacement du symbole privé est limité au processus de test et restauré en finally. Il ne constitue pas un point d'extension de production, ni un mécanisme sûr pour plusieurs conversations concurrentes. Aucun outil réel n'a exécuté une action. La relecture des événements ne prouve pas la reprise d'une session fournisseur ni la récupération après arrêt brutal.

Le lanceur `deploy/openhands-qualification/run.sh` borne les essais SDK à 90 secondes et retire le conteneur exact créé. Le test conversation initial a été rejoué avec ce lanceur; l'absence de conteneurs portant son label a été vérifiée après exécution normale.

Le chemin timeout a ensuite été provoqué sur le VPS avec `qualify_timeout.py`, limité explicitement à 3 secondes. Ce processus ignore SIGTERM et attend 120 secondes. Le marqueur de démarrage a été reçu, le lanceur est sorti avec le code attendu 124, et la recherche Docker des conteneurs de qualification est revenue vide. Cela vérifie le nettoyage d'un processus récalcitrant dans ce conteneur; cela ne démontre ni l'annulation ACP, ni la conservation du travail après interruption d'un fournisseur.

Prochaine étape : point d'extension de permissions maintenable et qualification d'arrêt/reprise; connecter officiellement un fournisseur seulement après qualification des frontières. Les services actifs n'ont pas été modifiés.

## Annulation ACP synthétique
qualify_cancellation.py exécuté sur le VPS : code 0. Le pair reçoit session/cancel et répond cancelled, la tâche se termine avec statut paused, puis le processus pair sort après close. Le SDK avertit cependant que le drainage du prompt annulé dépasse son délai et prévoit de recréer la session au prochain tour. Ne pas confondre arrêt observé avec reprise transparente. Aucun conteneur de qualification restant après exécution; zéro appel modèle. Annulation des outils fournisseur et reprise distante non qualifiées.

## Démarrage sans téléchargement de tarifs
Inspection du fichier installé LiteLLM get_model_cost_map.py : LITELLM_LOCAL_MODEL_COST_MAP=True sélectionne explicitement la copie embarquée. Réglage ajouté au lanceur du banc sans modifier les services actifs. qualify_conversation.py rejoué sur VPS : code 0, quatre événements, aucun avertissement de téléchargement de table distante dans le log. Ce changement supprime une tentative réseau inutile; aucun gain chiffré de latence n'est revendiqué sans benchmark comparable. Les tarifs embarqués ne constituent pas une source de prix actuels.
