# Décision technique : pilote Paperclip derrière HQ

29 septembre 2026. Direction retenue pour le pilote, sous réserve de validation isolée ; aucun Paperclip installé ou lancé.

Revue en lecture seule du code local au commit 29c8fb0b66cb01167f71e7107a89628e36b5e032, après l'inventaire initial. Le dépôt téléchargé reste une référence tant que sa revue et son environnement d'exécution ne sont pas prêts.

## Répartition

HQ conserve l'identité workspace, les intentions et le pilotage. Paperclip possède les issues/sous-tâches, files et exécutions durables. Memex conserve les connaissances. HQ stocke la correspondance mission/issue et les identifiants de commandes nécessaires à la réconciliation, pas une seconde file mutable.

Le moteur actuel de HQ refuse explicitement le live et son magasin d'essais est en mémoire. Ne pas lever ces protections pour donner l'impression d'une exécution réelle.

## Preuves examinées

- Schémas issues et heartbeat_runs : tâches, parenté, exécutions et reprises persistées en PostgreSQL.
- Adaptateur PostgreSQL du dispatcher : transactions et verrouillages pour les transitions de reprise.
- Service issues : clé d'idempotence et verrou transactionnel par company, mais rétention limitée à sept jours.
- Autorisation : frontières company, sessions et clés board. Un projet n'est pas automatiquement une frontière de sécurité équivalente à une company.
- Annulation : route et révocation d'autorité d'écriture, avec commandes de pause d'arbre ; l'arrêt immédiat chez tous les fournisseurs reste à tester.
- Adaptateurs présents : Codex, Claude, Cursor, Gemini, Grok, Hermes. Aucun adaptateur Antigravity trouvé dans les arborescences examinées.

## Conditions concrètes

Le checkout exige Node >=24.11 et pnpm 9.15.4 : runtime dédié, distinct de Node 22 pour HQ/Memex. Il faut un PostgreSQL dédié, un réseau privé, le mode authenticated explicitement activé, un compte d'intégration limité et une correspondance workspace/company. Les clés board expirent après trente jours ; leur renouvellement doit être prévu.

Le CLI choisi doit être connecté dans l'environnement exécutant les tâches. L'abonnement desktop seul ne suffit pas. Commencer par Claude, déjà installé mais déconnecté sur le VPS, puis valider Codex séparément.

L'adaptateur Hermes ajoute automatiquement --yolo. Ne pas l'utiliser pour coder avec les droits de l'hôte : isolation non-root, fichiers et montages limités, ressources bornées. Un worktree Git ne fournit pas cette isolation.

Une création ambiguë doit être réconciliée grâce à la référence persistée ; ne jamais recréer aveuglément une mission après expiration des sept jours d'idempotence.

## Prochain incrément

Client uniquement serveur avec URL fixe, délai et validation des réponses ; binding workspace/company ; lecture d'une issue existante et projection dans le dossier HQ. Ajouter ensuite création idempotente, dispatch et annulation après validation de l'authentification. Un dépôt fictif, un worker, puis deux seulement après mesure.

Ce choix ne valide pas encore la sécurité complète du dépôt, l'authentification des comptes, la reprise réelle ni les quotas. Les sources locales de revue sont les schémas packages/db/src/schema, server/src/services/issues.ts, server/src/modules/run-dispatch/adapters/postgres.ts et packages/adapters/hermes/src/server/execute.ts.
