# HQ — contrat du dossier de mission

29 septembre 2026 — conception du premier parcours ; aucune intégration distante livrée par ce document.

## Choix de départ

Construire un parcours complet autour d'une mission, avant de multiplier les agents. HQ présente le travail ; un seul orchestrateur possède la file et les transitions ; Memex fournit les connaissances versionnées. Paperclip reste un candidat à évaluer, pas une dépendance imposée. AgentMemory local reste réservé au développement.

Ces responsabilités décrivent la cible, pas des fonctions déjà livrées. Le dossier est une vue liée aux objets canoniques : l'orchestrateur possède les tâches et exécutions, Memex les connaissances publiées, Git les révisions de code. HQ conserve leurs références, sans devenir une seconde source de vérité. Une décision opérationnelle appartient à la mission ; sa publication durable dans Memex garde cette provenance et ne crée pas une seconde décision modifiable indépendamment.

## Dossier commun

Chaque mission conserve : projet, objectif, résultat attendu, critères de réussite, responsable, contraintes, décisions versionnées, tâches et dépendances, références de mémoire, exécutions, livrables et preuves de validation.

Chaque tâche conserve : identifiant stable, objectif borné, entrées autorisées, dépendances, rôle chargé du travail, état, version du contexte, tentative active, budget, livrable et critères de validation. Les secrets sont uniquement référencés par le connecteur.

Une exécution identifie le modèle et le connecteur réellement utilisés, les outils appelés, les révisions de code et de mémoire, les horaires, les erreurs et la consommation connue. Un quota ou coût non fourni est « inconnu », jamais zéro. Les traces permettent d'expliquer le parcours ; elles ne garantissent pas une reproduction exacte des réponses d'un modèle.

## Règles d'exécution

- États : à préciser, prête, en cours, bloquée, à vérifier, validée, annulée. Une tâche ne devient prête que lorsque ses dépendances et son contexte sont valides.
- Le worker obtient un bail limité dans le temps. Une reprise crée une nouvelle tentative ; les écritures d'une ancienne tentative sont rejetées grâce à un jeton de génération.
- Une clé d'idempotence protège chaque commande à effet externe. Après une interruption, réconcilier le résultat avant de répéter une action dont l'issue est inconnue.
- Une clé locale ne garantit pas l'unicité chez un fournisseur externe : utiliser sa prise en charge native ou rechercher une preuve de l'effet. Si l'issue reste ambiguë et que la répétition présente un risque, bloquer cette action pour résolution plutôt que la relancer automatiquement.
- La pause arrête les nouvelles affectations ; HQ indique séparément les opérations déjà en cours et celles effectivement arrêtées. Les délais de pause dépendent du connecteur.
- Un changement de décision produit une nouvelle version, marque les tâches concernées à resynchroniser et conserve les versions antérieures. Les résultats déjà produits sont réévalués si la décision touche leurs critères.
- Un agent ne valide pas seul sa propre livraison : vérification déterministe lorsque possible, revue indépendante pour les changements importants, décision humaine selon les règles du projet.
- Une réunion possède une question, des participants pertinents, un plafond de contributions et une issue : décision, expérience à réaliser ou blocage. La conversation n'est pas automatiquement une connaissance validée.

## Contrat Memex

Le serveur déduit les projets autorisés de l'identité authentifiée, y compris lors des recherches, exports et accès par identifiant. Chaque souvenir conserve provenance, portée, statut, version et relation éventuelle de remplacement. Les contenus externes restent des données non fiables, jamais des instructions système.

Les agents proposent une modification en indiquant la version attendue ; un conflit exige une résolution explicite. Une voie de publication unique enregistre le changement et son événement durable. Les index et vues dérivées sont reconstruisibles ; une recherche indique si sa projection est en retard. Les faits remplacés ou en quarantaine sont exclus du contexte courant par défaut, mais consultables pour l'historique avec les droits requis.

Le paquet de contexte contient un socle commun de décisions, puis des extraits pertinents au rôle et à la tâche, avec leurs sources. Il respecte un budget explicite ; les pièces longues sont consultées à la demande. Une correction importante invalide les paquets concernés.

## Premier scénario : rappels de prospects

Données fictives uniquement. Objectif : afficher les prospects et préparer un rappel après 48 heures, sans envoyer de messages réels.

1. Le chef prépare quatre tâches : préciser le comportement, réaliser le tableau, réaliser les rappels, vérifier le parcours.
2. Deux agents d'exécution travaillent dans des espaces distincts, à partir de la même décision initiale ; le chef coordonne les contrats d'interface et l'intégration.
3. L'utilisateur change le délai à 24 heures. Memex conserve la nouvelle décision ; HQ indique les tâches et tests affectés.
4. Une exécution est interrompue. La reprise reçoit les fichiers, preuves et décisions utiles ; elle ne recrée pas les rappels déjà enregistrés.
5. Une vérification indépendante confirme le délai, l'absence de doublons et l'isolation des projets. HQ présente une version essayable et les limites restantes.

« Deux agents » signifie deux workers au maximum en parallèle, auxquels s'ajoute le rôle de coordination. Le chef n'est pas un modèle qui tourne en permanence : les transitions ordinaires sont déterministes ; un modèle intervient pour décomposer une demande ou résoudre une ambiguïté. La vérification utilise d'abord des tests et, si nécessaire, une revue distincte exécutée après la production, sans imposer un troisième worker permanent.

## Interface

La mission montre d'abord l'objectif, l'avancement réel, les décisions attendues et « Essayer le résultat ». Une tâche expose son responsable, sa dépendance bloquante et sa preuve. Le salon montre uniquement les messages explicites de collaboration. La mémoire permet de retrouver une source et de proposer une correction. Le détail d'exécution montre outils, erreurs et consommation observée.

Ne pas afficher de pourcentage artificiel de réussite ni déclarer « terminé » sur la seule parole d'un agent. Les animations suivent de vrais événements. Les actions restent accessibles au clavier et les états utilisent du texte, pas seulement une couleur.

## Étapes et conditions de passage

| Étape | Livraison | Condition de passage |
|---|---|---|
| 1. Contrat et scénario | Ce dossier et une grille d'acceptation | Règles et effets des interactions explicités |
| 2. Fiabilité Memex | Isolation, publication cohérente, versions | Tests de concurrence et de fuite entre projets réussis |
| 3. Pilote local | Une mission, deux agents, un connecteur vérifié | Résultat testable, interruption/reprise et double soumission maîtrisées |
| 4. HQ relié au pilote | Commandes et états persistants | Rafraîchir l'écran ou perdre la connexion ne perd pas la mission |
| 5. Optimisation | Routage et contexte mesurés | Qualité maintenue avec consommation réduite sur les mêmes scénarios |
| 6. Hébergement | Environnement dédié et restauration | Accès, sauvegarde/restauration et arrêt vérifiés avant données réelles |

Le routage commence par des règles simples : capacité nécessaire, accès autorisé, disponibilité, puis coût et qualité mesurés. Évaluer chaque abonnement avec son interface officiellement disponible ; un abonnement à une application ne prouve pas un accès API inclus. Ne pas ajouter une couche autonome de sélection avant de disposer de mesures fiables.

## Ajustement d'ordre et efficacité

Les étapes sont des conditions de passage, pas une obligation de tout réaliser en série. Dès le départ, vérifier un connecteur réel sur des données fictives et définir le contrat d'échange minimal. En parallèle de la fiabilisation Memex, HQ peut être essayé avec un adaptateur simulé implémentant ce même contrat. La connexion à une mémoire partagée réelle attend les contrôles d'isolation et de publication ; la maquette n'attend pas ces travaux.

Avant d'écrire un moteur, vérifier si le candidat existant satisfait les besoins de file, reprise et annulation. Conserver un seul moteur et ne développer que les adaptateurs manquants. Mesurer un parcours avec un seul worker comme référence, puis deux : garder le parallélisme seulement s'il améliore délai ou qualité sans coût disproportionné.

- Budgets distincts par mission : durée, appels, tokens observables et dépenses supplémentaires. Les appels de coordination, reprise et évaluation sont inclus. Arrêter ou réorienter à la limite ; définir des plafonds conservateurs lorsque les quotas sont inconnus.
- Recherche ciblée avant chargement de documents ; outils et compétences à la demande ; cache de contexte indexé par projet, droits, rôle et versions. Revalider les droits et invalider le cache après correction ou retrait d'accès.
- Pas de réunion pour un simple transfert de résultat. Partager un livrable court et ses références ; lancer une discussion seulement si une décision ou un désaccord le justifie.
- Traces structurées légères pour toutes les tentatives ; contenu détaillé minimisé et rétention bornée. Ne pas enregistrer automatiquement les secrets, toute la mémoire ou chaque conversation complète.
- Comparer la réussite sur les mêmes cas avant le coût. Mesurer aussi le délai, les reprises, le temps d'intervention humaine et les ressources locales : un modèle sans frais de tokens n'est pas sans coût d'exploitation.

Les économies restent une hypothèse tant qu'elles ne sont pas mesurées. Aucun chiffre de réduction ni choix définitif de framework n'est annoncé à cette étape.

## Inspiration Datadog

Retenir la corrélation entre mission, outil, recherche et évaluation ; adapter l'affichage à l'utilisateur de HQ. Aucune dépendance Datadog n'est nécessaire pour définir ce contrat. Références publiques consultées : https://docs.datadoghq.com/llm_observability/quickstart/terms/ et https://docs.datadoghq.com/llm_observability/investigate/.
