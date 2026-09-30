# ORIA HQ — orchestration et intégrations

Dépôt privé des scripts hôte, adaptateurs, qualifications et plans de l'atelier de développement ORIA HQ. Le produit HQ reste dans son dépôt distinct ; ce dépôt ne contient ni son application complète ni Memex Core.

## Rôles

- **ORIA HQ** conserve les missions, décisions et états visibles. Ses scripts de bridge raccordent le contrat durable au consommateur hôte.
- **OpenHands SDK** exécute un dossier borné dans un environnement isolé. `integrations/openhands-runner` contient préparation, consommation, supervision, permissions, passerelle fournisseur et rapports de reprise.
- **Memex** fournit le contexte projet et un parcours gouverné de contribution/revue/publication. `deploy/memex-pilot` et `deploy/memex-tls` contiennent les outils d'intégration, pas le moteur mémoire complet.
- **AgentMemory** reste uniquement une mémoire locale de développement, distincte des services et données de production.
- **Antigravity** dispose d'un adaptateur expérimental et de fixtures ; une commande CLI réussie ne prouve pas une mission orchestrée complète.

## État réel

Le parcours synthétique couvre le dossier, les réservations durables, le contrôle des permissions, les limites temporelles, les refus et la conservation de preuves. Les rapports datés décrivent également des qualifications Docker/Linux, PostgreSQL/PostgREST et navigateur, chacune avec son périmètre.

**Une mission réelle complète, authentifiée, avec modification utile, tests, revue indépendante et aperçu reste à prouver.** Le compte fournisseur, les raccordements protégés et les scénarios de reprise doivent être qualifiés ensemble. Aucun rapport synthétique ni retour `agent_returned` ne vaut succès métier. Les anciens états de déploiement sont historiques : les images et archives indiquées peuvent précéder le code publié ici.

## Plan et tâches

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

Inspection sans effet, sans modèle et sans réconciliation :

```sh
python integrations/openhands-runner/operator_status.py
```

Le code de sortie 0 signifie qu'un rapport a été produit. Il ne signifie pas qu'une mission réelle est prête. `readyForRealMission` reste faux tant que l'authentification fournisseur, l'autorisation d'exécution, la revendication canonique et Docker ne sont pas observés. Une indisponibilité Docker n'est pas une absence de conteneur. Voir [le rapport d'inspection](integrations/openhands-runner/OPERATOR-STATUS.md).

Le test `deploy/hq-pilot/execution-bundle.test.mjs` exige en plus `HQ_SOURCE_ROOT` pointant vers le dépôt HQ réel et ses dépendances ; exécuter ce test séparément après configuration.

Certains tests hôte exigent les primitives Unix et sont ignorés sous Windows. Les qualifications `qualify_*.py` et les scripts `deploy/` ont des prérequis spécifiques décrits dans leurs README ; ne pas les assimiler à des tests locaux sans effets. Plusieurs exigent Docker Linux, les dépôts frères HQ/Memex et des configurations protégées.

Créer une archive hôte locale, sans installer ni démarrer de service :

```sh
python integrations/openhands-runner/build_host_release.py --output .validation/host-release
```

Le constructeur refuse un fichier archive déjà présent. Le manifeste décrit les fichiers retenus ; reconstruire puis vérifier les empreintes avant toute installation.

## Contenu publié

Sources, tests, fixtures synthétiques, modèles de configuration sans secret et comptes rendus de qualification sont conservés. `.validation`, caches, dépendances installées, archives générées, environnements, clés et état d'authentification restent exclus. Les chemins opérateur et identifiants d'images des rapports servent à tracer des essais historiques et ne constituent pas une configuration portable prête à déployer.
