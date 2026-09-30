# Frontière env Cursor/Gemini — 2026-09-29

Décision : la voie SSH native étudiée ne transmet pas automatiquement DATABASE_URL/BETTER_AUTH_SECRET du serveur au processus distant. La voie sandbox transmet en revanche l'environnement serveur fusionné aux probes de résolution de commande. Ne pas généraliser la conclusion SSH aux sandboxes. Revue du commit Paperclip `29c8fb0b66cb01167f71e7107a89628e36b5e032`, aucune donnée réelle utilisée.

## Preuve SSH

`packages/adapters/cursor-local/src/server/execute.ts:249` et `packages/adapters/gemini-local/src/server/execute.ts:273` construisent l'env à partir de `buildPaperclipEnv`, runtimeTools, contexte de tâche et config explicite. `server-utils.ts:3216` ne lit de l'environnement serveur que les adresses/ports nécessaires à l'API, pas un spread de toutes les variables. Le token Paperclip transmis est le token de run fourni par le contexte.

Cursor `execute.ts:660` transmet `env`, Gemini `execute.ts:640` transmet `invocationEnv = buildGeminiHeadlessEnv(env)` (TERM, COLORTERM et NO_BROWSER ajoutés). Aucun spread process.env dans ces arguments d'exécution.

`adapter-utils/src/execution-target.ts:914` applique `sanitizeRemoteExecutionEnv(options.env)` pour SSH. `server-utils.ts:4707` fusionne bien process.env pour le client SSH LOCAL, mais `:4733` passe séparément `remoteEnv: opts.remoteExecution ? opts.env : null`. `resolveSpawnTarget` (`:3620`) fournit uniquement ce remoteEnv à `buildSshSpawnTarget`. L'environnement du processus SSH local n'est pas automatiquement celui du processus distant. Vérifier néanmoins la configuration OpenSSH de l'image : un SendEnv/AcceptEnv personnalisé pourrait créer une autre voie ; aucune garantie globale contre une configuration SSH administrateur n'est donnée ici.

Les runtimeEnv fusionnés de Cursor `:448` et Gemini `:103` ne constituent pas une fuite via les probes SSH : `ensureCommandResolvable` (`server-utils.ts:4655`) vérifie seulement la disponibilité de ssh en local ; `resolveCommandForLogs` renvoie une chaîne descriptive sans commande ; l'installateur runtime (`execution-target.ts:1168`) retourne immédiatement pour SSH.

## Différence sandbox confirmée par le code

`ensureAdapterExecutionTargetCommandResolvable` (`execution-target.ts:713`) applique le sanitizer à l'env fusionné puis `probeSandboxCommandResolvable` (`:737`) envoie cet env au runner. `remote-execution-env.ts` ne retire que des variables d'identité héritées (HOME, PATH, etc.). Les autres clés, dont DATABASE_URL, BETTER_AUTH_SECRET ou un secret tiers arbitraire, sont conservées. Les deux adaptateurs passent runtimeEnv fusionné à cette fonction. Gemini passe aussi runtimeEnv à l'installation sandbox (`execute.ts:342`). Gravité élevée si des sandboxes moins fiables sont activées sur ce serveur ; ce n'est pas la voie SSH proposée.

Correction future recommandée : toutes les opérations distantes (probes, installation et lancement) reçoivent exclusivement env de run explicite. Garder runtimeEnv fusionné pour la résolution locale du client uniquement. Un filtre de quelques noms de secrets ne remplace pas cette séparation. Aucun patch de l'image déployée réalisé ici.

## Conditions d'intégration SSH

- Adapter config.env ne contient que les paramètres approuvés. `refreshPaperclipWorkspaceEnvForExecution` copie les clés non réservées : si l'opérateur configure DATABASE_URL explicitement, elle sera transmise. Le sanitizer n'est pas une protection contre ce cas.
- Runner séparé sans volumes/credentials DB ou HOME serveur ; clé SSH dédiée et knownHosts vérifiés. Lancer via Environment SSH réel, pas l'adaptateur local avec un wrapper arbitraire.
- Contrôler la config SSH effective sans imprimer les secrets et refuser SendEnv sensible ; sur le runner, ne pas accepter les variables serveur inutiles.
- Faire avant premier agent réel un essai end-to-end avec image de contrôle et valeurs canaris seules, qui rapporte uniquement présence/absence de clés. Couvrir version/probe, exécution, reprise et bridge API. Les tokens Paperclip scoped de run/runtimeTools sont attendus, les secrets serveur ne le sont pas.

## Validation disponible et limites

`env-boundary-canary.mjs` est un test offline : lit les sources en texte, vérifie les points de passage puis modélise le filtre avec un environnement entièrement synthétique. Il n'importe/exécute aucun module du dépôt téléchargé, ne lance aucun SSH/provider et ne lit aucun secret. Résultat attendu : SSH explicite sans canaris hérités ; sandbox fusionné conserve les trois canaris ; ajout explicite d'un secret en config n'est pas filtré.

Ce test et la revue prouvent le chemin de données statique examiné, pas une intégration SSH réelle. Dépendances du dépôt importé absentes ; aucune installation ajoutée pour les obtenir. Une preuve runtime synthétique reste requise pour qualifier la configuration effective du déploiement.
