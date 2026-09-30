# HQ — grille d'acceptation du pilote

Statut : scénarios définis, non exécutés. Données fictives ; aucun connecteur réel testé par cette grille.

| Cas | Manipulation | Résultat attendu |
|---|---|---|
| Mission complète | Soumettre le suivi de prospects | Sous-tâches liées, version essayable et preuves rattachées |
| Double soumission | Répéter la même commande | Une seule mission ou un seul effet, retour du résultat existant |
| Décision corrigée | Passer de 48 à 24 heures | Historique conservé, tâches affectées identifiées, nouveau contexte distribué |
| Correction concurrente | Deux écritures fondées sur la même version | Une acceptée, conflit explicite pour l'autre, aucune perte silencieuse |
| Fait remplacé | Rechercher après correction | Nouvelle règle par défaut ; ancienne règle seulement dans l'historique |
| Projet isolé | Chercher une note d'un autre projet avec un agent non autorisé | Aucun contenu ni métadonnée révélés, y compris par identifiant direct |
| Worker interrompu | Arrêter après un effet avant confirmation | Reprise après réconciliation, aucun doublon |
| Ancien worker | Faire répondre une tentative après expiration du bail | Résultat périmé rejeté, tentative active préservée |
| Pause | Mettre en pause pendant une opération | Aucun nouveau départ ; état réel de l'opération en cours visible |
| Quota absent | Connecteur ne fournit pas sa limite | Affichage inconnu, aucune estimation présentée comme mesurée |
| Discussion bornée | Atteindre le plafond de contributions | Conclusion ou blocage explicite, aucune boucle sans borne |
| Projection en retard | Interrompre l'indexation après publication | Changement durable conservé, retard visible, reconstruction possible |
| Rafraîchissement | Fermer puis rouvrir HQ | Mission et décisions restaurées depuis le serveur |
| Accessibilité | Réaliser le parcours au clavier et à largeur mobile | Contrôles utilisables, états compréhensibles et aucun contenu essentiel masqué |
| Budget global | Additionner travail, coordination, reprises et évaluations | Limites appliquées à la mission entière ; consommation inconnue signalée |
| Cache et droits | Retirer un accès après mise en cache du contexte | Ancien paquet non réutilisable par l'identité désormais non autorisée |
| Effet externe ambigu | Simuler un délai dépassé sans preuve d'exécution | Réconciliation ou blocage explicite, jamais de répétition aveugle |
| Intérêt du parallélisme | Comparer un puis deux workers sur les mêmes cas | Qualité, durée, consommation et interventions mesurées ; aucun gain présumé |
| Contrat simulé/réel | Appliquer les mêmes cas de commande et d'état aux deux adaptateurs | Mêmes états et erreurs contractuels ; les limites du fournisseur restent visibles |

Mesures à relever : critères réussis, durée jusqu'au résultat validé, tentatives échouées, tokens observés par mission validée, appels outils répétés, conflits résolus et consommation inconnue. Comparer sur les mêmes cas ; fixer les seuils de performance après la première mesure de référence.
