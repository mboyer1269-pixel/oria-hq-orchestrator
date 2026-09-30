# Antigravity — chemin d’intégration vérifié

29 septembre 2026. **Découverte documentaire et revue de code seulement.** Aucun binaire fournisseur téléchargé ou exécuté, aucune installation, authentification ou modification VPS ; aucun appel de modèle. Ce document ne prouve pas une intégration opérationnelle.

## Décision

Utiliser le CLI officiel `agy` dans un runner isolé et prévoir un petit adaptateur Paperclip dédié. Le mode `process` convient à un premier essai ponctuel contrôlé ; il ne suffit pas pour annoncer une intégration complète avec consommation, reprise et résultat validé. Ne pas détourner l’adaptateur Gemini pour Antigravity : les protocoles et l’authentification ne sont pas interchangeables.

## Distribution Linux observée

L’[installation officielle](https://antigravity.google/docs/cli/install/) fournit un CLI natif Linux/macOS/Windows. Sous Linux, destination documentée : `~/.local/bin/agy`. Le [script officiel](https://antigravity.google/cli/install.sh), lu comme texte sans exécution, distingue amd64/arm64 et glibc/musl. Il récupère un manifeste et vérifie SHA512 avant installation ; options disponibles pour éviter les modifications de profil : `--skip-aliases`, `--skip-path`.

Instantané lu directement depuis le [manifeste officiel Linux amd64](https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/linux_amd64.json) :

| Élément | Valeur observée |
|---|---|
| Version CLI | `1.2.13` |
| Archive | `https://storage.googleapis.com/antigravity-public/antigravity-cli/1.2.13-6662628811079680/linux-x64/cli_linux_x64.tar.gz` |
| SHA512 publié | `7a10134a69c575dc11bdc721322344e9db3bf2c9d890f2d40ff0bffda93d39b6ef1c7c486f491d1ddf08b123deef375c7bbe46b62cd3fbc3cc956b1a3bd22956` |

Ce checksum est celui du manifeste, **pas une vérification locale de l’archive**. Avant installation, relever l’architecture réelle, télécharger dans un répertoire de staging, vérifier le digest, puis épingler cette version. Ne pas exécuter directement un script distant non relu. Le binaire natif n’implique pas de dépendance Node déclarée par cette page ; la compatibilité système doit néanmoins être testée. Pour garder l’exécution reproductible, la documentation permet de désactiver l’auto-update avec `AGY_CLI_DISABLE_AUTO_UPDATE=true`. [Dépannage officiel](https://antigravity.google/docs/cli/troubleshooting/)

## Connexion au compte

La documentation décrit un trousseau système et, sur SSH, une URL d’autorisation ouverte localement puis un code saisi dans la session distante. Aucun chemin de fichier de jeton portable n’est établi par les pages consultées : ne pas inventer `auth.json`, copier des profils privés ou assimiler `settings.json` à un secret OAuth. Le mode API Gemini est distinct : `modelProvider=gemini` dans `~/.gemini/antigravity-cli/settings.json` et `GEMINI_API_KEY`. Il ne prouve pas l’utilisation de l’abonnement Google existant. [Installation/authentification](https://antigravity.google/docs/cli/install/)

Sur serveur Linux, le trousseau/D-Bus peut manquer ou être verrouillé. Il faut vérifier la persistance d’authentification sous **le même utilisateur effectif que le runner**, après redémarrage ; ne pas affirmer qu’une connexion desktop suffit. [Dépannage du trousseau](https://antigravity.google/docs/cli/troubleshooting/)

## Protocole exploitable

Le mode `-p` accepte `json` ou `stream-json`. Le JSON expose `conversation_id`, `status`, `response`, `usage` et durée ; le flux NDJSON produit `init`, `step_update`, `result`. La reprise utilise une conversation explicite. En mode entrée streaming, les compteurs sont cumulatifs et les messages de contrôle d’approbation ne sont pas pris en charge. Sans authentification préalable, le mode non interactif échoue. Une permission refusée peut malgré tout laisser une sortie processus zéro : celle-ci ne constitue pas une preuve de tâche réalisée. Préférer des règles de permission ciblées et `--sandbox` ; ne pas ajouter un contournement global. [Mode headless officiel](https://antigravity.google/docs/cli/headless/)

Pour notre adaptateur, conserver le JSON terminal validé, vérifier le statut et les critères de livraison séparément. Transmettre les prompts par stdin structuré lors de l’adaptation complète ; ne pas les concaténer dans une commande shell. Une conversation ne traverse jamais une frontière projet/utilisateur. L’évaluation devra inclure annulation, réponse incomplète, dépassement et redémarrage.

## Revue Paperclip : limites réelles des adaptateurs génériques

Source locale épinglée : `paperclipai--paperclip`, commit `29c8fb0b66cb01167f71e7107a89628e36b5e032`. Aucun adaptateur `agy`/Antigravity trouvé dans les répertoires d’adaptateurs examinés.

| Code inspecté | Comportement constaté | Conséquence |
|---|---|---|
| `server/src/adapters/process/execute.ts` | Lance command/args/cwd ; fournit identité Paperclip et jeton de run ; retourne stdout/stderr et code processus | Peut lancer un wrapper local fixe, mais ne construit pas le prompt depuis `ctx.context`, ne parse pas le JSON agy, ne remonte pas usage/session |
| `packages/adapter-utils/src/server-utils.ts`, `buildPaperclipEnv` | Fournit agent, company et URL API ; aucun task ID dans cette fonction | Ne pas supposer que le wrapper reçoit automatiquement la mission active ; son entrée doit être définie explicitement |
| `server/src/adapters/http/execute.ts` | Envoie agent/run/context ; HTTP réussi devient code zéro ; corps réponse ignoré | Un service distant seul ne fournirait pas les résultats/consommations par cet adaptateur ; l’abort HTTP ne garantit pas l’arrêt distant |
| `packages/adapter-utils/src/types.ts` | `AdapterExecutionResult` admet usage, `usageBasis`, session, modèle et erreurs | Extension dédiée courte possible avec les contrats existants ; aucune deuxième file nécessaire |

## Réalisation minimale proposée

1. **Préflight sans inférence** : installer la distribution vérifiée dans un runner dédié, relever version/aide, vérifier sandbox, droits et ressources. Authentification utilisateur par le parcours officiel, puis test de persistance. Aucun code du dépôt de référence exécuté sans son audit d’installation.
2. **Premier essai contrôlé** : wrapper local à arguments fixes, répertoire fictif, délai borné ; appel explicite autorisé. Valider résultat agy et une preuve déterministe. Ce jalon peut utiliser `process`, mais son statut affiché reste « essai CLI », sans prétendre mesurer les tokens via Paperclip.
3. **Adaptateur `antigravity_local`** : réutiliser le gestionnaire de processus de Paperclip, injecter un contexte borné issu du run, parser JSON/NDJSON, conserver session par tâche/projet, reporter usage et statut. Épingler les modèles réellement disponibles sur le compte, jamais un nom deviné. Ne pas créer de daemon ou queue concurrente.
4. **Contrat de résultat** : traduire le résultat fournisseur dans `AdapterExecutionResult`. Ne pas inventer coût/quota absents. Tester le comptage de consommation pour empêcher le double comptage lors d’une reprise ; tester l’arrêt du groupe de processus et rejeter une livraison arrivée après annulation.
5. **Validation pilote** : sans droits de production, comparer tâche simple, accès refusé, authentification absente, JSON invalide, timeout, interruption et reprise. Brancher Memex seulement avec son identité/namespace runtime dédié. HQ affiche version, connexion vérifiée, dernière preuve et limites restantes.

Fichiers envisagés dans une implémentation séparée de l’adaptateur : `packages/adapters/antigravity-local/src/server/{execute,parse,test,session}.ts`, types d’adaptateur/registre requis par Paperclip, tests avec faux processus et fixtures. Ces fichiers **ne sont pas créés par ce travail**. Pour une cible distante, réutiliser le mécanisme runner déjà supporté après audit de son contrat ; le simple HTTP générique ne suffit pas.

## Manques avant activation

- Binaire installé et compatible, version réellement exécutée, isolation OS vérifiée.
- Connexion Google du compte voulu et persistance effective du trousseau sur VPS.
- Capacités/quota réellement disponibles pour ce compte ; aucun partage automatique garanti avec Gemini CLI.
- Adaptateur et tests de résultat/arrêt/reprise ; intégration Paperclip non encore exécutée.
- Appel fournisseur borné et preuve de mission avant toute mention « opérationnel » dans HQ.
