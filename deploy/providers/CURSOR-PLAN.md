# Cursor runner — revue du 2026-09-29

Préparation seulement : aucun installateur exécuté, aucun VPS modifié, aucune authentification inspectée. Source Paperclip examinée au commit `29c8fb0b66cb01167f71e7107a89628e36b5e032` dans `C:/Users/micha/.agentmemory/knowledge-packs/import-2026-09-29/repos/paperclipai--paperclip`.

## Décision proposée

Conserver l'image Paperclip attestée. Ajouter un runner Linux persistant distinct, joint par l'environnement SSH natif de Paperclip et l'adaptateur `cursor`. Installer Cursor dans ce runner uniquement. Un simple `command: ssh ...` ne reproduit pas le contrat workspace/session/transport de Paperclip.

Runner : utilisateur nonroot dédié, HOME persistant privé `/home/cursor`, workspace dédié `/workspaces/cursor-pilot`, binaire root-owned en lecture seule sous `/opt/cursor-agent/2026.09.28-64d2043/`. Limites initiales proposées : 1 CPU, 2 GiB, 256 PID, une exécution à la fois. Aucun socket Docker, aucun montage `/paperclip`, PostgreSQL, `.env` pilote ou HOME hôte. Aucun port public. Garder les credentials Cursor séparés des worktrees et des autres providers.

Créer un réseau privé de contrôle partagé seulement entre Paperclip et runner, distinct du réseau DB. Le runner a sa propre sortie Internet ; Paperclip et PostgreSQL conservent leur réseau interne. SSH accessible seulement depuis le contrôle. Désactiver forwarding SSH, root/password login et agent forwarding ; vérifier la clé hôte. Les credentials accessibles au processus Cursor restent accessibles à son utilisateur : le conteneur constitue ici la frontière utile, les permissions CLI seules ne suffisent pas.

## Installation et identité officielles

[Installation](https://cursor.com/docs/cli/installation) : CLI Linux disponible, commande `agent`, `agent --version`; mise à jour automatique par défaut. Ne pas confondre Cursor Desktop et CLI.

[Installateur officiel examiné](https://cursor.com/install) : version incorporée `2026.09.28-64d2043`, Linux x64/arm64, archive Linux x64 `https://downloads.cursor.com/lab/2026.09.28-64d2043/linux/x64/agent-cli-package.tar.gz`. Installe normalement sous `~/.local/share/cursor-agent/versions/<version>` et expose `~/.local/bin/agent` + alias `cursor-agent`. Aucun sélecteur de version observé dans ce script. Pour un build reproductible : télécharger cette archive versionnée, examiner son contenu, relever/verrouiller SHA256 puis construire une image runner avec ce hash exigé et son digest final enregistré. Aucun hash Cursor n'a encore été obtenu/vérifié ; une URL versionnée seule ne garantit pas l'immuabilité. Éviter le `curl | bash` mutable au démarrage. Binaire en lecture seule et contrôle `--version` avant/après chaque essai ; comportement de l'auto-update à valider sans inventer de variable de désactivation.

[Authentification](https://cursor.com/docs/cli/reference/authentication) : `NO_OPEN_BROWSER=1 agent login` affiche un lien que le propriétaire ouvre lui-même. `agent status` vérifie l'état ; ne pas diffuser sa sortie contenant l'identité. Alternative automation officielle : `CURSOR_API_KEY`, jamais argument `--api-key` dans l'historique/process list. Le login utilise le compte Cursor ; les droits/quotas réels devront être confirmés sur ce compte, aucune gratuité ou mutualisation de tokens promise.

La documentation indique stockage local des credentials sans en garantir le fichier exact. [Configuration](https://cursor.com/docs/cli/reference/configuration) documente `~/.cursor/cli-config.json`, `CURSOR_CONFIG_DIR` et `XDG_CONFIG_HOME`, mais ce fichier de configuration n'est pas une preuve d'emplacement des tokens. Persister le HOME dédié entier avec accès privé puis vérifier une reconnexion après recréation du runner ; ne pas copier les credentials du desktop ni les publier dans les logs.

## Contrat Paperclip observé

- `packages/adapters/cursor-local/src/index.ts:1` : type réel `cursor`, modèle par défaut `auto`; son installation sandbox utilise actuellement le script mutable officiel.
- `packages/adapters/cursor-local/src/server/execute.ts:203` : `config.command` défaut `agent`, `model`, `mode`, `cwd`, `env`, `timeoutSec`, `graceSec`, `extraArgs` (ou `args`). Pour notre runner préinstallé : commande absolue `/opt/cursor-agent/2026.09.28-64d2043/cursor-agent`, timeout initial 180 secondes, grace 20, modèle explicite seulement après découverte des modèles du compte.
- `packages/shared/src/types/environment.ts:14` : environnement SSH `host`, `port`, `username`, `remoteWorkspacePath`, `privateKey`, `privateKeySecretRef`, `knownHosts`, `strictHostKeyChecking`. Utiliser la référence de secret Paperclip pour la clé dédiée, `privateKey: null`, clé hôte vérifiée et strict checking true. Ne pas mettre une clé dans la documentation ou le JSON versionné.
- `server/src/services/environment-execution-target.ts:631` transforme cet environnement en cible `kind: remote`, `transport: ssh`, avec `remoteCwd` de lease ou workspace. Lier l'environnement à l'agent via les mécanismes Environment/lease de la version déployée ; ne pas inventer un champ `remoteExecution` dans adapterConfig.
- `packages/adapters/cursor-local/src/server/remote-command.ts` : la découverte automatique `~/.local/bin` concerne les sandboxes, pas SSH. La commande absolue évite ce décalage.
- `execute.ts:606` : lance `-p --output-format stream-json --workspace ...`, reprend avec `--resume`, ET ajoute `--yolo` par défaut. Le mode headless n'est donc pas readonly. `shared/trust.ts` reconnaît `--trust`, `--yolo`, `-f`, `--trust=...` mais n'offre pas un interrupteur readonly simple. Première validation via CLI directe sans force, puis tâche Paperclip uniquement dans un dépôt jetable sans droits de publication. [Headless officiel](https://cursor.com/docs/cli/headless) distingue proposition et modification avec force/yolo.
- `execute.ts:660` transmet l'env explicitement construit ; `adapter-utils/src/execution-target.ts:914` le passe à SSH. `sanitizeRemoteExecutionEnv` retire des identités locales héritées, ce n'est PAS un filtre de secrets : refuser DATABASE_URL, BETTER_AUTH_SECRET et secrets de chiffrement dans adapterConfig.env. Les probes utilisent aussi un environnement fusionné : vérifier par un test canari synthétique que les helpers n'exportent aucun secret avant activation.
- `adapter-utils/src/execution-target.ts:932` rappelle qu'un timeout SSH ne prouve pas l'arrêt du processus distant. Prévoir vérification du processus et borne côté runner avant retry automatique, pour éviter coût doublé et écritures concurrentes.

## Validation à exécuter par l'intégrateur

1. Construire runner distinct avec base et archive verrouillées, enregistrer version/hash/digest ; contrôler montages/réseaux/UID sans afficher les valeurs des secrets.
2. Vérifier commandes et système uniquement, sans prompt fournisseur ; tester refus accès DB, absence des secrets canaris et clé hôte incorrecte refusée.
3. Propriétaire effectue login privé dans le HOME final. Recréer runner et confirmer statut connecté sans afficher son identité.
4. CLI directe : petit prompt lecture seule sur fixture publique sans `--force`, limite de temps ; sortie JSON et quota réel observés.
5. Agent Paperclip `cursor`, environnement SSH dédié, fixture jetable : modification bornée, test local, logs expurgés, session reprise, arrêt timeout confirmé. Vérifier appels Paperclip du runner et workspace sync ; le simple succès SSH ne prouve pas cette intégration.
6. Activer ensuite un projet à la fois, budget et concurrence bornés. Aucun partage de HOME entre Gemini et Cursor ; leur mémoire commune passe par l'interface Memex scoped.

Limites : contrat étudié statiquement, pas de preuve runtime Cursor/SSH/abonnement encore. Ce plan ne modifie ni les services existants ni leurs images. Le runner nécessitera une construction/configuration et une validation séparées avant la première tâche réelle.

## Diagnostic du runner installé : plugins synchronisés

Après installation et login opérateur (gérés séparément), la CLI 2026.09.28-64d2043 initialise des plugins du compte, même avec HOME dédié. Revue locale du bundle installé `/opt/cursor/index.js` et `/opt/cursor/8192.index.js`, sans lecture des credentials :

- Le profil authentifié impose `enableMarketplacePlugins`, `enableFirstPartyPlugins`, `enableUserLocalPlugins` et `enableWorkspaceOpenHook` à true dans `./src/local-agent-profile.ts`.
- Le client marketplace demande `getEffectiveUserPlugins` au backend ; `LocalPluginsService.load()` reçoit ces capacités, pas un champ `enabledPlugins` de cli-config.json. Les occurrences `enabledPlugins` examinées concernent l'import des plugins Claude (`~/.claude/settings.json`), donc ne désactivent pas les plugins Cursor synchronisés.
- `--plugin-dir` ajoute des chemins d'extension au Map existant et les plugins d'extension sont fusionnés avec les plugins de base. Ce flag n'isole pas la liste.
- `--disable-project-configs`, caché dans le help, ignore uniquement `.cursor/cli.json` : ce n'est pas un coupe-circuit de plugins.
- Le profil interne `local-authless` désactive les capacités backend mais change le fournisseur/mode d'authentification ; ce n'est pas une solution validée pour utiliser l'abonnement Cursor existant.

Aucun flag ou paramètre local pris en charge permettant de désactiver tous les plugins Cursor synchronisés n'a été trouvé dans cette version. Renommer le cache n'est pas déterministe : le backend fournit de nouveau les plugins. Ne pas modifier le bundle installé ni les réglages cloud pour contourner ce problème.

Correction MCP locale déjà appliquée sur le runner : `/paperclip/.cursor/projects/workspace/mcp-disabled.json` contient les identifiants simples et qualifiés `plugin-<pluginName>-<serverName>` extraits des manifests présents ; sauvegarde `.before-isolation`. Cette liste n'est pas synchronisée dans le cloud et le loader MCP l'applique. Elle ne désactive pas hooks/LSP.

Dernier smoke unique, ask readonly sans yolo, NODE_OPTIONS retiré : timeout45s, aucune sortie ni réponse. Un nouveau npm log correspond à `typescript-language-server --stdio` ; un hook `session-start` et `corridor` restent lancés malgré l'isolation MCP. Descendants du diagnostic arrêtés, vérification finale : seuls tini/sshd demeurent. Pas de nouvelle inférence après ce constat.

Blocage concret : avant activation d'agents Cursor, obtenir une version offrant un contrôle local complet de plugins, ou une isolation officiellement documentée du chargement backend tout en gardant l'authentification abonnement. Une désactivation account-wide nécessite une décision séparée et affecterait potentiellement le desktop ; elle n'a pas été faite. Les références de source ci-dessus expliquent pourquoi un HOME neuf ou un cache renommé seuls ne résolvent pas ce cas.
