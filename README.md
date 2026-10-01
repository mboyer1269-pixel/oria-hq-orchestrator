# ORIA HQ — orchestration et intégrations

État courant : [contrat de livraison du 1 octobre 2026](docs/HQ-LIVRAISON-2026-10-01.md), avec responsabilités, dépendances et critères vérifiables. Hermes est l'orchestrateur cible; HQ conserve les missions; OpenHands exécute. La mission réelle complète et la validation de la maquette restent à obtenir.

Dépôt privé des scripts hôte, adaptateurs, qualifications et plans de l'atelier de développement ORIA HQ. Le produit HQ reste dans son dépôt distinct ; ce dépôt ne contient ni son application complète ni Memex Core.

## Le HQ que nous construisons

**HQ est l'espace de travail quotidien dans ORIA : un même assistant, Hermes, pour discuter, apprendre et faire réaliser des projets.** Hermes est l'interlocuteur principal et le chef d'orchestration visé ; OpenHands est son outil délégué pour le développement logiciel. Ce positionnement décrit la cible produit, pas un branchement déjà opérationnel.

Deux espaces partagent le même contexte de projet et les mêmes missions :

- **Discuter** : poser une question, explorer une idée ou confier un objectif à Hermes. Une simple question ne déclenche pas une exécution.
- **Atelier** : suivre les missions issues des échanges, comprendre les décisions, examiner les preuves et essayer les résultats disponibles. Le navigateur, le terminal et les fichiers restent rattachés à la mission concernée.

Sur mobile, ces vues se succèdent sans perdre le contexte ; sur ordinateur, elles peuvent se compléter côte à côte. Les explications pédagogiques portent sur les décisions, les impacts et les preuves. La maquette et le code d'interface préparatoire restent isolés jusqu'à validation de la maquette, avant intégration dans HQ. Les données de démonstration et les fonctions non raccordées doivent être clairement identifiées.

## Responsabilités et frontières

- **Hermes, rôle cible** : recevoir la demande, organiser le travail, sélectionner les outils autorisés, déléguer et suivre le résultat. Ses capacités installées et son raccordement réel restent à qualifier ; le choix d'un modèle n'implique pas que tous les abonnements soient interchangeables.
- **HQ dans ORIA** conserve l'état officiel des missions, leurs identités, autorisations, décisions et preuves. Hermes et l'interface s'appuient sur ce même registre, sans créer un second suivi concurrent. Les scripts de bridge raccordent les contrats durables au consommateur hôte ; l'entrée Hermes n'est pas encore raccordée de bout en bout.
- **OpenHands SDK** exécute un dossier borné dans un environnement isolé. `integrations/openhands-runner` contient préparation, consommation, supervision, permissions, passerelle fournisseur et rapports de reprise.
- **AgentMemory, appuyé ici sur Memex Core**, partage uniquement la mémoire locale de développement entre les agents : décisions, contraintes et transmissions. Ce branchement n'est pas la mémoire d'exploitation d'ORIA, de Hermes ou de HQ ; il ne doit pas contenir de secrets ni de données runtime de production.
- **Les pilotes d'intégration Memex** préparent le contexte projet et un parcours gouverné de contribution/revue/publication. `deploy/memex-pilot` et `deploy/memex-tls` contiennent ces outils, pas le moteur mémoire complet. Un usage en production exige sa propre configuration, ses droits et sa qualification ; il ne réutilise pas implicitement la mémoire locale des développeurs.
- **Antigravity** dispose d'un adaptateur expérimental et de fixtures ; une commande CLI réussie ne prouve pas une mission orchestrée complète.

## État réel

Point de coordination du 1 octobre 2026. Les lots isolés ne sont pas intégrés au produit canonique. Les mandats courants sont définis dans le [contrat de livraison](docs/HQ-LIVRAISON-2026-10-01.md), les résultats indépendants dans la [revue](docs/HQ-REVUE-LIVRAISON-2026-10-01.md).

| Lot | Preuve disponible | Ce qui reste à établir |
| --- | --- | --- |
| Admission de mission, Antigravity | Runtime et harnais réunis dans le commit d'intégration `d331a39`; 18 tests CLI/service/handlers rejoués par Codex, sans exclusion. Syntaxe du harnais `720d513` vérifiée. | Qualification PostgreSQL/PostgREST persistante bloquée par le moteur Docker. Le lanceur privilégié et sa configuration restent à qualifier. Admission ne signifie ni autorisation ni exécution. |
| Accès et reprise, Claude Code | Lot source `13930e1`, intégré dans `c4659f1`. 107 tests ciblés et dépendants rejoués avec succès par Codex. | Recette navigateur du formulaire et contrôle global du candidat. La sonde Hermes déjà livrée a 64 tests rejoués; elle ne démontre pas l'installation VPS. |
| Modèles et coûts, Cursor | Lot récupéré par la [PR de transfert #7](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/7), appliqué en copie isolée. 61 tests ciblés passent après correction des identifiants invalides et de la comptabilité des tentatives. | Vérifications finales de l'ensemble; usage réel et budget persistant non qualifiés. Aucun tarif inventé ni repli payant implicite. |
| Interface, Antigravity et ses sous-agents | Maquette `87c00df` : continuité des directives, compteur après GO et ancien historique vérifiés dans le navigateur; largeur mobile 375/375 à 390 × 844. Protection de prévisualisation limitée au développement. | Validation Michael et raccordement réel requis. Les outils, preuves et budgets sont des démonstrations. Réactiver une ancienne directive crée une nouvelle mission de démonstration; le libellé mérite clarification. |

Le parcours synthétique couvre le dossier, les réservations durables, le contrôle des permissions, les limites temporelles, les refus et la conservation de preuves. Les rapports datés décrivent également des qualifications Docker/Linux, PostgreSQL/PostgREST et navigateur, chacune avec son périmètre.

**Une mission réelle complète, authentifiée, avec modification utile, tests, revue indépendante et aperçu reste à prouver.** Le compte fournisseur, les raccordements protégés et les scénarios de reprise doivent être qualifiés ensemble. Aucun rapport synthétique ni retour `agent_returned` ne vaut succès métier. Les anciens états de déploiement sont historiques : les images et archives indiquées peuvent précéder le code publié ici.

Le critère commun de livraison est un seul parcours : une directive depuis **Discuter** crée une mission unique, Hermes délègue à OpenHands selon les autorisations, **Atelier** expose l'état réel, puis le résultat revient avec ses tests et sa revue. Une reconnexion doit retrouver ce travail sans double lancement. La prochaine priorité est de fermer et qualifier cette chaîne, avant d'ajouter d'autres couches ou de déclarer le produit opérationnel.

## Plan et tâches

- [Direction commune Hermes/HQ et responsabilités des agents](docs/HQ-DIRECTION-COMMUNE-HERMES.md)
- [Revue indépendante et écarts à corriger](docs/HQ-REVUE-LIVRAISON-2026-10-01.md)
- [Direction mobile et intégration Hermes](docs/HQ-MOBILE-HERMES-DIRECTION.md)
- [Audit des directions d'interface](docs/AUDIT-DIRECTION-UI-HQ.md)
- [Plan constructeur et critères de sortie](PLAN-HQ-CONSTRUCTEUR.md)
- [Tâches réalisées et prochaines étapes](TASKS.md)
- [Contrat de première mission](docs/PREMIERE-MISSION-HQ.md)
- [Entrée hôte](integrations/openhands-runner/HOST-ENTRY.md), [consommateur](integrations/openhands-runner/HOST-CONSUMER.md), [livraison hôte](integrations/openhands-runner/HOST-RELEASE.md)
- [Reprise de passerelle](integrations/openhands-runner/GATEWAY-RECOVERY.md) et [autorité de revue](docs/REVIEW_AUTHORITY_DESIGN.md)

## Vérifications locales

Depuis la racine, avec Python et Node.js disponibles :

```sh
python -m unittest discover -s integrations/openhands-runner -p 'test_*.py'
node --test integrations/antigravity/runner.test.mjs integrations/antigravity/paperclip-adapter.test.mjs
node --test deploy/hq-pilot/readiness.test.mjs deploy/hq-pilot/development-snapshot.test.mjs
```

Le test `deploy/hq-pilot/execution-bundle.test.mjs` exige en plus `HQ_SOURCE_ROOT` pointant vers le dépôt HQ réel et ses dépendances ; exécuter ce test séparément après configuration.

Certains tests hôte exigent les primitives Unix et sont ignorés sous Windows. Les qualifications `qualify_*.py` et les scripts `deploy/` ont des prérequis spécifiques décrits dans leurs README ; ne pas les assimiler à des tests locaux sans effets. Plusieurs exigent Docker Linux, les dépôts frères HQ/Memex et des configurations protégées.

Créer une archive hôte locale, sans installer ni démarrer de service :

```sh
python integrations/openhands-runner/build_host_release.py --output .validation/host-release
```

Le constructeur refuse un fichier archive déjà présent. Le manifeste décrit les fichiers retenus ; reconstruire puis vérifier les empreintes avant toute installation.

## Contenu publié

Sources, tests, fixtures synthétiques, modèles de configuration sans secret et comptes rendus de qualification sont conservés. `.validation`, caches, dépendances installées, archives générées, environnements, clés et état d'authentification restent exclus. Les chemins opérateur et identifiants d'images des rapports servent à tracer des essais historiques et ne constituent pas une configuration portable prête à déployer.
