# Première mission de développement exécutée par HQ

Statut : mandat préparé, pas encore lancé. Une entrée backlog ne constitue pas une exécution. La qualification du runner natif Claude et de l'autorité Paperclip précède le lancement.

## Résultat

Permettre à l'utilisateur de distinguer dans une mission : un transfert reçu par Paperclip, un travail réellement en cours, un résultat à examiner et un blocage. Une demande d'arrêt et un arrêt observé doivent être distincts. La première livraison peut couvrir seulement les états que le connecteur remonte réellement ; aucune animation ne simule un agent actif.

## Entrée du développeur

- Snapshot source explicite de HQ, manifeste de hashes conservé par l'opérateur, aucun historique Git ou fichier de connexion copié.
- Base isolée dans le volume workspace Claude ; nouveau dépôt Git local à cette copie pour mesurer le diff. Aucune écriture sur le checkout canonique ou le déploiement actif.
- Mission et contrats du connecteur seulement ; le reste est chargé à la demande. Pas de copie du dialogue utilisateur complet.
- Agent natif Paperclip avec connexion Claude gérée ; credentials injectés par le chemin natif, jamais inclus dans le mandat ni dans le diff.

## Consignes de tâche

Lire les composants de mission et le contrat Paperclip existants. Identifier les statuts réellement disponibles. Proposer puis implémenter un affichage compact en français : état, dernière observation, prochaine action utile. Un échec de lecture ne doit pas être présenté comme un échec du travail distant. Ne pas déclarer une tâche terminée sur la seule sortie texte du modèle.

Changer seulement les fichiers nécessaires à cette présentation et ses tests. Ne pas installer de framework, modifier l'authentification, ajouter de nouveaux pouvoirs à l'agent, changer la base de données ou déployer. Ne pas faire de commit ou push distant. Si le contrat backend ne permet pas un état, le signaler explicitement au chef au lieu de l'inventer.

Fournir : fichiers modifiés, diff, validations réellement exécutées avec résultats, critères satisfaits et limites. Ne pas répéter tout le mandat. Le chef conserve les identifiants d'exécution et la consommation fournie par le moteur.

## Qualification et limites

Le premier essai du runner précède cette mission fonctionnelle et doit rester petit : lecture d'un fichier de cette copie, modification bornée et preuve de fichier produit. Aucune qualification n'est revendiquée sur un simple salut au modèle. Un seul essai automatique ; échec ou timeout → diagnostic du chef, pas boucle de relance.

Avant chaque lancement : délai strict configuré et testé via le mécanisme natif ; aucun plafond de tokens prétendu si l'adaptateur ne sait pas l'imposer. Quota et consommation inconnus restent affichés inconnus. Le scheduler périodique reste désactivé pendant le pilote.

Révision : un second exécutant ou l'agent principal examine le diff et les preuves avant intégration. Tests ciblés, TypeScript/lint et build/smoke prescrits par HQ ; validation navigateur desktop/mobile une fois candidat prêt. Des contrôles verts ne garantissent pas zéro bug.

Reprise : inspecter le run et le diff conservé avant tout nouveau lancement. Réutiliser l'identité de mission ; ne jamais créer une deuxième tâche pour masquer une réponse perdue. Arrêt : demander l'annulation native et vérifier les processus distants ; si seule la demande est confirmée, afficher « arrêt demandé ».

Livraison : appliquer le diff accepté sur la branche prévue, reconstruire et tester le candidat, puis basculer l'instance avec retour arrière disponible. HQ utilisé pour piloter reste séparé de la copie en cours de modification.
