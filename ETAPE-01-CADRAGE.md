# Orchestrator et Oria HQ — étape 1

Date : 29 septembre 2026. Statut : proposition, sans installation ni déploiement.

## Constat vérifié

Le dépôt Orchestrator ne contenait aucun fichier de travail. Les cinq dépôts partagés sont déjà présents sous `C:/Users/micha/.agentmemory/knowledge-packs/import-2026-09-29/repos`. Leur manifeste contient les commits et les rapports de scan. Ils restent en attente de revue ; les indicateurs statiques ne prouvent pas une vulnérabilité. Aucun de leurs programmes n'a été exécuté dans cette étape.

Le handoff AgentMemory du 29 septembre décrit un VPS Hostinger de 4 vCPU / 16 Go, Docker/Traefik et Hermes. Cet inventaire antérieur n'a pas été revérifié ici. Le code actuel de HQ et l'authentification des agents sur le VPS restent à examiner.

## Sélection proposée

| Dépôt | Utilité | Décision proposée |
| --- | --- | --- |
| [Paperclip](https://github.com/paperclipai/paperclip) | Coordination des agents, tâches, organisation, budgets ; serveur Node.js et interface React | Premier candidat à un pilote |
| [CUA](https://github.com/trycua/cua) | Automatisation d'interfaces et environnements de computer use | Plus tard, pour un besoin concret sans API adaptée |
| [CLI-Anything](https://github.com/HKUDS/CLI-Anything) | Création d'interfaces CLI pour logiciels | Outil complémentaire à évaluer logiciel par logiciel |
| [Archify](https://github.com/tt-a1i/archify) | Diagrammes et documentation visuelle | Complément documentaire |
| [codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web) | Pont entre ChatGPT Web et Codex avec connexion navigateur | Hors du socle initial : dépendance à une session Web et à une intégration tierce |

Ces rôles sont issus des présentations officielles et des README locaux, pas d'une validation en exécution. Paperclip paraît le mieux adapté parmi ces cinq dépôts ; ce n'est pas un classement exhaustif des orchestrateurs.

## Architecture proposée

HQ est l'interface de création et de supervision. Une API appartenant à notre projet traduit ses demandes vers l'orchestrateur. Paperclip pilote les tâches de fabrication ; des workers isolés exécutent les agents développeurs. Les agents métier fabriqués possèdent leur propre environnement d'exécution.

Flux : HQ → API Orchestrator → Paperclip → worker de développement → branche Git et tests → version d'agent → environnement de test → publication.

- HQ : catalogue, formulaire de création, versions, résultats de tests, statut et commandes de pause.
- API Orchestrator : identifiants stables, autorisations, lancement idempotent, adaptation aux API Paperclip, remontée du statut et des résultats. Éviter une seconde file de tâches concurrente à celle de Paperclip.
- Paperclip : affectation et suivi du travail. Vérifier les comportements de reprise, budgets et annulation dans le pilote.
- Workers : workspace isolé par tâche, droits limités aux outils nécessaires, journaux et artefacts associés à un identifiant d'exécution.
- Agents produits : configuration versionnée, outils autorisés, modèle, limites, tests et runtime séparé de la fabrication.
- Mémoire : AgentMemory reste local au développement. Les données et mémoires métier de HQ/Oria ont un stockage distinct.

Une définition d'agent minimale contiendrait : id, version, objectif, entrées/sorties, modèle, outils autorisés, limites de coût/durée, politique de mémoire, tests d'acceptation, cible d'exécution et état de publication. Les secrets sont référencés, jamais inclus dans cette définition.

## Progression et critères de réussite

1. Inventaire et sélection : cette note constitue le premier résultat.
2. Audit Paperclip ciblé : examiner les adaptateurs Codex/Claude/Hermes, l'API d'intégration, l'authentification, les scripts d'installation, les volumes et les alertes de scan pertinentes. Définir ensuite une configuration de pilote reproductible sur un commit fixé.
3. Premier scénario : fabriquer un agent simple qui transforme un brief en liste de tâches, sans accès client. Commencer par un worker développeur ; ajouter une revue distincte après validation du premier parcours.
4. Relier HQ : créer l'agent, lancer un test, consulter résultat/coût/statut, arrêter l'exécution. Vérifier qu'une double soumission ne lance pas deux fabrications.
5. Robustesse : tester interruption et reprise, panne fournisseur, annulation, limites de coût et restauration. Mesurer RAM et CPU avant d'augmenter la concurrence.
6. Extension : ajouter outils spécialisés et agents métier selon les besoins mesurés.

Le pilote sera concluant lorsqu'une demande produira une version d'agent traçable, testée et exécutable en environnement de test, avec résultat visible depuis HQ. Aucun framework supplémentaire n'est nécessaire à télécharger avant d'avoir identifié un manque concret dans ce parcours.

## Points encore ouverts

Emplacement et état réel du code HQ ; adaptateurs et authentifications effectivement disponibles ; compatibilité du conteneur Hermes existant ; isolation réelle entre organisations ; précision du suivi des coûts ; capacités de reprise et d'annulation ; ressources libres sur le VPS. La documentation commerciale ne suffit pas à valider ces propriétés.
