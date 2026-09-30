# Équipe du pilote HQ / Memex

Mandat utilisateur : avancer de manière autonome, par étapes vérifiables, avec une équipe coordonnée. Aucun résultat simulé ne doit être présenté comme une exécution réelle.

| Responsable | Livrable attribué | Périmètre de fichiers | Critères de passage |
|---|---|---|---|
| Agent HQ | Client Paperclip en lecture, mapping workspace/company, route authentifiée | Dépôt HQ, server/orchestration et route dédiée | Refus sans session/config, contrôle company, réponse validée, timeout, tests ; aucun dispatch ni seconde file |
| Agent infrastructure/sécurité | Pilote Docker privé reproductible | Orchestrator/deploy/paperclip-pilot | Images par digest, authentification explicite, données dédiées, non-root, pas de docker socket, limites CPU/RAM, contrôle Compose |
| Agent mémoire | Barrière de visibilité de publication | Memex graph/publication et tests | Contribution partielle invisible aux lectures ordinaires ; reprise et isolement vérifiés sans masquer les données déjà publiées |
| Agent principal | Revue croisée, provenance images, intégration et validation VPS | Orchestrator, commandes de validation et coordination | Vérifications finales cohérentes, preuves conservées, services existants préservés, blocages réels signalés |

## Règles communes

- Préserver tous les changements existants. Ne pas modifier un fichier détenu par un autre agent sans coordination.
- Lire les instructions du dépôt ; utiliser les compétences pertinentes à la tâche, sans installer une collection globale de skills.
- Chargement du contexte à la demande : contrats, changements concernés et preuves. Pas de conversation complète copiée entre tous les agents.
- Les modèles interviennent pour la conception et les ambiguïtés. Contrôles, publication validée, routage simple et tests restent déterministes lorsque possible.
- Un agent annonce son périmètre et sa méthode avant modification ; un autre vérifie les interfaces qui touchent son domaine.
- Fournir tests exécutés, échecs et limitations. Une suite verte ne prouve pas zéro bug.
- Aucun appel fournisseur payant, envoi externe, migration de données réelles ou désactivation de l'authentification pour simuler une intégration.
- Les mots de passe et tokens restent hors des rapports, du code et de la mémoire partagée.

## Ordre d'intégration

1. Barrière Memex et lecture HQ développées en parallèle avec préparation du pilote.
2. Revue de provenance et configuration ; démarrage privé seulement lorsque le dossier est concret et vérifié.
3. Lecture authentifiée d'une mission synthétique et validation des frontières workspace/company.
4. Connexion interactive du compte fournisseur dans le worker dédié, puis une tâche bornée.
5. Ajouter création, dispatch, reprise et annulation durables avant un second worker.

Paperclip reste seul propriétaire de la file d'exécution. HQ lit ses états et contrôle les commandes ; Memex reste propriétaire des connaissances. Le présent fichier est une consigne de coordination, pas la preuve que chaque étape est déjà accomplie.
