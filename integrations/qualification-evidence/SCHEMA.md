# Schéma `admission-report` version 2

Rapport d'admission du pont. Le validateur lit ce JSON hors ligne. Il ne relance aucune base et ne prouve pas que les commandes ont eu lieu.

`schemaVersion` vaut l'entier `2`. La version 1 est close : elle ne peut plus sortir `reviewable`, parce qu'un identifiant d'assertion seul ne dit pas si l'assertion a réussi.

## Succès explicite

Chaque assertion d'un scénario `real` a `id`, `passed` booléen, `expected` et `observed`. Les deux valeurs sont du même type parmi booléen, entier ou chaîne. `passed` doit valoir `true` et `expected` doit égaler `observed`. Un `passed` faux, une contradiction, un type malformé ou un entier négatif refuse le statut `real`.

Chaque sortie a `expectedExitCode` et `exitCode`, entiers positifs ou nuls, égaux. Le code n'a pas à être 0 : un conflit ou une perte de réponse peut attendre un autre code, à condition qu'il soit celui observé.

## Champs

- `fixtureClass` : `synthetic` ou `collected`. Une fixture synthétique ne peut pas porter un scénario `real`.
- `testedCommit` : quarante caractères hexadécimaux minuscules, le même partout.
- `limits` : liste non vide de limites assumées par l'auteur du rapport.
- `readyForProduction` et `authenticatesExecution` : s'ils valent `true`, le rapport est refusé. Les omettre.
- `database.backendKind` : `postgresql`, `map`, `mock`, `http-in-process` ou `unspecified`.
- `database.engine` : `postgresql` pour un scénario `real`.
- `database.implementation` : `postgresql+postgrest` pour un scénario `real`. Toute mention de `Map` ou de `createServer` refuse `real`.
- `database.selectVersion` : texte observé de `SELECT version()`.
- `database.postgrestVersion` : version observée.
- `database.imageDigests` : au moins un `sha256:` suivi de 64 hexadécimaux.
- `database.migrationsApplied` : noms de fichiers `.sql` réellement appliqués.
- `database.migrationHistoryComplete` : booléen. `false` est honnête si l'historique de production n'est pas complet.
- `database.sqlConstraint.name`, `definition`, `catalogSource`. Pour `real`, `catalogSource` vaut `pg_constraint` et la définition contient UNIQUE, PRIMARY KEY ou EXCLUDE.
- `scenarios` : les six identifiants ci-dessous, une seule fois chacun.

Identifiants : `same_request_concurrent`, `divergent_payload`, `lost_response_after_commit`, `restart`, `protected_identity`, `admission_authorization_execution`.

Chaque scénario a `status` parmi `simulated`, `real`, `not_run`, `failed`, le même `testedCommit`, `assertions`, `outputs` et `limits`.

Pour un statut `real`, chaque sortie a `command`, `expectedExitCode`, `exitCode` et `testedCommit`. Les assertions exigées par scénario, chacune avec succès explicite :

- concurrence : `single_row`, `both_callers_same_row` ; `rowCount` 1 ; `secondExecutionStarted` false.
- payload divergent : `payload_conflict_refused`, `stored_payload_unchanged` ; `secondPayloadStored` false.
- réponse perdue : procédure exactement `commit_then_drop_response_then_replay` ; assertions `committed_before_loss`, `response_dropped_after_commit`, `replay_creates_nothing` ; sorties de phases `commit`, `drop_response`, `replay`. Une procédure ou une phase `lookup` refuse le statut `real`.
- redémarrage : assertions `sql_count_before_restart` et `sql_count_after_restart`, dont `expected` et `observed` sont les comptes entiers égaux ; phases `count_before_restart`, `restart_database`, `count_after_restart`. Un `rowCount` présent doit égaler `observed`.
- identité protégée : `workspace_from_protected_context`, `foreign_workspace_denied` ; `bodyWorkspaceUsed` false.
- admission : `states_observed_separately` ; `stateCounts.admitted`, `authorized` et `executed` entiers ; `admissionMeansExecution` false.

Un champ `verdict` dans le rapport est ignoré. Le validateur calcule le sien.
