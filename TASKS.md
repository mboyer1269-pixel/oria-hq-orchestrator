# Tâches ORIA HQ constructeur

État de coordination au 1 octobre 2026. Références : [plan constructeur](PLAN-HQ-CONSTRUCTEUR.md), [mandats détaillés](docs/HQ-LIVRAISON-2026-10-01.md) et [revue indépendante](docs/HQ-REVUE-LIVRAISON-2026-10-01.md). Une case cochée désigne le livrable précis, pas l'achèvement du produit.

## Lot de consolidation en cours

- [x] Attribuer chaque périmètre à un seul agent et transmettre les directives.
- [x] Récupérer le patch Cursor sans étendre ses droits GitHub; vérifier le contenu transféré et le correctif avec 61 tests ciblés.
- [x] Assembler le runtime d'admission et le routage dans une copie isolée; 18 tests d'admission réussis dans cette copie.
- [x] Revoir et assembler les corrections d'accès et de reprise de Claude (`13930e1`, `abe4b81` → candidat `2f08e96`); 110 tests ciblés/dépendants passés chez Codex. Recette navigateur réalisée ci-dessous, avec transport simulé.
- [x] Corriger et vérifier la syntaxe du banc PostgreSQL d'Antigravity (`720d513`); ne pas confondre préparation et exécution.
- [x] Rétablir le moteur Docker local sans réinitialisation ni suppression des volumes; clients Windows et WSL vérifiés, moteur 29.4.0.
- [x] Exécuter le banc réel avec concurrence, réponse perdue et contenu préservé après redémarrage : run `1790836047_67270`, code 0; journal, assertions et nettoyage revus par Codex. Correctif de blocage stdin du banc intégré dans `ad549d7`.
- [x] Recette CUA du vrai formulaire avec transport simulé : résiduel, création explicite, réessai identique, changement de projet, réponse tardive ignorée, erreurs de stockage et rechargement. Voir `docs/HQ-RECETTE-NAVIGATEUR-2026-10-01.md`; l'ancien DOM maison est exclu de cette preuve.
- [x] Revue indépendante Cursor du banc réel (`a279100` repris dans `78d2d89`) : preuve de persistance maintenue; auth/RLS/Hermes explicitement non qualifiés.
- [x] Corriger et vérifier dans le navigateur la continuité Aujourd'hui → Discuter → Atelier de la maquette et l'état après GO (`87c00df`).
- [ ] Obtenir la validation visuelle de Michael puis raccorder l'interface aux événements réels.
- [x] Corrections de maquette `d821773` : séparation assistant/modèle/accès, continuité de mission et usage mobile vérifiés; 33 tests et recette CUA. Validation visuelle toujours requise.
- [x] Cursor : corriger et qualifier le composant budgétaire désactivé. 65 tests, PostgreSQL réel, sonde indépendante et quatre validations globales passants. Voir `docs/HQ-BUDGET-ACCEPTATION-2026-10-01.md`; activation, devis réels et identité des appelants restent à qualifier.
- [x] Claude puis Cursor : reproduire et corriger le délai HTTP après les en-têtes; Codex confirme 27 tests et une interruption du corps bloqué à 601–792 ms pour 600 ms demandés. Correctif intégré au candidat validé `286a211`.
- [x] Faire passer typecheck, lint, build et smoke sur le candidat de code `286a211` (0 erreur lint, 5 avertissements hors lot).
- [ ] Qualifier le vrai Hermes installé et l'accès modèle autorisé; réaliser la mission complète décrite ci-dessous.

## Implémenté ou qualifié dans un périmètre borné

- [x] Documenter le choix OpenHands SDK, les frontières HQ/Memex et le contrat de mission.
- [x] Préparer et vérifier les dossiers et les identités de source avant lancement.
- [x] Implémenter consommateur hôte, réservation durable et refus des doublons.
- [x] Implémenter supervision, deadline partagée, transport de permissions et refus par défaut.
- [x] Implémenter passerelle/relai fournisseur et rapports de réconciliation sans relance aveugle.
- [x] Qualifier des parcours synthétiques et scénarios de panne ; conserver leurs limites dans les rapports.
- [x] Fournir un paquet hôte reproductible avec manifeste et exclusions.
- [x] Fournir scripts et qualifications du contexte Memex et de la contribution gouvernée.
- [x] Fournir adaptateur Antigravity expérimental et tests de contrat.
- [x] Documenter le candidat staging, distinct de l'application active.

## À terminer avant de déclarer l'atelier utilisable

- [ ] Finaliser l'authentification fournisseur officielle et prouver son usage depuis le runner autorisé.
- [ ] Reconstruire un ensemble cohérent HQ/bridge/runner avec les derniers correctifs, config et montages protégés.
- [ ] Vérifier depuis HQ authentifié préparation, confirmation, lancement durable et état visible d'une mission réelle.
- [ ] Obtenir une modification utile en copie isolée, tests pertinents et aperçu essayable ; rattacher les preuves à la version exacte.
- [ ] Réaliser une revue indépendante du changement et tester le parcours réel de décision des permissions.
- [ ] Qualifier interruption, déconnexion, panne hôte/redémarrage et réconciliation des effets avant reprise réelle.
- [ ] Raccorder Antigravity à une mission complète avec contexte, résultat et annulation observés.
- [ ] Confier une amélioration d'ORIA HQ à l'atelier, puis livrer après revue avec retour arrière vérifiable.
- [ ] Mesurer durée, consommation disponible, interventions et reprises sur des missions comparables ; conserver les coûts inconnus comme inconnus.

## Publication et exploitation

- [x] Séparer ce dépôt d'intégrations des dépôts produit HQ et Memex Core.
- [x] Exclure clés, environnements, caches et artefacts runtime de la publication.
- [ ] Qualifier une installation durable de la version publiée ; la publication GitHub ne déploie aucun service.
