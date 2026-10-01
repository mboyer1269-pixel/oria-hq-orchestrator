# Remise en route de Docker pour la qualification locale — 1 octobre 2026

## Constat et intervention

Docker Desktop 4.69.0 ne démarrait plus. Le journal signalait un échec sur `run/dockerInference`; ce socket de zéro octet et attribut ReparsePoint datait du 29 septembre. La distribution `docker-desktop` était arrêtée. Le signalement [Docker #532](https://github.com/docker/desktop-feedback/issues/532) décrit un défaut comparable, sans garantir que toutes les occurrences ont la même cause.

L'arrêt officiel `docker desktop stop --timeout 25` a échoué. Codex a arrêté les seuls processus Docker précédemment identifiés par PID et chemin, puis vérifié leur disparition. Le répertoire `C:/Users/micha/AppData/Local/Docker/run`, lui-même non lié, a été conservé sous `run.stale-hq-20261001-020647`. Docker a été relancé depuis son binaire officiel installé.

Aucun volume, image, compte, credential ou réglage de sécurité n'a été supprimé ou modifié. Aucune réinitialisation usine. Cette intervention concerne la machine de développement, pas le VPS.

## Preuve de remise en route

Les clients Windows et WSL Ubuntu-24.04 répondent avec le moteur `29.4.0`. `docker ps` était vide après démarrage. `/usr/bin/docker` est disponible sous WSL. Les images du banc n'étaient pas présentes lors du premier contrôle.

Le blocage de démarrage local est donc levé. Cela ne prouve pas encore le banc de qualification du produit. Antigravity reprend son exécution dans des ressources jetables, avec journal complet, code de sortie et digests des images. La recette navigateur du formulaire est indépendante et ne prouve pas le serveur.

## Portée et suite

Le dossier conservé permet de revenir sur l'intervention en arrêtant préalablement Docker et en vérifiant l'état courant; ne pas l'effacer automatiquement ni remplacer un dossier actif. La persistance PostgreSQL, l'accès Hermes, le lancement protégé et la mission réelle sont des preuves différentes. Aucun accès SSH supplémentaire n'a été tenté.
