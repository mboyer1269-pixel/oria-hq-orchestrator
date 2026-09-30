# Preuve du parcours opérateur fournisseur — rapport vérifié

30 septembre 2026. Mandat : `MANDAT-CLAUDE-PREUVE-OPERATEUR.md`. Revue :
`REVUE-CLAUDE-PREUVE-OPERATEUR.md`. Diff non commité dans ce dépôt. Adaptateur
ACP synthétique, politique jetable, aucun compte, aucune requête modèle, aucun
service ni base active modifié. Ce document remplace la première version du même
rapport ; les corrections demandées par la revue sont listées telles quelles.

## Corrections appliquées après revue

1. **Code de sortie de la réinvocation vérifié explicitement.** Une sortie vide
   accompagnée d'un échec ne passe plus. `verify_no_second_effect` compare le
   code de sortie à la valeur attendue et conserve la fin de `stderr` dans le
   diagnostic d'échec. Ce dispositif est jetable et sans identifiant.
2. **Identités exactes au lieu de comptages.** Les identités complètes des
   conteneurs mission et passerelle sont capturées avant et après réinvocation
   puis comparées. Côté HQ, `qualify_hq_postgrest.mjs` reçoit l'identité observée
   par l'hôte (`QUALIFICATION_EXPECTED_CONTAINER`) et l'assertionne après
   redémarrage de la base. L'affirmation non appuyée
   `singleCanonicalContainerRetained` est supprimée et remplacée par
   `canonicalContainerIdentityAfterRestart`, qui repose sur cette assertion.
3. **Scénario renommé honnêtement.** `--lost-response` devient
   `--interrupted-start` : il tue le consommateur dès la création du conteneur.
   Il prouve une interruption au démarrage et un refus de relance, pas la
   récupération d'un résultat terminé. La sortie porte désormais
   `interruptedStartRefusesRelaunch` et `finishedResultRecovered: false`.
4. **Qualification distincte ajoutée.** `--lost-completed-response` laisse
   l'exécution se terminer par le vrai parcours, puis supprime uniquement la
   réception de la réponse dans le dispositif de test (`stdout` jeté). L'effet est
   reconstruit depuis l'état durable et les preuves retenues, la même demande est
   réinvoquée, et les identités, l'état durable et l'absence de nouvelle
   exécution sont vérifiés.
5. **Assertion négative ciblée.** `test_qualification_checks.py` prouve que le
   contrôle échoue sur une identité remplacée, un conteneur supplémentaire, une
   disparition d'identité, un consommateur en échec ou du travail rapporté, et
   que la fin de `stderr` est conservée.

## Aucun changement du code produit dans ce lot

Les six modules du parcours opérateur ont exactement les mêmes empreintes
SHA-256 que dans le lot déjà revu par Codex. Ce lot ne touche que le harnais de
qualification, son pendant Node et les tests. Les permissions, la revue d'outils
et les budgets, y compris la deadline partagée, sont inchangés.

## Invariants du parcours opérateur (rappel du lot revu)

Ces trois points étaient l'objet du mandat et restent en place, inchangés :

1. Autorisation obligatoire pour tout parcours fournisseur, harnais compris.
   Sans les deux paramètres, refus hors ligne habituel ; avec un seul, ou avec un
   registre ou une passerelle effectifs différents de ceux de l'autorisation,
   `invalid_provider_policy` avant toute socket, effet Docker ou transition.
2. Prérequis hôte de `policyRoot` et `gatewayRoot` validés dans
   `prepare_host_job` avant le sous-processus de cycle de vie, donc avant tout
   répertoire de lancement.
3. Preuve connectée par le vrai parcours : consommateur réel, préparation
   canonique, entrée opérateur, worker, passerelle, conteneur, état HQ durable.

## Fichiers modifiés dans ce lot

- `integrations/openhands-runner/qualify_hq_postgrest.py` —
  `launch_identities`, `verify_no_second_effect`, modes `--interrupted-start` et
  `--lost-completed-response`, codes de sortie et identités vérifiés, identité
  transmise à la phase de vérification.
- `integrations/openhands-runner/qualify_hq_postgrest.mjs` —
  `QUALIFICATION_INTERRUPTED_START`, assertion d'identité canonique après
  redémarrage, suppression de l'affirmation non appuyée.
- `integrations/openhands-runner/test_qualification_checks.py` — nouveau,
  assertion négative ciblée.
- `integrations/openhands-runner/PROVIDER-POLICY.md` — noms des scénarios.

## Commandes et version des sources

Racine de qualification jetable créée pour ce lot, aucune installation dans la
racine active ni dans le runtime hôte :
`/opt/oria-openhands-qualification/operator-provider-review-20260930-111109`
(sources dans son `openhands-runner/` ; `hq-postgrest`, `lifecycle` et
`provider-policy-check` sont des liens en lecture vers les fixtures épinglées).

```
python3 -m unittest discover -p "test_*.py"
sh run-proof.sh --operator-provider
sh run-proof.sh --interrupted-start
sh run-proof.sh --lost-completed-response
```

Suite hôte : Windows `Ran 142 tests ... OK (skipped=23)` ; VPS Linux
`Ran 142 tests in 1.418s ... OK`, zéro exclusion.

Empreintes SHA-256 identiques entre le dépôt local et la racine VPS au moment
des exécutions. Les six premières sont celles du lot déjà revu :

```
0d028538d2c132d437175e05051647bbb478358f42c2821a262a69c734a4d8ca  consume_pending.py
bcd4ba515dbce6117f769bddd553227df9c30617ea3e7707b841441ee6fec2eb  permission_worker.py
f10ee96ac44281fcea604cab6bb8f89d0d3329fdb091f58977b497c2822879ff  prepare_host_job.py
00c5b30757533b0d423838f6cbed4bc2fd46c47cb9582da38b1f26b057c74734  project_sources.py
8273ce6bb4c6fd8ddc0347c7f6279296d1df6fb111cb408512f75fe36b3893a3  provider_policy.py
81f840034a1c66af43e801106fe163d7fc02b334400b39b2dcb46cd21aadb2a3  run_host_job.py
4d801880169d446511e68f1e0ef105b7793c552997a6e9583992a1e4496303d5  qualify_hq_postgrest.py
de0123147f0cd7a0531e34d3f5b48de6fbf276290ea1fa27b6212cab842ff086  qualify_hq_postgrest.mjs
8ff5c651db03644f92707fbedd9ecefa8cf5a3442416ac523ed03ac020e1e2b6  test_qualification_checks.py
```

## Scénarios observés, distingués

Chaque invocation du harnais crée une mission et un lancement canonique. Les
observations sont des identités Docker par nom déterministe et des lectures
canoniques, pas des déductions d'un test vert. Les identités de conteneur sont
abrégées ici pour la lisibilité ; les valeurs complètes sur 64 caractères sont
dans les sorties des trois invocations, et ce sont elles qui sont comparées.

### A. Politique altérée, refusée avant effet

Présente dans les trois invocations, avant tout autre scénario. Le harnais modifie
`relay.mjs` dans sa copie jetable de la politique, lance le consommateur réel,
puis restaure les octets exacts.

```
{"alteredPolicyRefusedBeforeEffect": true,
 "observed": {"missionContainers": 0, "gatewayContainers": 0,
              "canonicalState": "claimed", "jobDirectory": false,
              "perLaunchBridgeConfig": false, "gatewayDirectory": false,
              "consumerExit": 3},
 "launchStillClaimedAndResumable": true}
```

Sortie 3, `{"state": "invalid_provider_policy", "started": false}`. Aucun
conteneur, aucun répertoire. Le lancement reste `claimed`, donc reprenable.

### B. Lancement nominal par le parcours réel

```
{"nominalOperatorProviderLaunch": true,
 "observed": {"missionContainers": 1, "canonicalState": "execution_finished",
              "consumerExit": 0,
              "missionContainerIds": ["0db3006d467a…6405"],
              "gatewayContainerIds": []}}
{"actualOperatorEntry": true, "repeatRefused": true, "sameContainerRetained": true}
{"actualWorkerGatewayAndHqStore": true, "syntheticAcp": true,
 "providerTlsVerified": true, "foreignHostDenied": true,
 "gatewayClosed": true, "modelRequests": 0}
{"canonicalContainerIdentityAfterRestart": "0db3006d467a", "identityReplaced": false}
```

`exitCode 0`, `containerStopped true`, `deadlineExceeded false`,
`elapsedSeconds 10.011`, `independentValidationPassed false`. Cette durée mesure
un trajet synthétique, pas une performance de mission. L'identité rapportée par
le consommateur est comparée à l'identité Docker observée, puis à l'identité
canonique après redémarrage de la base.

### C. Interruption au démarrage, puis demande identique

Panne injectée uniquement dans le harnais : SIGKILL du consommateur dès que le
conteneur de mission existe. Ce scénario prouve un refus de relance après une
interruption au démarrage ; il ne prouve pas la récupération d'un résultat
terminé (`finishedResultRecovered: false`).

```
"interrupted": {"canonicalState": "container_created", "consumerExit": -9,
                "responseReceived": false,
                "missionContainerIds": ["3004ed84d7e0…85a6"],
                "gatewayContainerIds": ["be79a89ebae1…c66c"]}
```

Effet établi AVANT toute reprise, par le lecteur en lecture seule existant
(`run_host_job.py --inspect --gateway-root`, sortie 0) :

```
"canonicalState": "container_created", "status": "observed",
"gateway": {"journalState": "ready", "containerState": "running",
            "networkState": "present", "attachedContainers": 1,
            "containerId": "be79a89ebae1…c66c", "reconciliationRequired": true},
"automaticRetry": false, "resumeAuthorized": false
```

Demande identique rejouée aux deux niveaux, puis contrôle des identités :

```
"afterIdenticalReplay": {"entryExit": 2, "consumerExit": 0,
                         "consumerReportedJobs": 0,
                         "canonicalState": "container_created",
                         "missionContainerIds": ["3004ed84d7e0…85a6"],
                         "gatewayContainerIds": ["be79a89ebae1…c66c"]}
"verdict": {"identitiesUnchanged": true, "reinvocationExit": 0, "consumerReportedJobs": 0}
```

Entrée opérateur : sortie 2,
`{"state": "reconciliation_required", "automaticRetry": false}`. Consommateur
réinvoqué : sortie 0 vérifiée explicitement, zéro travail rapporté. Identités
mission et passerelle inchangées. Après redémarrage de la base :
`{"interruptedLaunchSurvivedDatabaseRestart": true, "canonicalState":
"container_created"}` et `{"canonicalContainerIdentityAfterRestart":
"3004ed84d7e0", "identityReplaced": false}`.

### D. Réponse perdue après exécution terminée

L'exécution se termine par le vrai parcours ; seule la réception de la réponse
est supprimée dans le dispositif de test. Le consommateur sort en 0, vérifié, mais
son contenu de réponse est jeté : l'effet est reconstruit depuis l'état durable et
les preuves retenues.

```
{"lostCompletedResponse": true, "responsePayloadDiscarded": true,
 "recoveredFromDurableStateAndRetainedEvidence": true,
 "entryRefusal": {"state": "reconciliation_required", "automaticRetry": false},
 "entryExit": 2,
 "verdict": {"missionContainerIds": ["5e5584aa4106…bac2"],
             "gatewayContainerIds": [], "identitiesUnchanged": true,
             "reinvocationExit": 0, "consumerReportedJobs": 0},
 "resultsUnchanged": true, "newExecutionStarted": false,
 "identityReplaced": false, "independentValidationPassed": false,
 "businessSuccessClaimed": false}
```

Reconstruction : `canonicalState execution_finished`, passerelle `absent` /
`absent`, `resumeAuthorized false`, `independentValidationPassed false`, et
`claim.containerId` égal à l'identité Docker observée. Après la demande
identique : état canonique et identité inchangés, `results/outcome.json` et
`results/started.json` identiques octet pour octet, aucune nouvelle exécution.
Après redémarrage : `{"canonicalContainerIdentityAfterRestart": "5e5584aa4106",
"identityReplaced": false}`. Le processus s'est terminé avec `exitCode 0` côté
conteneur ; cela n'est ni une validation indépendante ni un succès métier.

### Le détecteur mord réellement

`test_qualification_checks.py` passe sur Linux (3 tests). Démonstration directe
sur le VPS, avec le même code :

```
DETECTED -> 'replaced mission identity: mission identity changed'
DETECTED -> 'extra mission container: mission identity changed'
DETECTED -> 'failed consumer re-invocation: exit 2 instead of 0
stderr tail:
Traceback (most recent call last)
RuntimeError: synthetic failure'
```

## Ressources et nettoyage

Ressources Docker étiquetées qualification ou nommées par lancement, sans port
publié ni volume opérationnel. Images épinglées réutilisées, dont le runner
`sha256:ecfafc87bc14…`. Vérification après les trois invocations :

```
conteneurs étiquetés qualification        : aucun
conteneurs hq-openhands-* / hq-provider-* : none
réseaux hq-provider-*                     : none
volumes oria-postgrest-qualification*     : none
répertoires temporaires /root/hq-*        : none
```

La racine jetable `operator-provider-review-20260930-111109` reste sur le VPS
pour la revue ; elle ne contient ni identifiant ni donnée réelle et aucun service
ne la référence. Le proxy, la base HQ, les services actifs et le registre
`/etc/oria-hq/provider-policies` n'ont pas été touchés.

## Limites

- Preuve d'un raccordement et de ses refus. ACP synthétique, registre de
  politique jetable, aucun compte, aucune requête modèle.
  `independentValidationPassed` reste faux partout.
- Le registre de production `/etc/oria-hq/provider-policies` reste vide et non
  qualifié ; aucune politique réelle n'existe.
- Ce code n'est pas installé dans le runtime hôte actif ni dans le service
  consommateur installé.
- Un lancement canonique par invocation : les scénarios C et D portent chacun sur
  leur propre lancement. La séquence « refus de politique puis succès sur le même
  lancement » est prouvée ; « succès puis panne sur le même lancement » ne l'est
  pas, et n'a pas de sens ici puisque C interrompt au démarrage.
- Les deux scénarios de panne s'arrêtent à la demande de réconciliation. La
  réconciliation elle-même — décider du sort du conteneur retenu et refermer le
  lancement — n'est pas qualifiée.
- La panne est un SIGKILL du processus opérateur, ou la suppression de la
  réception de sa réponse. Une panne noyau, une coupure d'alimentation, une perte
  réseau ou un `docker kill` concurrent ne sont pas couverts.
- Ces résultats ne rendent pas le produit prêt, ne démontrent aucune
  authentification et ne promettent aucune mission autonome réelle. Les coûts
  inconnus restent inconnus.

## Prochaine action indispensable

Obtenir l'octroi explicite de compte et vérifier la connexion Claude officielle
dans le conteneur d'exécution, puis qualifier le stockage et le rafraîchissement
des identifiants dans le CLI épinglé. Sans cela, aucune politique réelle ne peut
être approuvée pour `/etc/oria-hq/provider-policies` et `providerExecution` ne
peut nommer qu'une politique de qualification. Cette autorisation n'est pas
accordée par la présente délégation.

Ensuite seulement : approuver et installer une politique réelle, reconstruire le
paquet hôte, qualifier la réconciliation d'un lancement interrompu, puis exécuter
une mission de code réelle avec revue indépendante.
