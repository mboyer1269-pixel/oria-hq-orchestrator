# ORIA HQ — orchestration et intégrations

État courant : [contrat de livraison du 1 octobre 2026](docs/HQ-LIVRAISON-2026-10-01.md), avec responsabilités, dépendances et critères vérifiables. Hermes est l'orchestrateur cible; HQ conserve les missions; OpenHands exécute. La mission réelle complète et la validation de la maquette restent à obtenir.

Lot technique accepté dans le candidat `286a211` : 65 tests ciblés, banc PostgreSQL réel, sonde indépendante des erreurs du registre et quatre validations globales réussis. Les délais HTTP et la conservation des coûts incertains sont corrigés. Le budget reste désactivé; aucune mission modèle réelle n'est prouvée par ces tests. La maquette mobile `d821773` passe 33 tests et une recette navigateur; elle attend la validation visuelle de Michael. [Résultats et limites du lot](docs/HQ-BUDGET-ACCEPTATION-2026-10-01.md).

Dépôt privé des scripts hôte, adaptateurs, qualifications et plans de l'atelier de développement ORIA HQ. Le produit HQ reste dans son dépôt distinct ; ce dépôt ne contient ni son application complète ni Memex Core.

Qualification locale complémentaire acceptée dans `cf4fc4a` : 10 tests route/owner et bancs, lint ciblé et PostgreSQL réel réussis. Les rôles clients ordinaires ne lisent ni ne modifient les données de mission/budget testées. Les comptes d'authentification restent synthétiques; aucune session Supabase ou mission modèle réelle n'est prouvée. [Contrôles, commandes et limites](docs/HQ-FRONTIERES-ACCES-2026-10-01.md).

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
| Admission de mission, Antigravity puis revue Cursor | 18 tests de contrat rejoués. Banc PostgreSQL/PostgREST réel terminé code 0 après correctif `78df517` repris dans `ad549d7`; concurrence, réponse perdue et quatre missions conservées après redémarrage. Qualification route/owner synthétique et RLS locale ajoutée dans `cf4fc4a`, vérifiée par Codex. | Le lanceur privilégié et l'authentification utilisateur réelle restent à qualifier. RLS testée avec rôles locaux sans BYPASSRLS, sans JWT Supabase. Admission ne signifie ni autorisation ni exécution. [Qualification des accès](docs/HQ-FRONTIERES-ACCES-2026-10-01.md). |
| Accès et reprise, Claude Code | 110 tests ciblés et dépendants rejoués; état et charge isolés par workspace. Recette CUA du vrai formulaire réussie : choix explicite, réessai, réponse tardive, stockage indisponible et rechargement. Texte OpenHands corrigé dans `e0d80e5`. | Transport simulé pour les clics : auth/base/agent réels restent distincts. [Preuves et limites](docs/HQ-RECETTE-NAVIGATEUR-2026-10-01.md). La sonde Hermes ne démontre pas encore l'installation VPS. |
| Modèles et coûts, Cursor | Routage de la [PR #7](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/7) assemblé. Nouveau registre et délai via la [PR #9](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/9), accepté techniquement : 65 tests et banc PostgreSQL réel réussis, montants et identités préservés après redémarrage. | Les réservations bornent des devis serveur, pas une facture garantie. Flag désactivé, aucun tarif ni plafond réel ajouté. Erreurs du registre et fallback corrigés; chat réel, auth/RLS et OpenHands hors preuve. [Résultats et limites](docs/HQ-REVUE-BUDGET-2026-10-01.md). |
| Interface, Antigravity | Maquette `d821773` : 33 tests, continuité de mission et brouillon vérifiée dans le navigateur; largeur mobile 375/375 à 390 × 844. Saisie, actions et prochaine étape visibles. | Validation visuelle de Michael et raccordement réel requis. Les outils, preuves, modèles et budgets restent des démonstrations. [Recette et captures](docs/HQ-MAQUETTE-MOBILE-2026-10-01.md). |

Le candidat de code `286a211` passe TypeScript, lint (zéro erreur, cinq avertissements préexistants), compilation et smoke local. Ces validations ne prouvent aucun appel de modèle réel. Le parcours synthétique couvre le dossier, les réservations durables, le contrôle des permissions, les limites temporelles, les refus et la conservation de preuves. Les rapports datés décrivent également des qualifications Docker/Linux, PostgreSQL/PostgREST et navigateur, chacune avec son périmètre.

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
