# Reprise Cursor — inspection opérateur

30 septembre 2026. Branche de travail initiale `codex/cursor-recovery-handoff`, commit documentaire `77f9b9e9233cc120fdd5774a21c94481efcd584f`. Base fonctionnelle `59f279260d8ed7db7054867a66d3266e979e86a6`. Branche de livraison `cursor/operator-inspect`. Aucun déploiement, aucun accès VPS, aucun modèle payant, aucun changement de permissions réseau.

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

Environnement : Linux x86_64, utilisateur `ubuntu` sauf mention, Python 3.12.3, Node v22.14.0, Git 2.43.0, `flock` util-linux 2.39.3. Docker : commande absente. `commit.gpgsign` global est revenu à `true`. Les commits de fixtures qui en ont besoin passent `-c commit.gpgsign=false` ; le script d'environnement ne le désactive plus.

Revue des indicateurs, reproduite puis refusée par les tests :

```sh
python -m unittest discover -s integrations/openhands-runner -p 'test_operator_status.py'
```

Un répertoire `job-empty` vide donne `isolated: false` et `reason: empty_job_directory`. Un répertoire de politique vide donne `connectorDirectoryPresent: true` et `connectorConfigured: false`. `readyForRealMission` reste faux même quand le clone et le manifeste concordent, faute de revendication canonique et d'authentification fournisseur.

| Scénario | Commande | Résultat |
| --- | --- | --- |
| Suite hôte, signature Git globale active | `python -m unittest discover -s integrations/openhands-runner -p 'test_*.py'` | 180 tests, 20 ignorés (réservés à root), 0 échec, 1,128 s |
| Même suite, root | `sudo python -m unittest discover -s integrations/openhands-runner -p 'test_*.py'` | 180 tests, 0 ignoré, 0 échec, 1,150 s |
| Faux positifs vides | inspection d'un `job-empty` vide et d'un répertoire de politique vide | isolation et connecteur refusés ; répertoires inchangés |
| Mauvaise identité | dossier d'un autre espace, puis commit de clone différent | `InvalidDossier` ou `commit_identity_mismatch` ; arbres inchangés |
| Configuration incomplète | `operator_status.py --dossier` sans les trois autres liens | exit 2, `incomplete_dossier_binding`, chemins vides |
| Outils absents | sonde injectée sans `python3`, `node`, `git`, `flock` ni Docker | ces noms figurent dans `missingEvidence` |
| Contrats Antigravity | `node --test integrations/antigravity/runner.test.mjs integrations/antigravity/paperclip-adapter.test.mjs` | 21 réussis, exécutés avant cette revue |
| Instantané de développement | non relancé et non modifié | l'échec de lien symbolique reste à Antigravity |

Les 20 tests ignorés sans root couvrent les chemins protégés (passerelle, permissions de service, publication root). Ils passent dans la suite root ci-dessus. Cette suite root n'est pas une qualification Docker.

Preuves non sensibles de cette session : sorties de tests conservées hors dépôt. Le rapport d'inspection ne contient ni objectif de dossier, ni secret, ni chemin de politique.

## 4. Exécuté, implémenté, bloqué

Exécuté ici : installation idempotente de l'alias `python`, suites unitaires, préparation synthétique, inspection sans effet. Un agent Cloud distinct a revu les outils et la suite d'alors (165 tests, 20 ignorés) plus une préparation synthétique. Cet agent a démarré depuis la construction d'environnement, pas depuis une mission modèle.

Implémenté avant cette reprise, et rejoué seulement par les tests unitaires : verrou `flock`, refus de clôturer une absence Docker ambiguë, reprise d'identité, courses à barrière. Ces tests ne parlent pas au démon Docker.

Implémenté par cette reprise : le rapport d'inspection, puis le resserrement de ses indicateurs. Une présence de répertoire n'est plus une isolation ni un connecteur configuré. Les outils absents sont nommés dans `missingEvidence`.

Bloqué : Docker n'est pas installé. Les qualifications `qualify_*.py`, le redémarrage PostgreSQL et le parcours `--interrupted-run --reconcile` n'ont pas été relancés. L'authentification fournisseur n'a pas été vérifiée. `independentValidationPassed` reste faux. Le compte rendu Codex du 30 septembre décrit un agent synthétique sur un autre hôte ; il n'est pas une observation de cette machine.

## 5. Mesures et prochaine action

| Mesure | Valeur | Lecture |
| --- | --- | --- |
| Suite hôte avec `commit.gpgsign=true` | 180 tests, 20 ignorés, 1,128 s ; root 180 tests, 1,150 s | Les commits de fixtures portent `-c commit.gpgsign=false`. Aucun réglage global. |
| Faux positif `job-empty` avant correction | `isolated: true` | Un nom de répertoire ne prouvait pas un clone. |
| Même dossier après correction | `isolated: false`, `empty_job_directory` | Le répertoire reste vide. |
| Faux positif politique vide avant correction | `connectorConfigured: true` | La présence du répertoire ne validait aucun octet. |
| Même dossier après correction | `connectorConfigured: false`, `connector_content_missing` | Le répertoire reste vide. |

Prochaine action minimale vers une mission avec modèle : sur un hôte où `docker info` répond, exécuter la qualification connectée déjà écrite, avec un compte fournisseur distinct de ce rapport, puis relire `authenticationVerified`. Ne pas traiter le rapport d'inspection ni l'agent synthétique comme cette mission.

## 6. Limites

L'inspection ne prend pas le verrou et ne crée pas `launch.lock`. Elle ne lit pas le store canonique : l'état reste `unknown`, donc `readyForRealMission` reste faux. Un connecteur dont les empreintes concordent ne vérifie pas un compte fournisseur. Un démon Docker absent n'autorise aucune conclusion sur un conteneur. Le défaut Linux de `development-snapshot` n'est pas modifié ici ; il est traité à part par Antigravity. Le script d'installation d'environnement n'exécute plus `git config --global commit.gpgsign false`.

AgentMemory n'est pas accessible depuis cet environnement et n'est pas utilisé comme mémoire de production.
