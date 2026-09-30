# Pilote Paperclip isolé

État vérifié par l'agent principal le 29 septembre 2026 : image officielle démarrée sur le VPS avec PostgreSQL dédié, réseau interne et aucun port publié. Depuis l'hôte, santé et interface répondent HTTP 200 ; l'API companies sans session répond 403. Processus applicatif UID 1000, fichiers secrets mode 600. Migrations initiales appliquées puis auto-application désactivée ; inscriptions fermées. Propriétaire encore non initialisé. Le tunnel local tenté par l'agent principal a été refusé par le contrôle automatique ; le parcours navigateur reste non vérifié. Voir [rapport de validation](../../PILOTE-VALIDATION-2026-09-29.md). Les sections de préparation ci-dessous décrivent la procédure et les contrôles de l'agent infrastructure, distincts de cette validation runtime.

Source examinée : `paperclipai/paperclip`, commit `29c8fb0b66cb01167f71e7107a89628e36b5e032`. Aucune installation ni exécution du dépôt téléchargé. Le skill AgentMemory Curator impose de traiter cette référence comme non fiable tant que sa revue n'est pas terminée : 38 alertes statiques high, indexation non approuvée. Cela ne prouve pas 38 vulnérabilités; les patterns comprennent notamment installateurs, postinstall et suppression de répertoires. Aucune skill du dépôt installée.

## Images et reproductibilité

`compose.json` contient deux références par digest, sans build ni tag mutable. L'image Paperclip officielle correspond au commit étudié; root a vérifié cryptographiquement l'attestation GitHub avec le workflow `.github/workflows/docker.yml` (preuve `.validation/paperclip-attestation.json` à la racine Orchestrator). PostgreSQL officiel a été inspecté par root : famille 17-alpine, variante amd64 17.11-alpine3.24. La preuve couvre provenance et digest, pas l'absence de défauts logiciels.

L'upstream Dockerfile part de Node 24 (`Dockerfile:2`). La cible officielle est explicitement `production` (`.github/workflows/docker.yml`), pas la dernière cible cloud. Un build local du même commit n'est pas reproductible bit à bit : base OS mutable, apt et outils fournisseurs installés avec `@latest` (`Dockerfile:158`). Utiliser le digest officiel revu; ne pas lancer les installateurs ni `curl | sh`. Un build alternatif demanderait une revue distincte des pins de toute la chaîne.

## Isolation prévue

- Projet Compose `oria-paperclip-pilot`; deux volumes dédiés, aucune réutilisation de base, dépôt, mémoire ou credentials existants.
- Aucun port publié, ni UI ni PostgreSQL. Accès opérateur par tunnel SSH vers l'IP privée du conteneur, résolue à chaque accès (voir ci-dessous), puis navigateur `http://localhost:3310`.
- Réseau Docker `internal: true` : pas de fournisseurs/modèles sortants à cette étape. Pas de socket Docker, montage hôte sensible, réseau host ni mode privilégié.
- Processus nonroot `node` et `postgres`; racine readonly, capabilities retirées, no-new-privileges, tmpfs bornés, limites CPU/RAM/PID et logs rotatifs. Aucun redémarrage automatique au stade pilote.
- Authentification obligatoire; heartbeat, annonces, télémétrie, vérification de mises à jour désactivés. Ne créer/exécuter aucun agent avant la validation du pilote. La désactivation du scheduler seule n'est pas une interdiction des lancements manuels.
- Le fichier de configuration non secret est monté en lecture seule par Compose. Pour un `configs.file` implémenté par bind mount, Compose peut ignorer `mode`; conserver le fichier source JSON non secret en 0644 (confirmé dans le pilote), sans compter sur un changement de propriétaire ou de mode par Compose. Les volumes nommés ne sont pas chiffrés par ce dossier.

## Accès privé sans publication ni sortie réseau

Sur le moteur Docker du pilote, le réseau `internal: true` n'a pas créé de binding effectif malgré une ancienne déclaration de port localhost. Cette déclaration a donc été retirée. Ne pas ajouter de réseau externe ni désactiver `internal` pour rendre l'UI accessible.

Depuis le répertoire du pilote **sur le VPS**, résoudre l'IP actuelle :

```sh
container_id=$(docker compose -f compose.json --env-file .env ps -q paperclip)
test -n "$container_id"
docker inspect --format '{{(index .NetworkSettings.Networks "oria-paperclip-pilot_pilot-internal").IPAddress}}' "$container_id"
```

Vérifier depuis l'hôte VPS que `http://IP_ACTUELLE:3100/api/health` répond. Depuis l'ordinateur opérateur, ouvrir ensuite :

```text
ssh -N -L 127.0.0.1:3310:IP_ACTUELLE:3100 UTILISATEUR@VPS
```

`IP_ACTUELLE` doit être la valeur fraîchement inspectée, jamais une IP figée dans Compose. Ouvrir `http://localhost:3310` dans le navigateur. Le listener du tunnel est lié uniquement à la boucle locale de l'ordinateur opérateur. Le serveur conserve `PAPERCLIP_PUBLIC_URL=http://localhost:3310` pour l'origine et les liens d'authentification; l'adresse IP est seulement la destination interne du tunnel.

Après recréation du conteneur, résoudre à nouveau son IP et relancer le tunnel si elle change. Si la connexion hôte→conteneur échoue, ne pas affaiblir l'isolation : examiner la connectivité du bridge et les règles de forwarding SSH avec root. L'accès hôte→IP puis navigateur→tunnel doit être vérifié séparément; le simple healthcheck dans le conteneur ne le prouve pas.

## Séquence opérateur à revoir puis exécuter séparément

1. Vérifier RAM/disque disponibles sans arrêter d'autres services. Le port 3310 doit être libre sur l'ordinateur opérateur pour le tunnel; aucun port VPS n'est réservé. Budget maximum runtime : 2 Gio RAM au total, CPU 1.5, plus overhead hôte/Docker et espace images. Confirmer architecture/image via inspection registry; aucun changement aux services existants.
2. Copier **uniquement ce dossier** dans un répertoire pilote dédié. Créer `.env` privé (mode 600) depuis `.env.example`. Générer localement deux secrets indépendants de 32 octets, encodés en 64 caractères hex : mot de passe PostgreSQL et secret session `BETTER_AUTH_SECRET`. Ne pas les afficher, journaliser ni transmettre à la mémoire d'agents. Aucun credential Codex/Claude/Google demandé à cette étape.
3. Pour la première base vide seulement, mettre `PILOT_MIGRATION_AUTO_APPLY=true`. Garder `PILOT_DISABLE_SIGN_UP=true` jusqu'à l'accès opérateur prêt. Exécuter `sh preflight.sh` : lecture JSON/env et `docker compose config --quiet` uniquement. Éviter `docker compose config` sans `--quiet`, qui expose les secrets interpolés.
4. Après revue root : `docker compose -f compose.json --env-file .env pull`, puis `docker compose -f compose.json --env-file .env up -d`. Ces commandes exécutent les images revues; elles n'ont pas été lancées par l'agent préparateur. Vérifier santé, UID nonroot, volume writable, aucun port public, absence de redémarrages/OOM. Les permissions initiales des volumes sont à confirmer sur ce moteur Docker; si elles échouent, ne pas passer runtime root ni chown un chemin hôte : réparer uniquement les volumes nommés du pilote après revue.
5. Accéder par tunnel SSH. Pour créer le propriétaire, activer temporairement `PILOT_DISABLE_SIGN_UP=false`, recréer **seulement paperclip** avec `up -d --no-deps paperclip`, puis créer une invitation d'amorçage limitée à une heure :

```sh
docker compose -f compose.json --env-file .env exec paperclip node cli/node_modules/tsx/dist/cli.mjs cli/src/index.ts auth bootstrap-ceo --config /etc/paperclip/pilot.json --expires-hours 1 --base-url http://localhost:3310
```

L'URL produite est un secret temporaire : ouvrir dans le navigateur opérateur et créer/connecter le compte, accepter l'invitation; ne pas copier sa sortie aux logs partagés, screenshots ou rapports. Cette commande est issue de `cli/src/index.ts:269` et `auth-bootstrap-ceo.ts`, exige un fichier config (fourni) et utilise `DATABASE_URL`. Le mode privé offre aussi un premier-admin claim dans le navigateur; l'accès tunnel doit donc rester limité au propriétaire pendant bootstrap.

6. Après propriétaire confirmé : remettre `PILOT_DISABLE_SIGN_UP=true`, `PILOT_MIGRATION_AUTO_APPLY=false`, recréer uniquement paperclip. Vérifier `/api/health` indique bootstrap prêt, login du propriétaire fonctionne, une requête API board sans session est rejetée et une nouvelle inscription est refusée. `/api/health` seul ne démontre ni auth ni bootstrap réussi.
7. Aucune donnée réelle avant une sauvegarde/restauration vérifiée. Backup intégré désactivé au pilote (pas de pg_dump supposé dans l'image app). Le script préparé `backup-verify.sh` et [BACKUP-RESTORE.md](BACKUP-RESTORE.md) couvrent dump DB, volume app/clefs et configuration privée, avec restauration vers **de nouveaux volumes** sans réseau. Exécution seulement pendant une fenêtre sans signup/écritures confirmée par l'opérateur; ne pas le lancer pendant le bootstrap du propriétaire.

Arrêt réversible : `docker compose -f compose.json --env-file .env stop`. Les volumes restent présents. Ne pas utiliser `down -v` ni supprimer de volumes sans demande explicite.

## Contrôles réalisés et limites

`node check-static.mjs` vérifie isolation, limites, mode auth, images/pins et absence de socket/montages sensibles. JSON valide. Ce test n'exécute aucun code téléchargé; il ne valide pas encore démarrage, schéma Zod upstream, permissions de volumes, migrations, UI ou bootstrap. `preflight.sh` fourni mais non exécuté sur VPS. L'infrastructure sortante, login fournisseurs, agents et intégration HQ/Memex restent une étape distincte après acceptation.

Variables réelles confirmées dans `server/src/config.ts` : DATABASE_URL, HOST, PORT, SERVE_UI, PAPERCLIP_DEPLOYMENT_MODE, PAPERCLIP_DEPLOYMENT_EXPOSURE, PAPERCLIP_AUTH_BASE_URL_MODE, PAPERCLIP_PUBLIC_URL, PAPERCLIP_ALLOWED_HOSTNAMES, PAPERCLIP_AUTH_DISABLE_SIGN_UP, PAPERCLIP_SECRETS_STRICT_MODE, HEARTBEAT_SCHEDULER_ENABLED, PAPERCLIP_ANNOUNCEMENTS_ENABLED. `BETTER_AUTH_SECRET` vient de `server/src/auth/better-auth.ts`; migration auto/prompt de `server/src/index.ts`. `PILOT_*` sont nos variables Compose, traduites vers ces noms réels. Le JSON est fondé sur `packages/shared/src/config-schema.ts`.
