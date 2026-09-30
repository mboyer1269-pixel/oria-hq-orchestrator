# Vérification sauvegarde/restauration — pilote Paperclip

Validation réelle effectuée le 29 septembre 2026. PostgreSQL restauré et nombres de lignes identiques ; volume applicatif restauré puis comparé membre par membre avec GNU tar. Preuves conservées uniquement sur le VPS : `/opt/oria-paperclip-pilot/backups/20260929T213558Z-aeadbfa4/result.txt`.

## Conditions vérifiées

Aucune exécution d’agent n’était enregistrée dans `heartbeat_runs`. L’application pilote a été arrêtée gracieusement, la base restant disponible pour `pg_dump`. Le script refuse de capturer si le conteneur applicatif tourne et vérifie de nouveau son arrêt après capture. Un contrôleur avec trap a redémarré l’application après le test : conteneur healthy et `/api/health` HTTP 200 vérifiés. Cette courte interruption concernait uniquement le pilote Paperclip.

## Exécution

Le script `backup-verify.sh` utilise Docker, Python3, OpenSSL, sha256sum et cmp ; aucun Node installé sur l’hôte n’est nécessaire. Les images doivent déjà être présentes et sont référencées par digest. L’opérateur doit vérifier l’absence de travail actif, arrêter gracieusement l’application et garantir son redémarrage même en cas d’échec.

```sh
cd /opt/oria-paperclip-pilot
# Après vérification de l’absence de mission active :
trap 'docker start oria-paperclip-pilot-paperclip-1 >/dev/null' EXIT
docker stop --time 30 oria-paperclip-pilot-paperclip-1 >/dev/null
bash backup-verify.sh
```

## Périmètre exact

- Source fixe : projet Compose `oria-paperclip-pilot`, volume `oria-paperclip-pilot_pilot-paperclip` et PostgreSQL correspondant ; provenance contrôlée.
- Copie privée de `.env`, configuration et overlays disponibles, dump PostgreSQL custom, archive du volume applicatif en lecture seule.
- Restauration dans de nouveaux volumes dédiés : refus de réutiliser un nom existant, aucun écrasement ni suppression.
- Conteneurs de vérification sans réseau, non privilégiés, limités en ressources. Aucun serveur Paperclip restauré ni fournisseur IA exécuté.
- Comparaison des tables/nombres de lignes et du contenu/métadonnées de l’archive applicative ; arrêt de la base de vérification et conservation privée des preuves.

Les fichiers de sauvegarde restent sur le VPS, répertoire 700 et fichiers privés. Ils contiennent des secrets nécessaires à la reprise : ne jamais les placer dans Git, AgentMemory ou un rapport public. Ils ne sont pas chiffrés ; une copie hors serveur nécessiterait une protection adaptée.

## Limites

Le succès prouve la restauration du dump et du volume, pas une reprise fonctionnelle complète : connexion propriétaire, sessions et exécution d’une mission sur l’instance restaurée restent à tester. Les snapshots DB et volume sont successifs ; le contrôle d’arrêt aux deux bornes et les nombres de lignes ne prouvent pas l’absence de toute écriture externe. Les volumes des fournisseurs isolés (`oria-*-home`) et les clés SSH des runners ne sont pas inclus dans cette sauvegarde ; leur reprise est une étape distincte. Aucun nettoyage automatique des preuves n’est effectué.