# Hermes — installation observée et mise à jour terminée

Michael a autorisé l'inspection SSH, puis demandé la mise à jour. Les mentions antérieures « SSH non autorisé » sont dépassées. Codex a effectué les opérations; Claude a revu les sources et le conditionnement, sans intervenir sur le VPS.

## Résultat constaté

- Installation Nous Research dans l'image Hostinger `ghcr.io/hostinger/hvps-hermes-agent`.
- Compose `/docker/hermes-agent-cmho/docker-compose.yml`, service `hermes-agent`, données persistantes en bind mount `/docker/hermes-agent-cmho/data:/opt/data`.
- Image maintenant épinglée : `ghcr.io/hostinger/hvps-hermes-agent@sha256:374874de079dc821db4cf9e67df8c8eee8064deb51c5b64524d3b130967045c1`.
- Version `0.21.5`, publication officielle `v2026.9.24`, source embarquée `f97608f178d1ffeca59860195ab7da295f7c8e5f`, confirmés par le paquet, `.hermes_build_sha` et `/etc/hermes/image-provenance.json`.
- Ancienne image `sha256:837f64b392abd400d0d740325ca5b5eb0891d9e12031432c201bbe95be395ba1` conservée et archivée. L'ancien paquet indiquait `0.15.2`, mais son pyproject indiquait `0.14.0`; son SHA amont n'est pas établi.

## Qualification effectuée

Avant remplacement : conteneur temporaire sans réseau, sans données de production, clé synthétique, sans soumission de run ni appel modèle. Santé 200, API sans clé 401, dashboard 302 vers connexion. Lecture authentifiée des capacités de ce conteneur : submission/status/events/stop/steer/approval et idempotence durable déclarés disponibles. Cette déclaration ne prouve pas l'exécution, ni les réglages authentifiés de l'instance de production.

Après remplacement du seul service Hermes : santé 200/version 0.21.5; refus API sans clé 401; dashboard redirigé vers connexion. Aucun nouveau port publié; proxy existant conservé. Environnement inchangé, changement du compose limité à l'image, autres identités de conteneurs inchangées. Les 4 009 chemins de fichiers de la sauvegarde existent encore dans les données. Cela ne constitue pas un contrôle sémantique de toutes les conversations et mémoires. Le conteneur temporaire a été supprimé.

## Retour arrière préparé

Sauvegarde privée sur le VPS : `/docker/hermes-agent-cmho/upgrade-20261001T180022Z`, répertoire protégé. Compose/environnement, image précédente, archive des données réalisée à l'arrêt du service, empreinte SHA256 et override de restauration conservés. Archive image : 2 971 978 240 octets; données : 189 962 240 octets. Aucun secret ou contenu runtime importé dans le dépôt ou AgentMemory. Archives vérifiées; restauration non exécutée. Ne pas supprimer l'ancienne image.

## Ce qui reste à démontrer

Session utilisateur réelle, capacités avec la configuration de production, compte/modèle autorisé, raccordement HQ et mission modèle complète. Aucune activation budgétaire ni mise en production HQ effectuée. La maquette reste soumise à validation visuelle distincte.

Sources : [publication Nous Research](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.24), [installation Hostinger](https://www.hostinger.com/tutorials/how-to-set-up-hermes-agent/). Le catalogue source Hostinger répond 404; le build n'a pas fait l'objet d'un audit complet de ses sources.
