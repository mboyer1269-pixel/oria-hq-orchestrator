# Cursor — rendre la reprise opérateur exploitable et reproductible

## But et périmètre

Continuer le travail Claude/Codex, pas le recommencer. Livrer un parcours opérateur de qualification et de reprise utilisable depuis un checkout Linux propre : préparation, diagnostic explicable, réconciliation sûre, preuves et transfert vers la première mission réelle. HQ repose sur OpenHands ; ne pas ajouter un orchestrateur ni refaire l'interface. L'objectif final est un atelier de développement dans ORIA HQ qui permettra ensuite de terminer ORIA HQ lui-même.

Autonomie sur l'implémentation, les corrections ciblées et les tests ; exigence élevée sur les preuves. Une solution simple et terminée vaut mieux qu'une architecture supplémentaire. Ne pas promettre zéro bug, ne pas inventer de résultats, d'accès ou de capacités.

## Sources de travail

- Dépôt principal : mboyer1269-pixel/oria-hq-orchestrator, branche codex/cursor-recovery-handoff. Base fonctionnelle 59f279260d8ed7db7054867a66d3266e979e86a6 ; le commit contenant ce mandat est un ajout documentaire.
- Dépôt compagnon public : https://github.com/mboyer1269-pixel/Oria.HQ.Michael.HQ-APP.git, branche codex/hq-mission-dossier, commit e9ff840a38b4532b687bb29f3e2371afeeb3024e. Le consulter dans un checkout séparé si nécessaire. Ne pas mélanger avec oria-studio ou OKauto.
- Lire README, instructions applicables et docs/CLAUDE-CONCURRENCE-RESULTAT.md en priorité. Les rapports Claude plus anciens peuvent décrire un état remplacé : trancher avec le code et une reproduction.
- Cibles : integrations/openhands-runner, notamment launch_lease.py, permission_worker.py, reconcile_launch.py, provider_gateway.py, build_host_release.py et leurs tests ; côté compagnon, les contrats OpenHands dans src/server/missions.

## État déclaré à vérifier, pas à répéter comme un résultat personnel

Codex rapporte 165 tests Linux sans exclusion, un parcours connecté interrompu puis réconcilié sans seconde exécution, et la persistance après redémarrage de PostgreSQL. Ces essais utilisent un agent synthétique : aucun compte fournisseur ni modèle réel ; independentValidationPassed reste false. Aucun déploiement actif. Le nombre de tests est une référence, pas un quota artificiel.

Le verrou interprocessus protège les chemins coopératifs d'un seul hôte. Après un crash, la libération du verrou n'annule pas une commande déjà reçue par Docker. Une absence de conteneur depuis creation_requested, start_requested ou running reste ambiguë : docker_effect_unresolved, aucune clôture ni suppression. Préserver cette règle. Un résultat terminé ne peut être récupéré qu'avec l'identité exacte attendue et les preuves requises. Ne jamais transformer un timeout ou une observation manquante en succès ou annulation supposée.

## Phase 1 — établir la vérité et le chemin critique

1. Confirmer dépôt, branche, commit et arbre de travail. Créer une branche de livraison distincte à partir de cette base, sans reset destructeur.
2. Recenser les commandes de test réellement définies et les prérequis Python, Node, Git, Linux et Docker. Vérifier les outils disponibles ; ne pas supposer Docker privilégié ou un accès au VPS.
3. Exécuter une référence pertinente, enregistrer commandes, versions, résultats, durées et exclusions motivées. Identifier précisément les preuves impossibles dans cet environnement.
4. Produire une courte liste des écarts qui empêchent un opérateur nouveau de préparer et diagnostiquer une mission. Prioriser le blocage réel, puis implémenter ; ne pas s'arrêter au rapport d'audit.

## Phase 2 — livrer un parcours opérateur clair

Réutiliser les scripts et contrats existants. Ajouter ou compléter un point d'entrée documenté de préparation/inspection qui vérifie les prérequis sans lancer un modèle, puis restitue un rapport lisible et exploitable par machine. Inclure : identité de mission et d'exécutant, état canonique, observation Docker ou son indisponibilité, disponibilité du verrou, catégorie du blocage, prochaine action permise et preuves manquantes. Aucun secret dans ce rapport.

Séparer inspection sans effet, réconciliation autorisée et exécution. Une inspection ne modifie pas l'état et ne nettoie rien. Un état inconnu reste inconnu ; un refus doit indiquer une raison utile. Ne pas ajouter un bouton ou une option force qui contourne identité, permissions, chemins ou coordination. Si un outil similaire existe déjà, le compléter au lieu de le doubler.

La préparation à une vraie mission doit distinguer : outils disponibles, connecteur configuré, authentification effectivement vérifiée, autorisation présente, budget défini, espace isolé, validations prévues. Un fichier de configuration ne prouve pas l'authentification. En cloud sans compte fournisseur, rapporter ce prérequis comme non vérifié, sans bloquer les autres livrables.

## Phase 3 — qualification portable et adversariale

Rendre les vérifications indépendantes des chemins personnels Windows et du VPS historique. Construire des fixtures jetables et documenter une commande reproductible depuis un checkout neuf. Réutiliser le harness connecté existant autant que possible ; ne pas copier de données réelles ni de configuration secrète.

Couvrir avec des assertions d'effets, pas seulement des codes de retour :

- lancement nominal et résultat récupérable ;
- seconde demande identique, sans nouvelle exécution ;
- concurrence worker/réconciliation : le perdant ne touche ni Docker ni l'état ;
- crash après émission d'une commande dont l'effet est inconnu : aucune clôture sur simple absence ;
- réponse perdue après terminaison : récupération du même conteneur, bon code de sortie, aucune relance ;
- identité étrangère, chemin interdit, autorisation absente : refus avant effets ;
- observation indisponible : ressources conservées ;
- persistance et répétition de la réconciliation après redémarrage, lorsque le harness disponible le permet.

Utiliser des barrières déterministes pour les courses ; éviter les sleeps censés prouver la concurrence. Distinguer tests unitaires, vrais processus, Docker réel, agent synthétique et modèle réel. Ne jamais faire passer l'un pour l'autre. Si Docker n'est pas disponible, livrer le harness exécutable et ses contrôles indépendants, en signalant explicitement la qualification connectée restante.

## Phase 4 — efficacité et contrôle indépendant

Mesurer le temps des étapes reproductibles avant/après si une optimisation est justifiée. Éliminer une répétition ou attente inutile seulement si cela ne réduit pas les contrôles. Ne pas inventer de gains de tokens sans appels mesurés. Préférer scripts et tests aux analyses répétitives ; une seule implémentation active, délégation ciblée seulement si utile.

Relire le diff comme un réviseur : effets avant validations, erreurs masquées, logs secrets, faux succès, refus contournables, assertions tautologiques, dépendances supplémentaires injustifiées. Corriger les défauts concrets. Ne pas supprimer ou sauter des tests pour obtenir du vert. Donner les exclusions et leur impact si une capacité d'environnement manque.

## Phase 5 — rendu vérifiable

Livrer code, tests, documentation opérateur et docs/CURSOR-REPRISE-RESULTAT.md avec :

1. Résultat utilisable et commande exacte pour le reproduire.
2. Commits de départ et de livraison, fichiers essentiels et justification des choix.
3. Tableau des scénarios, commande exécutée, environnement, résultat et emplacement des preuves non sensibles.
4. Distinction explicite entre ce qui est exécuté, seulement implémenté et encore bloqué.
5. Mesures réelles, limites restantes et prochaine action minimale vers une première mission avec modèle.
6. Mise à jour de la liste de tâches et d'un handoff local au dépôt. AgentMemory est une mémoire locale de développement ; ne pas supposer son accès depuis Cursor cloud ni l'utiliser comme mémoire de production.

Publier la branche et ouvrir une PR brouillon si disponible, sans fusion. Ne pas déployer, modifier les permissions des comptes, transférer des identifiants, accéder au VPS actif ou lancer un modèle payant. L'absence d'accès ne justifie pas l'arrêt du travail indépendant. En cas de blocage, expliquer la preuve manquante et terminer tout ce qui reste possible.

Le défi est de rendre une situation incertaine compréhensible et maîtrisable sans jamais mentir sur l'état du travail. Le résultat attendu est un parcours opérateur terminé, pas une inflation du nombre de tests ou une nouvelle promesse d'architecture.
