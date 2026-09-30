# Raccordement opérateur vers worker fournisseur : résultat

30 septembre 2026. Mandat : `MANDAT-CLAUDE-INTEGRATION.md`. Lot local uniquement,
aucun commit, aucun déploiement, aucun accès nouveau accordé. Revue indépendante
par Codex attendue sur le diff non commité de ce dépôt.

## Problème identifié dans le code réel

Chemin tracé avant modification, de la découverte d'une mission jusqu'à
`run_permission_job` :

1. `consume_pending.main` vers `load_config` (schéma fermé à huit clés) puis
   `discover` (liste bornée de lancements canoniques).
2. `consume_pending.consume` vers `provider_policy.provider_preflight(profil hôte)`.
3. `project_sources.prepare_configured_project` vers `prepare_host_job` : écrit
   `operator.json` avec exactement `lifecycleCommand`, `jobRoot`, `reviewSocket`.
4. `run_host_job.execute_configuration` vers `load_configuration` puis
   `run_permission_job`.
5. `permission_worker.run_permission_job` : relecture canonique, puis
   `provider_gateway` et `container_job.create_job(provider=...)`.

Deux refus structurels, tous deux dans le périmètre du mandat :

- Refus amont. `consume` appelait `provider_preflight(config)` sans second
  argument. Une politique protégée intacte renvoyait quand même
  `unsupported_provider_profile` : aucune configuration opérateur ne pouvait lever
  ce refus, quel que soit le profil approuvé.
- Paramètre manquant. `run_host_job.execute_configuration` appelait
  `run_permission_job(command, job, job_root, review_socket)` sans `gateway_root`.
  Le worker retombait alors sur `provider_preflight` et refusait. Le seul
  `gateway_root` existant venait du harnais de qualification
  (`qualify_hq_postgrest.py --synthetic-provider`), jamais de l'entrée opérateur.
  `run_host_job.py --gateway-root` était et reste réservé à l'inspection.

Le code aval était déjà qualifié et n'avait pas besoin d'être réécrit :
`provider_gateway` (cycle de vie, journal, nettoyage), `container_job` (montages,
identité Docker vivante, réseau `none`) et le partage de deadline existaient déjà.
Le chaînon absent était uniquement le passage de paramètres depuis l'opérateur,
plus l'absence d'un objet « politique approuvée » côté hôte auquel comparer le
profil canonique.

## Changement retenu (un seul)

Un objet optionnel `providerExecution`, absent par défaut, déclaré dans la
configuration racine de l'opérateur et transporté jusqu'au worker :

```json
{
  "profileId": "claude-subscription-v1",
  "policySha256": "<sha256 du policy.json approuvé>",
  "gatewayRoot": "/var/lib/oria-hq/provider-gateways"
}
```

Chaîne complète :

```
consumer.json / operator.json / preparation.json
  consume()                 provider_preflight(config, authorization)
  prepare_host_job()        refus avant toute création de répertoire
  operator.json             providerExecution écrit en 0600, jamais dans le dossier
  execute_configuration()
    run_permission_job(gateway_root=..., authorization=...)
      relecture canonique, authorized_profile, load_provider_policy
      provider_gateway(deadline partagée), create_job(provider=...)
```

Invariants vérifiés dans le code :

- Politique approuvée identique. `authorized_profile` exige que le
  `providerProfile` canonique ait exactement l'`id` et le `policySha256` approuvés,
  en plus de la validation de profil existante et du hachage des quatre artefacts
  protégés. Le contrôle est répété à trois endroits indépendants : consommateur,
  préparation, worker après relecture canonique.
- Identité de mission et de projet. Inchangée : sélection de source, hash de charge
  utile et UUID de lancement conservent leurs contrôles existants. La passerelle
  reste nommée par le lancement canonique.
- Durée commune. Aucun budget nouveau. `provider_gateway` continue de recevoir le
  `deadline_monotonic` que `dispatch` calcule pour la création du conteneur et la
  supervision ; un test vérifie qu'une seule valeur circule.
- Permissions explicites. Inchangées : socket de revue, `PendingPermissions`,
  refus par défaut. Aucun octroi automatique n'a été ajouté.
- Échec visible, pas de relance aveugle. Un profil absent, altéré, incohérent ou
  non autorisé renvoie `invalid_provider_policy` avant tout effet ; une sortie
  incertaine reste `reconciliation_required`. Un test compte les appels et vérifie
  qu'aucune création ni exécution n'est retentée.
- Configuration par défaut inchangée. Sans la clé, les schémas, les refus et les
  paramètres transmis au worker sont identiques à avant. `consumer.example.json`
  n'a pas été modifié.

`gatewayRoot` est un chemin hôte : validé comme réel, absolu, propriété root, non
inscriptible par groupe ou autres, et interdit de partager un sous-arbre avec
`jobRoot` ou le répertoire de contrôle. Il n'apparaît ni dans le dossier, ni dans
le fichier de cycle de vie, ni dans une charge utile navigateur. Aucun chemin de
passerelle venant d'`argv` ne peut atteindre l'exécution : `--gateway-root` reste
strictement réservé à `--inspect`.

## Fichiers modifiés

Source, tous dans `integrations/openhands-runner/` :

- `provider_policy.py` : `validate_authorization`, `authorized_profile`,
  `provider_preflight(config, authorization=None)`.
- `permission_worker.py` : paramètre `authorization`, liaison avant toute socket,
  transition ou effet Docker.
- `run_host_job.py` : clé optionnelle dans le schéma, validation des chemins,
  quadruplet de retour, transmission au worker.
- `prepare_host_job.py` : refus avant effet, écriture de l'autorisation dans
  `operator.json` en mode 0600.
- `project_sources.py` : passage dans les deux chemins de préparation.
- `consume_pending.py` : clé optionnelle, validation des chemins, préflight
  autorisé, passage à la préparation.

Tests : `test_provider_policy.py`, `test_permission_worker.py`,
`test_run_host_job.py`, `test_provider_profile_consumer.py`,
`test_prepare_service_permissions.py` adaptés et étendus ;
`test_prepare_provider_authorization.py` ajouté pour l'invariant de refus au
moment de la préparation.

Documentation corrigée parce que ses affirmations devenaient fausses :
`HOST-ENTRY.md`, `HOST-CONSUMER.md`, `PROVIDER-POLICY.md`,
`PROVIDER-INTEGRATION-GAPS.md`, `SHARED-DEADLINE.md`.

Aucune modification dans `C:/Users/micha/Dev/Oria.HQ` ni dans
`C:/Users/micha/Documents/memex-core`. Aucun fichier de compte, de session ou de
secret lu, copié ou écrit.

## Commandes et résultats

Poste Windows, Python 3.14, tests simulés uniquement.

```
python -m unittest discover -s integrations/openhands-runner
```

- Avant le changement : `Ran 124 tests ... OK (skipped=22)`.
- Après le changement : `Ran 137 tests ... OK (skipped=23)`.

Runs ciblés : `-p "test_p*.py"` donne 54 tests, OK, 18 sautés ;
`-p "test_run_host_job.py"` donne 5 tests, OK, 1 sauté.

Nature des preuves, à ne pas confondre :

- Fait établi ici. Le contrat de configuration, le passage de paramètres et les
  refus se comportent comme décrits, sous tests simulés Windows.
- Non rejoué. Les 23 tests sautés sont les tests Linux root : permissions réelles,
  liens symboliques, modes de fichiers, et les deux assertions nouvelles qui
  dépendent de chemins protégés (`operator.json` portant l'autorisation, refus
  d'un `gatewayRoot` partageant un sous-arbre avec le job ou le contrôle). Ils
  doivent être exécutés sur le VPS avant toute conclusion.
- Non exécuté. Aucun conteneur, aucun Docker, aucun proxy, aucun réseau, aucun
  compte, aucun appel de modèle. `qualify_hq_postgrest.py` n'a pas été relancé :
  il n'a pas été modifié, mais sa preuve Linux antérieure ne couvre pas ce
  nouveau paramètre.

## Limites

- Ceci lève un obstacle de configuration, pas le verrou d'authentification. Une
  politique vérifiée et approuvée ne monte aucun identifiant, n'authentifie pas le
  CLI, ne prouve pas les réglages de connecteurs de compte et ne qualifie pas la
  revue d'outils. La liste 1 à 6 de `PROVIDER-INTEGRATION-GAPS.md` reste valable.
- Ce code n'est pas installé sur le VPS. Le service consommateur installé ne
  contient pas cette clé et refuse toujours tout profil.
- `run_permission_job` accepte encore `gateway_root` sans `authorization` : c'est
  le contrat historique du harnais de qualification. Aucun chemin produit ne
  l'emprunte, mais l'invariant n'est pas rendu obligatoire au niveau du worker.
  Le rendre obligatoire invaliderait une preuve Linux que je ne peux pas rejouer
  ici ; c'est une décision à prendre avec la prochaine exécution VPS.
- `run_host_job.py --inspect --gateway-root` ne vérifie pas la cohérence avec le
  `gatewayRoot` configuré. Sans impact sur l'exécution, à resserrer si la revue le
  demande.
- Changement de comportement à signaler : `project_sources.py --config` refuse
  désormais une mission porteuse de profil sans autorisation explicite, au lieu de
  préparer un travail que le worker aurait refusé ensuite. Aucun répertoire n'est
  créé dans ce cas, donc aucune dette de réconciliation.
- Aucune affirmation de performance, de coût ou d'absence de défaut. Les coûts
  inconnus restent inconnus.

## Prochain blocage concret

Le premier blocage est une autorisation, pas du code : il n'existe aucun
`/etc/oria-hq/provider-policies/<id>/policy.json` approuvé en production, et le
consentement OAuth du compte fournisseur sur le VPS reste en attente. Sans ces
deux éléments, `providerExecution` ne peut nommer aucune politique réelle.

Séquence minimale ensuite, dans cet ordre :

1. Exécuter la suite hôte sur le VPS Linux sans exclusion, pour couvrir les 23
   tests sautés ici. C'est faisable sans nouvel accès.
2. Décider si `authorization` devient obligatoire dès que `gateway_root` est
   fourni, puis rejouer `qualify_hq_postgrest.py --synthetic-provider` si oui.
3. Obtenir l'octroi explicite de compte et vérifier la connexion Claude
   officielle, puis qualifier le stockage et le rafraîchissement d'identifiants
   dans le CLI épinglé. Sans cela, l'exécution fournisseur reste inatteignable
   même avec un profil autorisé.

Ce lot s'arrête ici : le raccordement demandé est livré et testé, la suite exige
des autorisations que cette délégation n'accorde pas.

## Suite

Codex a revu ce lot et exécuté les 139 tests sur Linux sans exclusion. Le mandat
suivant (`MANDAT-CLAUDE-PREUVE-OPERATEUR.md`) a corrigé les invariants restants
et ajouté `policyRoot` à l'objet `providerExecution`, qui compte donc quatre
champs et non trois. Le contrat à jour et les preuves connectées sont dans
`CLAUDE-PREUVE-OPERATEUR-RESULTAT.md`.
