# Réconciliation effective d'un lancement interrompu — résultat

30 septembre 2026. Objectif : `OBJECTIF-CLAUDE-RECONCILIATION.md`. Diff non
commité dans Orchestrator et dans `C:/Users/micha/Dev/Oria.HQ`. Adaptateur ACP
synthétique, politique jetable, aucun compte, aucun appel modèle, aucun service
ni base active modifié. Revue indépendante par Codex attendue.

Note sur les moyens : `/goal` n'existe pas dans cette installation ; l'objectif
est resté explicite dans ce lot, sans prétendre avoir activé une fonctionnalité
absente.

## Corrections appliquées après la revue Codex

`REVUE-RECONCILIATION-CODEX.md` a identifié trois défauts P1 dans le code livré et
une concurrence à éprouver. Les trois sont reproduits, corrigés et couverts par
des preuves négatives ; la concurrence est éprouvée sur le vrai chemin. Aucune
correction n'a touché le contrat HQ : les défauts étaient tous dans la liaison
faite par l'hôte.

### P1-a — identité observée non liée à l'identité canonique

Reproduit tel quel : claim `container_created`/`containerId=A`, conteneur observé
`created`/`containerId=B`, evidence absente → `record_cancelled`, puis
`apply_decision` envoyait A. Un conteneur de remplacement portant les mêmes nom,
étiquettes et image justifiait donc la clôture.

`identity_binding(claim,mission)` est ajouté et évalué en tête de `decide`. Il
renvoie `bound`, `mismatch`, `absent`, `unbound` ou `uncanonical`, et le résultat
accompagne **chaque** décision, y compris `already_final`. Un `mismatch` refuse
toute transition ; passé `creation_requested`, un conteneur que le claim n'a
jamais lié est refusé lui aussi. Seul `creation_requested` peut légitimement
n'avoir aucune identité enregistrée, et c'est le seul cas où
`record_container_created` reste possible.

### P1-b — contrôle des chemins après effets

`main` vérifiait `root.name` et `review.parent.name` **après** `reconcile`, qui
pouvait déjà avoir écrit une transition et supprimé une passerelle. La comparaison
des deux répertoires se fait maintenant avant l'appel, et `reconcile` reçoit
`expect_launch_id` qu'il vérifie juste après sa première lecture canonique, avant
toute décision. Une configuration nommant un autre lancement lève avant tout
effet.

### P1-c — nettoyage permis malgré observation incertaine

`reconcile` n'excluait du nettoyage que `ACTIVE`, donc `unknown` et
`identity_mismatch` pouvaient atteindre `release_gateway` alors que son contrat
exige un agent observé incapable d'agir. Le nettoyage exige désormais une liste
explicite d'états admissibles — `absent`, `created`, `exited`, `dead` — **et** une
identité concordante, évalués sur une ré-observation postérieure aux écritures.
Toute autre observation conserve les ressources et renvoie son motif
(`agent_container_not_releasable` avec l'état observé, ou
`agent_container_identity_mismatch`).

### Concurrence éprouvée

La CAS sur l'état n'ordonne que les enregistrements ; elle ne gèle pas Docker.
Deux mesures, toutes deux démontrées et non affirmées :

- **Sérialisation existante démontrée.** Avec le lancement en `start_requested`,
  la transition réelle `claimed → creation_requested` est refusée par la CAS
  canonique, et `docker create` sur le nom déterministe est refusé par Docker.
  C'est le mécanisme qui empêche une seconde création légitime, pas une enum.
- **Fenêtre observation → écriture fermée par constat.** `reconcile` ré-observe
  après ses écritures et compare état et identité. Si le monde a changé, le
  résultat porte `observation_changed_after_recording`, `canonicalTerminal` repasse
  à faux, le nettoyage est refusé et la prochaine action est donnée. La CAS ne peut
  pas être annulée ; le constat est donc rendu visible au lieu d'être présenté
  comme une réussite.

## Comportement avant

Le parcours s'arrêtait à « interruption détectée, intervention nécessaire ». La
cause était dans le contrat, pas dans l'outillage :

- `launchClaimSchema` autorisait déjà les états terminaux `cancelled`, `failed`,
  `succeeded`, `reconciliation_required`, mais **aucune transition de
  `openhands-lifecycle.ts` ne produisait l'un d'eux**.
- `execution_finished` n'accepte que `expected` dans `start_requested` ou
  `running`. Un lancement interrompu à `creation_requested` ou
  `container_created` était donc un cul-de-sac canonique définitif.
- Rien ne lisait un conteneur arrêté pour récupérer le résultat qu'il avait déjà
  produit ; l'hôte perdait cette information avec son processus.
- Les lots précédents prouvaient le refus de relancer. Ils ne pouvaient ni
  clôturer ni récupérer.

## Comportement après

Trois issues, chacune liée à l'état réellement observé, jamais à une supposition :

| État canonique | Conteneur observé | Enregistré |
|---|---|---|
| `execution_finished`, `cancelled`, `succeeded`, `failed` | quelconque | rien ; preuves retenues relues |
| `claimed` | quelconque | rien ; aucun effet n'existe |
| `creation_requested` | absent | `cancelled`, `interrupted_before_start` |
| `creation_requested` | created | `container_created`, puis clôture au passage suivant |
| `container_created` | absent, created, dead | `cancelled`, `interrupted_before_start` |
| `start_requested`, `running` | exited | `execution_finished` avec le code de sortie observé |
| `start_requested`, `running` | absent, dead | `cancelled`, `result_unrecoverable` |
| toute étape | running, paused, restarting, removing | rien ; motif et prochaine action |
| toute étape | identité différente de celle du claim | rien ; `container_identity_mismatch` |
| toute étape | identité non conforme ou illisible | rien ; motif et prochaine action |

## Décisions et pourquoi

1. **Une seule transition canonique ajoutée, pas un nouvel état.** Les états
   terminaux existaient déjà dans le schéma ; il manquait la transition. Le
   contrat HQ gagne `cancelled` et rien d'autre.
2. **Le contrat contraint la forme et la cohérence, l'hôte contraint la
   fraîcheur.** Correction d'une affirmation trop forte de la première version de
   ce rapport : le champ `observed.containerState` n'accepte que `absent`,
   `created` ou `dead`, ce qui rend certaines observations inexprimables, mais HQ
   n'a aucun accès à Docker et **ne peut pas vérifier qu'une observation est à
   jour**. Un hôte fautif peut soumettre `absent` pendant que le conteneur
   tourne. Ce qui protège réellement : la liaison d'identité et d'état faite par
   le réconciliateur avant toute transition, la CAS canonique sur l'état, le nom
   de conteneur déterministe, et la ré-observation après écriture.
3. **La raison doit correspondre à l'étape.** `interrupted_before_start` n'est
   acceptée que depuis `creation_requested`/`container_created`,
   `result_unrecoverable` que depuis `start_requested`/`running`. Un `created`
   n'est explicable que par la première. Cela empêche de clôturer en
   « irrécupérable » un travail qui n'avait jamais démarré, et inversement.
4. **La clôture porte l'identité exacte du conteneur du claim** (les deux, ou
   aucune). Une preuve appartenant à un autre lancement est rejetée.
5. **La clôture reste possible après expiration de l'autorité**, comme
   `execution_finished` : elle enregistre un effet observé, elle n'en crée pas.
   Créer un effet exige toujours l'autorité courante.
6. **Récupérer plutôt que clôturer quand c'est possible.** Un conteneur démarré
   puis sorti donne son code de sortie réel ; on enregistre
   `execution_finished`, on ne jette pas le résultat.
7. **Rien n'est deviné.** `deadlineExceeded` vient du `startRequestedAt`
   canonique et du `FinishedAt` du conteneur. Un horodatage manquant renvoie
   `deadline_unknown` au lieu d'un résultat inventé ; idem pour un code de sortie
   non entier.
8. **Aucune suppression de travail.** Le commande ne supprime aucun fichier de
   job, checkout, résultat ni dossier. Le seul nettoyage possible est la
   passerelle du lancement, et seulement après terminaison canonique et
   conteneur agent observé inactif, sur des identités vérifiées par étiquette et
   journal. Le journal est conservé et marqué `released`.
9. **Permissions et budgets inchangés.** Aucune modification de la revue
   d'outils, de `permissionPolicy`, de la deadline partagée ni des budgets.

## Fichiers

`C:/Users/micha/Dev/Oria.HQ` (strictement le nécessaire à la persistance) :

- `src/server/missions/openhands-launch.ts` — champ optionnel
  `claim.reconciliation` portant motif, état observé et horodatage.
- `src/server/missions/openhands-lifecycle.ts` — transition `cancelled`, table
  `CLOSURE` liant motif et étape, contrôle d'identité, persistance de la preuve.
- `src/server/missions/openhands-launch.test.mjs` — trois tests ajoutés.

`integrations/openhands-runner/` :

- `reconcile_launch.py` — nouveau. Observation (`observe_mission`,
  `retained_evidence`, `deadline_exceeded`), décision pure (`decide`),
  application bornée (`apply_decision`, `reconcile`) et CLI opérateur.
- `provider_gateway.py` — `write_journal` extrait du contexte existant,
  `release_gateway` et `TERMINAL_LAUNCH_STATES`.
- `hq_transition.py` — passage de la liste blanche `observed`.
- `build_host_release.py` — inclusion de `reconcile_launch.py` dans le paquet.
- `qualify_hq_postgrest.py` / `.mjs` — `--interrupted-run`, `--reconcile`,
  assertions de clôture après redémarrage de la base.
- `test_reconcile_launch.py` — nouveau, table de décision et garde-fous.
- `HOST-ENTRY.md` — documentation de la commande.

## Validations réellement exécutées

Racine de qualification jetable, rien installé dans la racine active ni dans le
runtime hôte : `/opt/oria-openhands-qualification/reconciliation-20260930-120945`
(sources dans `openhands-runner/`, copie réelle des surcouches HQ dans
`lifecycle/`, liens en lecture vers `hq-postgrest` et `provider-policy-check`).

```
node run-tests.mjs                                    # dans Oria.HQ
python3 -m unittest discover -p "test_*.py"           # dans la racine jetable
sh run-proof.sh --interrupted-start --reconcile
sh run-proof.sh --interrupted-run --reconcile
sh run-proof.sh --lost-completed-response --reconcile
sh run-proof.sh --replaced-container
sh run-proof.sh --operator-provider
```

- HQ : `tests 4046 / pass 4042 / fail 0 / skipped 4`, typecheck `tsc --noEmit`
  sans erreur (inchangé : aucun fichier HQ modifié après la revue).
- Hôte : Windows `Ran 161 tests ... OK (skipped=23)` ; VPS Linux
  `Ran 161 tests in 1.407s ... OK`, zéro exclusion.
- Les cinq qualifications connectées ci-dessous passent, chacune suivie du
  redémarrage réel de la base, et toutes rejouées après les corrections.

### 1. Interruption au démarrage : lancement clôturé

Conteneur créé mais jamais démarré, consommateur tué (SIGKILL, sortie -9).

```
"interrupted": {"canonicalState": "container_created", "consumerExit": -9,
                "missionContainerIds": ["95834eec9294…71ca"],
                "gatewayContainerIds": ["f88b250478aa…0f66f"]}
{"interruptedLaunchClosedOnObservedState": true,
 "closure": {"reason": "interrupted_before_start", "containerState": "created",
             "observedAt": "2026-09-30T16:12:11Z"},
 "deliberateStop": false,
 "gatewayRelease": {"attempted": true, "removed": {"container": "4eff40a0437d…",
   "network": "b671ae8559fc…"}, "journalState": "released"},
 "workPreserved": {"checkout": true, "results": true, "dossier.json": true,
                   "operator.json": true},
 "repeatIsNoOperation": true, "secondContainerCreated": false,
 "resultInvented": false}
```

Après redémarrage de la base :
`{"closedLaunchSurvivedDatabaseRestart": true, "canonicalState": "cancelled",
"closure": {"reason": "interrupted_before_start", "containerState": "created"}}`
et `{"canonicalContainerIdentityAfterRestart": "21e9caf0b332",
"identityReplaced": false}`.

### 2. Interruption en cours d'exécution : résultat récupéré

Consommateur tué pendant que le conteneur tournait ; le conteneur termine seul,
sans superviseur et sans relance.

```
"interrupted": {"canonicalState": "start_requested", "consumerExit": -9,
                "missionContainerIds": ["a1a852f87d3c…3947"]}
{"interruptedRunResultRecovered": true, "observedExitCode": 0,
 "process": {"exitCode": 0, "containerStopped": true, "deadlineExceeded": false},
 "retainedEvidence": {"started": "bound", "outcome": "present"},
 "gatewayRelease": {"journalState": "released"},
 "repeatIsNoOperation": true, "secondContainerCreated": false,
 "reExecuted": false, "independentValidationPassed": false}
```

Le code de sortie enregistré est celui lu sur le conteneur, comparé dans
l'assertion. `canonicalContainerIdentityAfterRestart: "a1a852f87d3c"`.

### 3. Résultat déjà terminé, réponse perdue : relu sans exécuter

```
{"finishedResultReadBackWithoutExecuting": true,
 "canonicalState": "execution_finished",
 "process": {"exitCode": 0, "containerStopped": true, "deadlineExceeded": false},
 "retainedEvidence": {"started": "bound", "outcome": "present"},
 "gatewayRelease": {"removed": {"container": null, "network": null},
                    "journalState": "released"},
 "newExecutionStarted": false}
```

Aucune transition n'est appliquée : le premier pas est `already_final`.

### 4. Conteneur remplacé et concurrence : clôture refusée

Lancement en `start_requested`, conteneur d'origine supprimé, remplacé par un
leurre portant le **même nom, les mêmes étiquettes et la même image épinglée**,
avec un identifiant différent.

```
{"replacedContainerRefusedBeforeClosure": true,
 "secondCreationRefusedByCanonicalCas": true,
 "duplicateDeterministicNameRefusedByDocker": true,
 "canonicalContainerId": "438e6a2d7b3c…4684",
 "observedDecoyId":      "e4c98b70c339…0e08",
 "refusal": {"reason": "container_identity_mismatch", "identity": "mismatch",
             "gatewayRelease": {"attempted": false,
                                "reason": "canonical_state_not_terminal"}},
 "workPreservedDuringRefusal": {"checkout": true, "results": true,
                                "dossier.json": true, "operator.json": true},
 "closureAfterRemoval": {"reason": "result_unrecoverable",
                         "containerState": "absent",
                         "observedAt": "2026-09-30T16:32:33Z"},
 "resultInvented": false, "independentValidationPassed": false}
```

Avant la correction, ce leurre aurait justifié une clôture. Désormais : aucune
transition, passerelle conservée, travail conservé, lancement toujours ouvert en
`start_requested`. Après suppression du leurre, plus rien ne prétend être ce
conteneur et la clôture devient légitime — `result_unrecoverable`/`absent`, sans
résultat inventé. Après redémarrage :
`{"closedLaunchSurvivedDatabaseRestart": true, "canonicalState": "cancelled",
"closure": {"reason": "result_unrecoverable", "containerState": "absent"}}` et
`{"canonicalContainerIdentityAfterRestart": "438e6a2d7b3c",
"identityReplaced": false}` — l'identité comparée est celle du claim, pas celle du
leurre.

Les deux premières lignes sont la démonstration demandée du mécanisme de
sérialisation existant : la CAS canonique refuse une seconde création, et le nom
déterministe la refuse aussi au niveau Docker.

### 5. Nominal, non régressé

`{"nominalOperatorProviderLaunch": true, "observed": {"missionContainers": 1,
"canonicalState": "execution_finished", "consumerExit": 0}}` puis
`{"databaseRestartVerified": true}`. Rejoué parce que le harnais a changé, pas
pour répéter une preuve inchangée.

### Preuves négatives des trois défauts

`test_reconcile_launch.py`, classe `NoEffectTests` — chacun de ces cas
reproduisait un défaut réel avant correction, aucun n'écrit désormais :

- `test_a_replacement_container_never_justifies_a_closure_or_a_release` : le cas
  exact de la revue, pour `container_created`, `start_requested`, `running` et
  `creation_requested`, plus un claim terminal. Aucune transition, nettoyage
  refusé en `agent_container_identity_mismatch`, travail conservé.
- `test_a_configuration_naming_another_launch_produces_no_effect` : refus avant
  toute transition, zéro écriture, fichiers conservés.
- `test_an_uncertain_observation_keeps_every_resource` : `unknown` et
  `identity_mismatch` sur un claim terminal ne libèrent rien.
- `test_a_container_appearing_after_the_record_is_reported_not_hidden` : conteneur
  absent à l'observation, présent et en cours après l'écriture — le résultat porte
  `observation_changed_after_recording`, `canonicalTerminal` est faux et le
  nettoyage est refusé.

### Refus vérifiés par tests, pas seulement par narration

`test_reconcile_launch.py` couvre la table complète : conteneur actif jamais
clôturé, identité non conforme refusée, preuve `results/started.json` étrangère
ou illisible bloquant toute transition, horodatage ou code de sortie manquant
refusant l'enregistrement d'un résultat, lancement déjà terminal relu sans
transition, clôture sans identité quand le claim n'en a pas, et release de
passerelle refusée hors état terminal ou sur identité non vérifiée. Côté HQ,
trois tests prouvent que `running`, `paused`, `restarting`, `removing`,
`unknown`, `identity_mismatch` et `exited` sont rejetés par le contrat, que le
motif doit correspondre à l'étape et à l'identité, et qu'un lancement clôturé est
terminal — toute transition de l'ancienne séquence renvoie `conflict`.

## Version des sources

Empreintes SHA-256 identiques entre les dépôts locaux et la racine VPS au moment
des exécutions :

```
b05eed0800c08f75d0be3be3951cc35420b7c3b6d92c5cf549db2502554500e5  reconcile_launch.py
eac8d78f03ff59b598a2ad6d0cb1d7d1b6103ea9722622358789a8a7cf2513a1  provider_gateway.py
5e32a42cc4ef5e10d3a263ab3eddd37d2b097aad09082167f71646d3f175fdb5  hq_transition.py
2e31e7cb226e31e39bff5da396c8c75bc07271167a204ecbaf65cb1fc8500c86  qualify_hq_postgrest.py
b293be5234cd35929aa634945955f129ed0e904ca9a8512030f9159f1292b5b1  qualify_hq_postgrest.mjs
bfe5c68c1ed6bd3549b961a007dfbcee19be36dc8e22a019bd1ee949d500dca2  test_reconcile_launch.py
56a61ff2d2f81a7695d2bd72db9cc845305f1d63ccf043f7ba99c3613b29387c  openhands-lifecycle.ts
e48a3d0299ab67b596684ecab0e6444650e0e96d7d20e6a7804545ffec94fac0  openhands-launch.ts
```

Les deux fichiers HQ sont inchangés depuis la revue : les corrections sont
entièrement côté hôte.

## Ressources nettoyées

Après les quatre qualifications :

```
conteneurs étiquetés hq-postgrest-qualification : aucun
conteneurs hq-openhands-* / hq-provider-*       : none
réseaux hq-provider-*                           : none
volumes oria-postgrest-qualification*           : none
répertoires temporaires /root/hq-*              : none
conteneurs de service actifs                    : 18, inchangés
```

Les passerelles supprimées l'ont été par la commande de réconciliation
elle-même, sur identités vérifiées, et leurs journaux ont été conservés avec
l'état `released`. Les racines jetables restent sur le VPS pour la revue ; elles
ne contiennent ni identifiant ni donnée réelle. `/etc/oria-hq/provider-policies`,
le proxy, la base HQ et les services actifs n'ont pas été touchés.

## Mémoire partagée

AgentMemory-Hub est joignable en lecture-écriture. Contexte lu avant
implémentation (`Agent/handoffs/hq-openhands-*`, sept notes de session Codex ;
aucune note existante ne couvrait la réconciliation). Fait durable consigné :
`Agent/handoffs/hq-openhands-interrupted-launch-reconciliation-2026-09-30.md`,
avec le manque fermé, les garde-fous, les preuves et les limites. Aucun secret,
aucune donnée de production, aucune mémoire runtime écrite.

## Limites

- `independentValidationPassed` reste faux partout. Clôturer ou récupérer un
  lancement n'est jamais une validation du travail produit.
- Les pannes injectées sont un SIGKILL du processus opérateur et un remplacement
  de conteneur par le harnais. Panique noyau, coupure d'alimentation et partition
  réseau ne sont pas qualifiés.
- La fenêtre entre l'observation Docker et l'écriture canonique n'est pas
  supprimée : elle est **constatée après coup**. Si le monde change dans cet
  intervalle, le résultat le signale (`observation_changed_after_recording`) et
  refuse le nettoyage, mais l'enregistrement canonique déjà écrit n'est pas annulé.
  Fermer réellement cette fenêtre demanderait un jeton d'observation vérifié par
  HQ, ce que ce lot n'introduit pas.
- La fraîcheur d'une observation Docker n'est pas vérifiable par HQ, qui n'a pas
  accès à Docker. La protection est côté hôte : liaison d'identité et d'état, CAS
  canonique, nom déterministe, ré-observation. Un hôte délibérément fautif reste
  hors modèle de menace de ce lot.
- Deux passes bornées par invocation : une situation qui demanderait plus d'étapes
  renvoie son motif au lieu de boucler.
- Un lancement canonique par invocation du harnais : les trois scénarios portent
  chacun sur le leur. Le cas `creation_requested` avec conteneur existant
  (enregistrement puis clôture en deux passes) est prouvé par test unitaire, pas
  encore en connecté : la fenêtre entre `docker create` et la CAS canonique est
  trop courte pour être visée de façon fiable par une injection externe.
- Le cas « canonique `start_requested` mais conteneur resté `created` » est un
  cul-de-sac assumé : le contrat refuse de le clôturer, la commande renvoie
  `container_never_started` et demande une suppression délibérée. C'est un motif
  compréhensible, pas une issue automatique.
- Agent synthétique, registre de politique jetable, aucun compte, aucun appel
  modèle. Rien ici ne démontre une mission autonome réelle.
- Ce code n'est pas installé dans le runtime hôte actif ni dans le service
  consommateur installé, et la modification HQ n'est pas déployée.
- Aucune prétention à zéro bogue. Les coûts inconnus restent inconnus.

## Chemin restant vers une mission réelle

1. Revue indépendante de ce diff corrigé par Codex, dans les deux dépôts. Aucune
   activation avant cette revue.
2. Obtenir l'octroi explicite de compte, vérifier la connexion Claude officielle
   dans le conteneur d'exécution, puis qualifier le stockage et le
   rafraîchissement des identifiants dans le CLI épinglé. C'est le blocage
   restant : sans lui, aucune politique réelle ne peut être approuvée pour
   `/etc/oria-hq/provider-policies`.
3. Approuver et installer une politique réelle, reconstruire le paquet hôte avec
   `reconcile_launch.py`, déployer la modification HQ.
4. Exécuter une mission de code réelle, puis la faire réviser indépendamment sur
   ses changements exacts. Le parcours de réconciliation est désormais disponible
   pour cette mission, mais il ne la remplace pas.
