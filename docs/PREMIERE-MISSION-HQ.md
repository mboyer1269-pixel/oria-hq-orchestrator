# Première mission de développement exécutée par HQ

Statut : mandat préparé, pas encore lancé. Une entrée backlog ne constitue pas une exécution. Direction courante : Hermes reçoit la directive, HQ conserve la mission et son autorisation, OpenHands réalise la tâche avec le profil fournisseur qualifié. Le runner, le compte et le transport autorisés doivent être prouvés avant lancement. Paperclip n'est pas une dépendance obligatoire de ce parcours; ses références anciennes ne doivent pas réintroduire une deuxième autorité des missions.

## Résultat

Permettre à l'utilisateur de distinguer dans une mission : l'admission par HQ, l'autorisation accordée, le démarrage observé du worker OpenHands, un résultat à examiner et un blocage. Une demande d'arrêt et un arrêt observé doivent être distincts. La première livraison couvre seulement les états que le parcours remonte réellement ; aucune animation ne simule un agent actif. Toute intégration de la nouvelle maquette reste soumise à la validation visuelle de Michael.

## Entrée du développeur

- Snapshot source explicite de HQ, manifeste de hashes conservé par l'opérateur, aucun historique Git ou fichier de connexion copié.
- Base isolée dans le workspace du runner OpenHands ; nouveau dépôt Git local à cette copie pour mesurer le diff. Aucune écriture sur le checkout canonique ou le déploiement actif.
- Mission et contrats du connecteur seulement ; le reste est chargé à la demande. Pas de copie du dialogue utilisateur complet.
- Profil fournisseur explicitement autorisé, identique à celui de la mission canonique. L'identité, le compte et le chemin de connexion doivent être observés et qualifiés; un adaptateur Claude installé ne prouve pas une connexion. Credentials absents du mandat, du snapshot, du diff et des journaux. Aucun repli vers une API payante non autorisée.

## Consignes de tâche

Lire les composants de mission et les contrats HQ/worker existants. Identifier les statuts réellement disponibles. Proposer puis implémenter un affichage compact en français : état, dernière observation, prochaine action utile. Un échec de lecture ne doit pas être présenté comme un échec du travail distant. Ne pas déclarer une tâche terminée sur la seule sortie texte du modèle. Ce travail fonctionnel n'autorise pas l'intégration de la maquette non approuvée.

Changer seulement les fichiers nécessaires à cette présentation et ses tests. Ne pas installer de framework, modifier l'authentification, ajouter de nouveaux pouvoirs à l'agent, changer la base de données ou déployer. Ne pas faire de commit ou push distant. Si le contrat backend ne permet pas un état, le signaler explicitement au chef au lieu de l'inventer.

Fournir : fichiers modifiés, diff, validations réellement exécutées avec résultats, critères satisfaits et limites. Ne pas répéter tout le mandat. Le chef conserve les identifiants d'exécution et la consommation fournie par le moteur.

## Qualification et limites

Le premier essai du runner précède cette mission fonctionnelle et doit rester petit : lecture d'un fichier de cette copie, modification bornée et preuve de fichier produit. Aucune qualification n'est revendiquée sur un simple salut au modèle. Un seul essai automatique ; échec ou timeout → diagnostic du chef, pas boucle de relance.

Avant chaque lancement : délai strict configuré et testé via le mécanisme natif ; aucun plafond de tokens prétendu si l'adaptateur ne sait pas l'imposer. Quota et consommation inconnus restent affichés inconnus. Le scheduler périodique reste désactivé pendant le pilote.

Révision : un second exécutant ou l'agent principal examine le diff et les preuves avant intégration. Tests ciblés, TypeScript/lint et build/smoke prescrits par HQ ; validation navigateur desktop/mobile une fois candidat prêt. Des contrôles verts ne garantissent pas zéro bug.

Reprise : inspecter le run et le diff conservé avant tout nouveau lancement. Réutiliser l'identité de mission ; ne jamais créer une deuxième tâche pour masquer une réponse perdue. Arrêt : demander l'annulation native et vérifier les processus distants ; si seule la demande est confirmée, afficher « arrêt demandé ».

Livraison : appliquer le diff accepté sur la branche prévue, reconstruire et tester le candidat, puis basculer l'instance avec retour arrière disponible. HQ utilisé pour piloter reste séparé de la copie en cours de modification.
