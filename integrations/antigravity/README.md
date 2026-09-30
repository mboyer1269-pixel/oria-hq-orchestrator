# Antigravity planning adapter

Integration Node ESM pour un runner SSH isolé. Non enregistrée et non activée dans Paperclip. Aucun téléchargement, login ou appel fournisseur à l'import. Le mode exposé produit un plan ; une réponse SUCCESS ne prouve pas la livraison d'une application.

## Contrat final

`createServerAdapter()` fournit le contrat external-adapter Paperclip. Pour être exécutable, sa factory exige des bindings hôte hors configuration agent :

- `loadTransport()` : par défaut importe `@paperclipai/adapter-utils/execution-target` et son export `runAdapterExecutionTargetProcess(runId,target,command,args,options)`.
- `renderTask(ctx)` : compose le prompt à partir du contexte de mission. Le contexte upstream ne garantit pas un champ `context.prompt` universel ; ce champ sert seulement dans les fixtures.
- `stopAndVerify(ctx)` : arrête et vérifie le runner exclusivement assigné au run, puis retourne `{stopped:true, scope:'exclusive_runner', runId:ctx.runId, environmentId:ctx.executionTarget.environmentId}`. Reçu absent, faux, rejeté ou portant une autre identité interdit le succès. Une sortie SSH seule ne constitue pas cette preuve.

Le contexte hôte doit porter une cible `kind:remote`, `transport:ssh`, un environmentId, knownHosts et strictHostKeyChecking, avec remoteCwd `/workspace`. Config exige `qualifiedRemoteRunner:true`. Ces conditions expriment une qualification opérateur, pas une permission d'activation accordée par le modèle. Le callback upstream `stopRemoteStartup` n'est pas utilisé : dans le commit examiné, il est réservé aux sandboxes annulées et retourne void.

Le loader externe upstream appelle la factory sans paramètres. L'intégration des bindings hôte reste donc nécessaire avant une activation native ; le loader par défaut refuse l'exécution. Le package adapter-utils expose bien le sous-chemin utilisé, mais sa résolution dans l'installation hôte doit encore être testée.

## Exécution isolée

Monter cette intégration readonly dans `/opt/oria-antigravity`, le binaire dans `/opt/antigravity/antigravity`, le HOME fournisseur dédié dans `/paperclip`, le workspace dans `/workspace`. Aucun socket Docker, volume DB, HOME application ou credential Paperclip ne doit être monté dans le runner. Une seule exécution par runner est nécessaire pour que l'arrêt vérifié ne touche aucun autre run.

Commande fixe : `/bin/sh /opt/oria-runner/bounded-command.sh <watchdog-seconds> node /opt/oria-antigravity/remote-entry.mjs`. JSON stdin transporte seulement `runId`, `prompt`, `timeoutMs`. L'environnement transmis est limité à HOME. Le wrapper est maintenu dans deploy/providers/runner ; il n'est pas choisi par le contenu de la tâche.

Pour un délai fournisseur T (1 à 300 secondes), watchdog = ceil(T)+3 secondes avec escalade KILL après 5 secondes ; transport SSH = ceil(T)+10 secondes. Le runner applique aussi son délai propre. Toute sortie, y compris heureuse, exige ensuite le reçu hôte. Aucun retry automatique, reprise de session ou autorisation de replay n'est émis. Les descendants détachés échappant au groupe de processus justifient la vérification de runner indépendante.

## Protocole fournisseur

Le runner envoie une seule entrée JSON `user/message.content`, avec flags fixes plan, sandbox, streaming et délai. Les prompts comprenant une ligne commençant par slash sont refusés. Le flag disable-slash-commands n'est pas utilisé : la version testée signale qu'il rend plan inopérant.

Le parseur attend init, step_update, result ; vérifie session, permission init request-review, succès terminal unique et compteurs. Toute sortie stderr est refusée, car un refus de permission peut accompagner un exit zéro. Les buffers sont bornés ; les diagnostics bruts ne sont pas rendus dans le résultat. Le champ permission seul ne prouve pas le confinement.

Usage absent signifie inconnu, jamais zéro. Les compteurs validés sont par run frais ; le coût reste null. La réponse est marquée deliveryVerified:false et nécessite un vérificateur indépendant avant livraison.

Source officielle : [headless Antigravity](https://antigravity.google/docs/cli/headless/). Référence Paperclip examinée readonly : commit `29c8fb0b66cb01167f71e7107a89628e36b5e032` ; contrat contexte dans adapter-utils/src/types.ts et callback sandbox dans server/src/services/heartbeat.ts autour de 24653. Aucun code du dépôt téléchargé exécuté pour cette revue.

## Preuves au 2026-09-29

La CLI agy 1.2.13 a été vérifiée par la tâche principale. Les fixtures observed-json-success.json et observed-stream-success.ndjson proviennent de smokes réels ; UUID anonymisés et stream réduit, pas une capture intégrale. La tâche principale a aussi exécuté runAntigravity dans un conteneur isolé avec HOME persistant sans DBus/socket hôte : succès streaming validé, sans diagnostic stderr.

Dernière qualification réelle rapportée par la tâche principale : appel SSH de remote-entry réussi avec réponse `ORIA_AGY_SSH_OK`, 13 803 tokens entrée, 294 sortie dont 286 thinking, total 14 097, durée fournisseur 4,521 secondes. Ce coût en tokens pour une réponse minimale impose un benchmark avant usage régulier.

Vérifications runtime distinctes : watchdog 1 seconde sur sleep20 termine exit124 avec enfant absent ; clé hôte inconnue refusée exit255 ; docker stop donne Running=false et PID=0, puis runner redémarré. Ces preuves ne valident ni la factory native Paperclip ni une annulation pendant une génération modèle active.

Tests locaux : `node --test integrations/antigravity/runner.test.mjs integrations/antigravity/paperclip-adapter.test.mjs` : 21 réussis. Ils couvrent protocole, limites, diagnostics, annulation locale, environnement SSH minimal, contexte non qualifié, transport perdu, timeout, reçus d'arrêt absents/faux/mauvais run/rejetés et succès parsé. Les doubles de transport ne font aucun appel réseau/modèle.

## Restant avant activation

La revue du commit Paperclip épinglé a aussi confirmé une liste fermée dans `packages/shared/src/environment-support.ts:67–80` : notre type externe n'est pas éligible aux cibles SSH/sandbox natives. Le refus est appliqué par `server/src/services/environment-execution-target.ts`. La factory seule ne suffit donc pas. Il faut un correctif explicite de prise en charge des adaptateurs distants et de leur cycle de vie, ou une future version amont qui offre ce contrat ; ne pas activer en détournant le nom d'un adaptateur intégré.

Intégrer les bindings loader hôte et tester la factory native complète ; qualifier annulation en génération réelle, confinement workspace et ressources, refus de permission, puis budget/qualité. L'autorisation du board et l'enregistrement d'un agent restent des étapes séparées. Aucun test synthétique, succès SSH ou reçu construit par un mock ne remplace ces validations.
