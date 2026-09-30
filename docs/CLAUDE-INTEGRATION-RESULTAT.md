# Qualification intégrée ORIA HQ — résultat

30 septembre 2026. Mandat : `OBJECTIF-CLAUDE-INTEGRATION-AGENTS.md`. Branche
`codex/integrated-qualification` dans un clone isolé. Aucun déploiement, aucun
modèle fournisseur appelé, aucun compte ni permission accordé, aucun checkout
d'un autre agent modifié.

Le rapport du premier mandat qui occupait ce chemin a été renommé
`CLAUDE-RACCORDEMENT-OPERATEUR-RESULTAT.md` ; il n'est pas perdu.

## Résultat concret

Les deux lots revus sont assemblés et la chaîne complète est qualifiée en
connecté : consommateur réel → préparation canonique → entrée opérateur → worker
→ conteneur → résultat conservé → réconciliation, suivie du redémarrage de la
base jetable. Une incompatibilité démontrée entre l'inspection opérateur et le
vrai format de politique est corrigée avec preuves négatives.

Commande d'inspection, lecture seule, sans modèle :

```sh
python3 integrations/openhands-runner/operator_status.py \
  --dossier <request.json> --workspace <id> --executor-version 1.50.0 \
  --source <depot> --jobs-root <racine> --policy-root <registre>
```

Sur le VPS, registre réel qualifié : `connectorConfigured: true`,
`connectorReason: manifest_bytes_match`, `docker.daemon: available` 29.6.1,
`readyForRealMission: false`. Les trois blocages restants sont des
autorisations, pas du code : `provider_authentication`,
`execution_authorization`, `canonical_claim`.

## Sources des lots

| Provenance | Référence | Contenu retenu |
| --- | --- | --- |
| Cursor | `origin/cursor/operator-inspect` à `0d2f8a9b7e5d9f1ddaf46f6d9683e79a88aa71b3` | `operator_status.py`, ses tests, `OPERATOR-STATUS.md`, contournement de signature limité aux fixtures |
| Antigravity | patch figé `C:/Users/micha/AppData/Local/Temp/antigravity-snapshot-review.patch` | `lstat` par composant avant classification, tests liens fichier/répertoire et destination absente |
| HQ compagnon | `C:/Users/micha/Dev/Oria.HQ`, `codex/hq-mission-dossier`, `e9ff840a38b4532b687bb29f3e2371afeeb3024e` | lu en surcouche de qualification, aucun changement requis ni effectué |

Le patch Antigravity a été appliqué après `git apply --check`, pas pris à
l'aveugle. Rien d'autre produit entre-temps par les agents n'a été repris. Le
checkout Antigravity (`/home/michael_/.gemini/antigravity/scratch/...`) n'a été ni
lu en écriture ni modifié ; seule la copie figée du patch a servi.

## Incompatibilité corrigée, reproduite d'abord

Le rapport d'inspection refusait un connecteur réellement configuré.
`operator_status._profile_consistent` exigeait un champ `id` dans
`policy.json`, alors que `provider_policy.validate_manifest` interdit ce champ :
l'identité du profil vient de la configuration canonique HQ et du nom du
répertoire de registre. Reproduit sur les octets réels de la politique déjà
qualifiée, copiés depuis
`/opt/oria-openhands-qualification/provider-policy-check/qualified` :

```
avant : {'directoryPresent': True, 'configured': False,
         'reason': 'connector_identity_not_validated'}
après : {'directoryPresent': True, 'configured': True,
         'reason': 'manifest_bytes_match'}
```

Correction choisie : l'inspecteur appelle `validate_manifest`, le validateur réel,
au lieu de redéfinir le format. Les deux seules valeurs qu'il ne peut pas
connaître viennent de ce qu'il observe — l'identité est le nom du répertoire,
l'image d'exécution est celle du manifeste — donc il prouve une cohérence interne
et l'intégrité des artefacts, jamais un accord avec une configuration canonique
ni un compte authentifié. `provider_policy.py` n'est pas modifié : aucun second
format concurrent n'a été introduit.

Preuves négatives ajoutées, `ConnectorFormatTests` : le champ `id` inventé est
refusé ; un réseau `host`, des connecteurs `enabled`, un transport étranger, une
image proxy non épinglée, des octets non canoniques, un artefact altéré d'un
octet et un nom de répertoire inutilisable comme identité sont tous refusés avec
`connector_identity_not_validated` ; deux profils valides restent ambigus. Chaque
cas vérifie aussi que l'arborescence est inchangée. Les fixtures des tests Cursor
sont passées au format réel plutôt que d'être contournées.

## Deuxième cohérence vérifiée : le vrai format de `prepare_job`

Le mandat demandait de vérifier que l'inspection reconnaît un espace réellement
préparé. Exécuté de bout en bout, pas simulé :

```sh
python3 prepare_job.py --dossier request.json --workspace synthetic-a \
  --executor-version 1.50.0 --source /tmp/oria-coherence/source \
  --jobs-root /tmp/oria-coherence/jobs
python3 operator_status.py --dossier request.json --workspace synthetic-a \
  --executor-version 1.50.0 --source /tmp/oria-coherence/source \
  --jobs-root /tmp/oria-coherence/jobs
```

`prepare_job` a produit `job-061d1074…e73de` avec
`commitSha 494f1146dbce4f09cbb4ac4eb29de7607cb380dd`. L'inspection a répondu
`isolated: true`, `reason: clean_checkout_identity`, même `commitSha`, et a retiré
`isolated_workspace` et `budget` de `missingEvidence`. Aucun faux négatif sur ce
format ; et malgré cet accord elle maintient `readyForRealMission: false`,
`canonicalState: unknown`, `authenticationVerified: false`. Les refus
conservateurs sur Docker incertain sont conservés : `container: not_observed` est
imposé par une assertion du code, une indisponibilité du démon n'est jamais lue
comme une absence de conteneur.

## Course de remplacement de chemin : ce qui est et n'est pas prouvé

Le patch Antigravity ajoute un `lstat` par composant avant classification.
`checkedFile` faisait déjà ce parcours juste avant la lecture, donc l'apport réel
du patch est l'ordre du refus et le traitement `ENOENT` d'un composant
intermédiaire comme `deleted_working_file`. La lecture restait faite par chemin
après une vérification par chemin : un composant remplacé entre les deux aurait
été suivi.

Renforcement ajouté ici : `checkedFile` ouvre désormais le fichier avec
`O_NOFOLLOW`, juge ce descripteur par `fstat` et lit ce descripteur. Le dernier
composant ne peut donc plus être échangé contre un lien entre la vérification et
la lecture. **Les composants répertoires restent vérifiés par chemin** : l'API
synchrone de Node n'expose pas d'`openat` par composant, et le mandat interdit
d'ajouter une dépendance. Cette course plus étroite reste donc ouverte, elle est
commentée dans le code, et un test vert ne la ferme pas. Contexte atténuant, pas
une garantie : la source est un dépôt d'opérateur de confiance et l'export de
développement n'est pas une frontière exposée aux agents.

## Commandes et environnement

Clone isolé : `/home/michael_/oria-integrated-qualification` (WSL Ubuntu-24.04),
branche `codex/integrated-qualification` partie de `0d2f8a9`. Linux x86_64,
Python 3.12.3, Node v20.18.0, Git 2.43.0, `flock` util-linux 2.39.3.

```sh
python3 -m unittest discover -s integrations/openhands-runner -p 'test_*.py'
node --test deploy/hq-pilot/development-snapshot.test.mjs
node --test integrations/antigravity/runner.test.mjs \
            integrations/antigravity/paperclip-adapter.test.mjs
```

| Suite | Environnement | Résultat |
| --- | --- | --- |
| Hôte | WSL, utilisateur `michael_` | 184 tests, 20 ignorés, 0 échec, 2,192 s |
| Hôte | VPS, root, racine jetable | **184 tests, 0 ignoré, 0 échec**, 2,395 s |
| Instantané de développement | WSL | 5 tests, 0 échec |
| Contrats Antigravity | WSL | 21 tests, 0 échec |
| Inspection opérateur | WSL | 19 tests, 0 échec (15 de Cursor + 4 ajoutés) |

Les 20 tests ignorés sous WSL sont les chemins protégés réservés à root. Ils ont
été couverts par l'exécution root sur le VPS, donc **zéro exclusion au total**.

## Capacité Docker : limite réelle, contournée proprement

Docker local est indisponible. Constat exact : Docker Desktop est arrêté, la
distribution `docker-desktop` de WSL est `Stopped`, et dans Ubuntu-24.04 le shim
`/mnt/c/Program Files/Docker/Docker/resources/bin/docker` répond
`The command 'docker' could not be found in this WSL 2 distro`.

Prérequis manquant, à faire une fois par l'utilisateur : démarrer Docker Desktop
puis activer Settings → Resources → WSL integration pour `Ubuntu-24.04`.
Vérification attendue ensuite :

```sh
wsl -d Ubuntu-24.04 -- docker info --format '{{.ServerVersion}}'
```

Conformément au mandat, la qualification connectée a donc utilisé uniquement
l'environnement isolé déjà documenté sur le VPS, dans un nouveau dossier
`/opt/oria-openhands-qualification/integrated-20260930-152805`, jamais les
services actifs. Les 18 conteneurs de service du VPS sont restés en place et
inchangés.

## Preuves connectées : nominal, reprise, répétition, persistance

Agent ACP synthétique, politique jetable, base PostgreSQL/PostgREST jetable,
aucun compte fournisseur, aucun appel modèle. Chaque scénario est suivi du
redémarrage réel de la base jetable.

### Nominal

```
{"nominalOperatorProviderLaunch": true,
 "observed": {"missionContainers": 1, "canonicalState": "execution_finished",
              "consumerExit": 0,
              "missionContainerIds": ["23806e02b6a6…ca4c"]}}
{"actualHostDispatch": true, "outcome": {"state": "execution_finished",
 "containerId": "23806e02b6a6…ca4c",
 "containerName": "hq-openhands-454c4cfc-25a0-44e1-a420-2290dda12b45",
 "process": {"exitCode": 0, "elapsedSeconds": 9.711, "containerStopped": true,
             "deadlineExceeded": false},
 "independentValidationPassed": false}}
{"canonicalContainerIdentityAfterRestart":"23806e02b6a6","identityReplaced":false}
```

L'identité du conteneur est comparée, pas comptée : l'identité rapportée par le
consommateur, celle observée dans Docker et celle relue dans la base après
redémarrage sont la même. `elapsedSeconds` mesure un trajet synthétique, pas une
performance de mission.

### Interruption puis récupération du résultat terminé

Opérateur tué par SIGKILL pendant l'exécution (`consumerExit: -9`), conteneur
laissé finir seul, puis réconciliation réelle.

```
"interrupted": {"canonicalState": "start_requested", "consumerExit": -9,
                "missionContainerIds": ["3921439a73f4…8aec8"]}
{"interruptedRunResultRecovered": true, "observedExitCode": 0,
 "process": {"exitCode": 0, "containerStopped": true, "deadlineExceeded": false},
 "retainedEvidence": {"started": "bound", "outcome": "present"},
 "gatewayRelease": {"journalState": "released"},
 "repeatIsNoOperation": true, "secondContainerCreated": false,
 "reExecuted": false, "independentValidationPassed": false}
{"canonicalContainerIdentityAfterRestart":"3921439a73f4","identityReplaced":false}
```

Le code de sortie enregistré est celui lu sur le conteneur, comparé par assertion
à `observedExitCode`. Aucune réexécution, identité inchangée, passerelle libérée
sur identité vérifiée avec journal conservé.

### Répétition sans nouvelle exécution

Réponse d'un lancement terminé jetée, puis mêmes demandes rejouées.

```
{"lostCompletedResponse": true, "responsePayloadDiscarded": true,
 "recoveredFromDurableStateAndRetainedEvidence": true,
 "entryRefusal": {"state": "reconciliation_required", "automaticRetry": false},
 "entryExit": 2,
 "verdict": {"missionContainerIds": ["525ccb2ea1e8…a6ae"],
             "identitiesUnchanged": true, "reinvocationExit": 0,
             "consumerReportedJobs": 0},
 "resultsUnchanged": true, "newExecutionStarted": false,
 "identityReplaced": false, "businessSuccessClaimed": false}
{"finishedResultReadBackWithoutExecuting": true,
 "canonicalState": "execution_finished",
 "process": {"exitCode": 0, "containerStopped": true, "deadlineExceeded": false},
 "retainedEvidence": {"started": "bound", "outcome": "present"}}
```

L'entrée opérateur refuse en sortie 2, le consommateur sort en 0 sans rapporter de
travail, les fichiers de résultat sont identiques octet pour octet, et la
réconciliation ne pose aucune transition : premier pas `already_final`.

### Nettoyage

Après les trois scénarios : aucun conteneur `hq-openhands-*` ni `hq-provider-*`,
aucun réseau `hq-provider-*`, aucun volume `oria-postgrest-qualification*`, aucun
répertoire temporaire `/root/hq-*`. Une commande Docker au résultat inconnu reste
bloquée sans clôture ni nettoyage : ce comportement est inchangé et couvert par la
suite.

## Phase 3 — prérequis de la première mission réelle

Faits vérifiés, pas supposés.

| Prérequis | État constaté | Comment constaté |
| --- | --- | --- |
| Instance concernée | conteneur `oria-openhands-claude-login` sur le VPS, `Up 13 hours` | `docker ps -a --filter name=oria-openhands-claude-login` |
| Authentification fournisseur | **vérifiée absente** : `loggedIn: false`, `authMethod: "none"`, `statusReadable: true` | `check_claude_login_status.py`, lecture seule, aucun jeton imprimé, aucun modèle appelé |
| Autorisation par profil | contrat présent et exercé ; l'objet `providerExecution` nomme profil, empreinte, registre et racine de passerelle | suites hôte et qualifications connectées |
| Registre de politiques de production | **absent** : `/etc/oria-hq/provider-policies` n'existe pas | `ls` sur le VPS |
| Politique approuvable | format réel validé sur les octets déjà qualifiés | inspection ci-dessus, `manifest_bytes_match` |
| Budget fournisseur | inconnu ; le budget par mission existe dans le contrat (`maxCostCents`, `maxTokens`, `maxIterations`, `timeoutSeconds`) mais aucun plafond de compte n'est observable | lecture du contrat de lancement |
| Périmètre isolé | dossier jetable `integrated-20260930-152805`, réseau agent `none`, aucun port publié | qualifications ci-dessus |

Aucun modèle facturable n'a été lancé et aucun accès n'a été accordé dans ce lot.

### Tâche réelle candidate, prête et vérifiable

`integrations/openhands-runner/fixtures/first-mission-task/` : `window_sums`
oublie la dernière fenêtre. `TASK.md` énonce la consigne, `test_window_sums.py`
est le test indépendant que la mission n'a pas le droit de modifier.

Le défaut est réel et le test le voit, avant toute mission :

```sh
cd integrations/openhands-runner/fixtures/first-mission-task
python3 -m unittest discover -s . -p 'test_window_sums.py'
# FAILED (failures=1)
```

Le chemin isolé accepte déjà cette tâche :

```
prepare_job.py  -> {"status": "prepared", "clean": true,
                    "commitSha": "5b93adfa5f4882e7997d9f7b1e5635e508d3ea7d",
                    "checkout": "/tmp/oria-first-mission/jobs/job-061d1074…e73de"}
operator_status -> readyForRealMission: false, isolated: true,
                   connectorConfigured: true,
                   missingEvidence: ["docker", "provider_authentication",
                                     "execution_authorization", "canonical_claim"]
```

Le dépôt source est resté intact après inspection (`git status --porcelain` vide).
Résultat visible attendu : une ligne changée dans `window_sums.py` et le test
indépendant qui passe, exécuté depuis une copie vierge afin qu'affaiblir le test
ne puisse pas produire un succès.

## Échecs, exclusions et ce qui n'a pas été fait

- `sudo` sans mot de passe n'est pas disponible dans WSL, donc la suite root n'y a
  pas tourné ; elle a tourné sur le VPS en root à la place. Commande tentée :
  `sudo -n python3 -m unittest discover -s integrations/openhands-runner -p 'test_*.py'`.
- Docker local absent (voir ci-dessus) ; aucune installation privilégiée tentée.
- AgentMemory n'était pas joignable pendant cette session : le serveur MCP a été
  retiré de la configuration en cours de route, donc les handoffs
  `2026-09-30-cursor-review` et `2026-09-30-antigravity-efficiency` n'ont pas été
  lus par appel MCP. Je ne remplace pas cela par la lecture d'un fichier du vault.
  Le fait durable est donc consigné dans ce dépôt, pas en mémoire partagée.
- Aucune vérification que le checkout Antigravity WSL est connecté à AgentMemory :
  hors de mon périmètre, et son checkout n'a pas été touché.
- Les 180 tests annoncés par Cursor sont devenus 184 ici : 4 tests d'inspection
  ajoutés. Je n'ai pas rejoué les suites HQ compagnon, aucun changement HQ n'étant
  requis.

## Limites

- Qualification synthétique. L'agent est un adaptateur ACP synthétique ; rien ici
  ne démontre une mission de développement réelle, ni une authentification, ni une
  validation indépendante. `independentValidationPassed` reste faux partout.
- La course de remplacement des composants répertoires du chemin d'export reste
  ouverte, comme expliqué plus haut.
- Le registre de politiques de production est vide : la politique validée ici est
  une copie de qualification, pas une politique approuvée.
- Ce code n'est installé ni dans le runtime hôte actif ni dans le service
  consommateur ; rien n'est fusionné dans `main`, rien n'est poussé.
- Aucune prétention à zéro bogue.

## Prochaine action unique

Connecter le compte fournisseur officiel dans le conteneur
`oria-openhands-claude-login` du VPS, puis reconstater
`loggedIn: true` avec `check_claude_login_status.py`. C'est la seule action
autorisée qui manque : tant que `loggedIn` reste faux, aucune politique réelle ne
peut être approuvée pour `/etc/oria-hq/provider-policies` et la tâche candidate
ne peut pas être exécutée, même si tout le reste du chemin est prouvé.

Cette action demande une autorisation de l'utilisateur et n'est pas accordée par
ce mandat. Codex effectue la revue indépendante avant toute activation.
