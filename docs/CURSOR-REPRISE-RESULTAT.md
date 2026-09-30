# Reprise Cursor — inspection opérateur

30 septembre 2026. Branche de travail initiale `codex/cursor-recovery-handoff`, commit documentaire `77f9b9e9233cc120fdd5774a21c94481efcd584f`. Base fonctionnelle `59f279260d8ed7db7054867a66d3266e979e86a6`. Branche de livraison `codex/cursor-operator-inspect`. Aucun déploiement, aucun accès VPS, aucun modèle payant, aucun changement de permissions réseau.

Le dépôt compagnon public `Oria.HQ.Michael.HQ-APP` au commit `e9ff840a38b4532b687bb29f3e2371afeeb3024e` n'a pas été mélangé à ce checkout et n'a pas été modifié. Cette livraison ne change pas ses contrats.

## 1. Résultat utilisable

Commande d'inspection, sans modèle et sans écriture :

```sh
python integrations/openhands-runner/operator_status.py
```

Le code 0 signifie qu'un rapport JSON a été produit. Il ne signifie pas qu'une mission est prête. Sur cette machine le rapport indique `readyForRealMission: false`, `docker.daemon: unavailable`, `docker.container: not_observed`, `canonicalState: unknown`, `authenticationVerified: false` et `independentValidationPassed: false`.

La préparation isolée déjà existante reste :

```sh
python integrations/openhands-runner/prepare_job.py --dossier request.json --workspace synthetic-a --executor-version 1.50.0 --source <depot> --jobs-root <racine>
```

La réconciliation qui peut écrire une transition reste `reconcile_launch.py`. L'exécution reste `run_host_job.py` sans `--inspect`.

## 2. Commits et choix

| Repère | Commit | Rôle |
| --- | --- | --- |
| Mandat documentaire | `77f9b9e9233cc120fdd5774a21c94481efcd584f` | Décrit les cinq phases. |
| Base fonctionnelle | `59f279260d8ed7db7054867a66d3266e979e86a6` | Coordination lancement / réconciliation déjà qualifiée par Codex sur un agent synthétique. |
| Livraison | `b12df830ab3cdb9b03fb28cfbfbc987ac7fb6efa` | Inspection portable. |

Fichiers essentiels : `integrations/openhands-runner/operator_status.py`, `integrations/openhands-runner/test_operator_status.py`, `integrations/openhands-runner/OPERATOR-STATUS.md`. Le rapport réutilise `dossier.prepare` et `request_io.read_dossier`. Il ne réimplémente pas le verrou, la réconciliation ni le superviseur.

`run_host_job.py --inspect` reste l'observation root d'un hôte déjà préparé. Elle ne peut pas servir à un checkout sans configuration protégée. La nouvelle commande couvre ce vide sans affaiblir les contrôles root.

## 3. Scénarios réellement exécutés

Environnement : Linux x86_64, utilisateur `ubuntu` sauf mention, Python 3.12.3, Node v22.14.0, Git 2.43.0, `flock` util-linux 2.39.3. Docker : commande absente. `commit.gpgsign` global désactivé pour que les commits de test restent sous la limite de 5 secondes du dépôt ; la signature SSH injectée dépassait parfois 12 secondes.

| Scénario | Commande | Résultat |
| --- | --- | --- |
| Suite hôte, utilisateur courant | `python -m unittest discover -s integrations/openhands-runner -p 'test_*.py'` | 175 tests, 20 ignorés (réservés à root), 0 échec, 0,980 s |
| Suite hôte, root | `sudo python -m unittest discover -s integrations/openhands-runner -p 'test_*.py'` | 175 tests, 0 ignoré, 0 échec, 1,007 s |
| Contrats Antigravity | `node --test integrations/antigravity/runner.test.mjs integrations/antigravity/paperclip-adapter.test.mjs` | 21 réussis |
| Préparation HQ sans réseau | `node --test deploy/hq-pilot/readiness.test.mjs` | 3 réussis |
| Frontière Memex TLS | `node deploy/memex-tls/check-static.mjs` puis `node --test deploy/memex-tls/proxy.test.mjs` | statique réussi, 9 tests réussis |
| Préparation synthétique | `prepare_job.py` sur un dépôt Git jetable | première sortie `prepared`, seconde sortie 3 `preparation_conflict`, aucun modèle |
| Inspection nouvelle | `python integrations/openhands-runner/operator_status.py` | rapport `real_mission_not_ready`, Docker indisponible, conteneur non observé |
| Instantané de développement | `node --test deploy/hq-pilot/development-snapshot.test.mjs` | 4 réussis, 1 échec préexistant : un lien symbolique de répertoire n'est pas refusé |

Les 20 tests ignorés sans root couvrent les chemins protégés (passerelle, permissions de service, publication root). Ils passent dans la suite root ci-dessus. Cette suite root n'est pas une qualification Docker.

Preuves non sensibles de cette session : sorties de tests conservées hors dépôt. Le rapport d'inspection ne contient ni objectif de dossier, ni secret, ni chemin de politique.

## 4. Exécuté, implémenté, bloqué

Exécuté ici : installation idempotente de l'alias `python`, suites unitaires, préparation synthétique, inspection sans effet. Un agent Cloud distinct a revu les outils et la suite d'alors (165 tests, 20 ignorés) plus une préparation synthétique. Cet agent a démarré depuis la construction d'environnement, pas depuis une mission modèle.

Implémenté avant cette reprise, et rejoué seulement par les tests unitaires : verrou `flock`, refus de clôturer une absence Docker ambiguë, reprise d'identité, courses à barrière. Ces tests ne parlent pas au démon Docker.

Implémenté par cette reprise : le rapport d'inspection et ses contrôles d'effet.

Bloqué : Docker n'est pas installé. Les qualifications `qualify_*.py`, le redémarrage PostgreSQL et le parcours `--interrupted-run --reconcile` n'ont pas été relancés. L'authentification fournisseur n'a pas été vérifiée. `independentValidationPassed` reste faux. Le compte rendu Codex du 30 septembre décrit un agent synthétique sur un autre hôte ; il n'est pas une observation de cette machine.

## 5. Mesures et prochaine action

| Mesure | Valeur | Lecture |
| --- | --- | --- |
| Suite hôte avant désactivation de la signature Git | 165 tests, 3 à 7 erreurs de délai, environ 52–56 s | Le signataire SSH injecté bloquait `git commit` au-delà de 5 s. |
| Même suite après `commit.gpgsign=false` | 165 tests, 20 ignorés, 11,833 s puis 0,980 s une fois le cache chaud | Le délai venait de la signature, pas du code de coordination. |
| Suite avec l'inspection | 175 tests, 0,980 s (ubuntu) et 1,007 s (root) | Dix tests d'inspection ajoutés. Aucun test existant retiré. |
| Préparation synthétique | exit 0 puis exit 3 | Conflit de destination, travail conservé. |

Prochaine action minimale vers une mission avec modèle : sur un hôte où `docker info` répond, exécuter la qualification connectée déjà écrite, avec un compte fournisseur distinct de ce rapport, puis relire `authenticationVerified`. Ne pas traiter le rapport d'inspection ni l'agent synthétique comme cette mission.

## 6. Limites

L'inspection ne prend pas le verrou et ne crée pas `launch.lock`. Elle ne lit pas le store canonique : l'état reste `unknown`. Un démon Docker absent n'autorise aucune conclusion sur un conteneur. Le test d'instantané de développement qui échoue n'est pas corrigé ici ; le classement des liens symboliques de répertoire reste un écart séparé.

AgentMemory n'est pas accessible depuis cet environnement et n'est pas utilisé comme mémoire de production.
