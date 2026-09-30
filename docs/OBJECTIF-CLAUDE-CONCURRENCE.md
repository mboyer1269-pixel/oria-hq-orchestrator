# Objectif bloquant : coordonner lancement et réconciliation

La revue confirme 161 tests Linux et les trois corrections précédentes. Le défaut restant est documenté : la réconciliation peut enregistrer cancelled alors qu'un processus autorisé est encore susceptible de créer ou démarrer le conteneur. Une observation après écriture n'annule pas l'état erroné. Ce défaut doit être résolu avant toute mission réelle.

## Résultat obligatoire

Coordonner les chemins de lancement et de réconciliation sur un même lancement : aucune clôture ne peut être confirmée tandis qu'un exécutant peut encore effectuer un démarrage autorisé. Une clôture confirmée interdit tout démarrage tardif provenant d'une ancienne exécution. Une réponse perdue ou un crash ne doit pas laisser un verrou indéfiniment bloquant ni permettre une reprise concurrente aveugle.

Choisir la solution minimale compatible avec le déploiement réel après inspection des processus et contrats. Un verrou uniquement dans le processus Python, une temporisation ou une nouvelle observation seule ne suffisent pas. Un verrou interprocessus ou mécanisme de fencing doit couvrir réellement tous les chemins concernés, y compris les effets Docker encore en vol. Ne pas présumer qu'un jeton contrôlé seulement par HQ rend Docker atomique.

Autonomie pour inspecter, implémenter et corriger dans Orchestrator et, si nécessaire, les contrats ciblés de Oria.HQ. Conserver les modifications existantes. Réutiliser les primitives présentes et justifier brièvement le choix. Ne pas ajouter de systèmes ou de dépendances sans nécessité.

## Preuves déterministes

Forcer les entrelacements avec des barrières de test contrôlées, pas des sleeps aléatoires : suspension après autorisation avant création, avant démarrage, clôture concurrente et reprise d'un ancien exécutant. Vérifier état canonique ET état/identité Docker. Ajouter un crash du détenteur et deux demandes de réconciliation simultanées. Les assertions doivent échouer sur l'ancienne implémentation. Garder une qualification connectée Linux couvrant le mécanisme réel, puis les contrôles de régression affectés.

Une absence de garantie nécessaire reste un blocage explicitement rapporté, jamais une réussite avec simple avertissement. Préserver les fichiers et preuves ; distinguer résultat récupéré, clôture confirmée et incertitude.

## Limites et livraison

Même périmètre isolé que OBJECTIF-CLAUDE-RECONCILIATION.md : aucun compte, appel modèle, octroi OAuth, changement de service ou de base active, déploiement, publication Git ou suppression de travail utilisateur. Aucun autre agent. Tests SSH dans un nouveau dossier de qualification autorisés. Lire et mettre à jour uniquement la mémoire partagée de développement pertinente.

Livrer docs/CLAUDE-CONCURRENCE-RESULTAT.md avec invariant, mécanisme, entrelacements réellement vérifiés, preuves, limites et commandes. Codex effectue une revue indépendante avant activation. Ne pas prétendre avoir utilisé /goal si cette commande est absente.
