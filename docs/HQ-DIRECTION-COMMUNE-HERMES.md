# Direction commune validée — Hermes dans HQ

Cette directive remplace les formulations précédentes qui plaçaient Hermes comme simple exécutant optionnel. Cible produit validée : ORIA héberge HQ ; Hermes est l'interlocuteur quotidien et le chef d'orchestration ; OpenHands est un outil de développement délégué. HQ conserve les états, autorisations, identités et preuves. Ce rôle cible ne signifie pas que le branchement est opérationnel.

Une seule expérience : Discuter et Atelier, même contexte de projet et même mission. Conversation sans exécution automatique si simple question ; directive actionnable transformée en mission selon politique existante. Navigateur/terminal/fichiers rattachés à la mission. Mobile prioritaire, maquette indépendante avant intégration approuvée par l'utilisateur. AgentMemory reste local développement, jamais mémoire de production implicite.

## Propriétaires actuels

Mise à jour du 1 octobre 2026 : [contrat de livraison](HQ-LIVRAISON-2026-10-01.md). Cette répartition est la seule utilisée pour attribuer le travail courant.

- Claude Code : correction de la sonde `integrations/hermes-runtime-probe/` dans son worktree Orchestrator, pour reconnaître l'installation Hostinger observée et distinguer identité, capacités déclarées et qualification. Aucun fichier produit HQ.
- Cursor : recette indépendante du raccordement, tests et rapport dans `handoffs/cursor-hermes-acceptance/`. Aucun changement au backend du constructeur, au routeur ou à la maquette. Revue finale sur le commit remis par Antigravity.
- Antigravity : raccordement minimal Hermes vers les services HQ existants en copie backend isolée. Un sous-agent de revue en lecture seule au besoin. La maquette `d821773` et ses previews restent gelés; aucun changement UI canonique avant validation Michael.
- Codex : vérification indépendante, cohérence des contrats, préparation de l'assemblage et documentation. Une suite verte isolée ne vaut pas acceptation du parcours complet.

Mandat courant détaillé : [coordination après mise à jour Hermes](HQ-COORDINATION-HERMES-2026-10-01.md). Le constat VPS est disponible dans [le rapport de mise à jour](HQ-HERMES-MISE-A-JOUR-2026-10-01.md). Les anciens lots d'accès, de routage et de base de données restent clos dans leur périmètre qualifié.

Résultats et limites : [revue de livraison](HQ-REVUE-LIVRAISON-2026-10-01.md). Les anciens mandats ci-dessous sont conservés uniquement pour l'historique.

## Répartition historique — ne plus utiliser pour attribuer du travail
- Claude Code : intégration Hermes → mission HQ → OpenHands → résultat. Conserver le travail première mission ; inspecter version et capacités Hermes réellement disponibles. Définir puis implémenter le plus petit adaptateur compatible avec les contrats existants dans son checkout isolé. Pas de second registre de missions. Pas de remplacement du worker fiable. Ni nouveaux droits, frais, accès public ou copie de credentials. Si authentification manque, préparer adaptateur/tests et indiquer une seule action humaine exacte ; ne pas passer le lot à répéter les simulations.
- Cursor : terminer le risque de copie concurrente sur ses seuls fichiers snapshot et tests. Puis revue indépendante en lecture seule du contrat Hermes/HQ lorsqu'il est livré : identité, doublons, autorisations, reprise et résultat incertain. Ne pas implémenter un second adaptateur ni éditer le backend de Claude.
- Antigravity : maquette indépendante uniquement, Discuter/Atelier, Hermes interlocuteur principal, OpenHands dans le détail de la réalisation. Aucun raccordement production avant validation visuelle utilisateur. Conserver les interactions quotidiennes et pédagogiques, données de démonstration explicites ; ni faux terminal actif ni faux choix de modèle disponible.
- Codex : revue croisée, rapprochement des contrats et preuves, acceptation finale des lots ; ne pas accepter une auto-évaluation comme seule preuve.

## Livraison commune
Chaque lot rend fichiers/commit, preuves réellement exécutées, environnement, exclusions et limites. Toute modification de contrat partagée est proposée dans un document avant adoption par un autre agent. Un responsable d'écriture par périmètre, branches isolées, aucune fusion ou mise en production dans ce mandat.

Critère final à atteindre progressivement : une demande depuis Discuter crée une mission unique, Hermes délègue à OpenHands, l'état reste visible dans Atelier, le résultat est testé indépendamment et récupérable après reconnexion sans double lancement. Les tests synthétiques sont nécessaires mais ne suffisent pas à déclarer cette preuve réelle acquise. Vérifier compte/profil/budget avant modèle réel. L'explication pédagogique décrit décisions et preuves, pas raisonnement interne.

Autocritique obligatoire et concise : quelle hypothèse pourrait invalider le résultat, quel scénario adverse a été vérifié, ce qui demeure inconnu. Priorité au résultat utilisable ; pas de refonte opportuniste ni nouvelles couches sans besoin démontré.
