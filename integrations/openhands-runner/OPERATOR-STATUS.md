# Inspection opérateur sans effet

`operator_status.py` prépare le diagnostic d'un checkout Linux. Il ne réconcilie pas, n'exécute pas, ne nettoie rien et n'appelle aucun modèle.

```sh
python integrations/openhands-runner/operator_status.py
```

Avec un dossier synthétique déjà vérifiable localement, lier explicitement l'espace, la version d'exécutant et la source. Ces quatre arguments vont ensemble. Aucun n'accorde une exécution.

```sh
python integrations/openhands-runner/operator_status.py \
  --dossier request.json \
  --workspace synthetic-a \
  --executor-version 1.50.0 \
  --source /chemin/depot
```

## Ce que le rapport sépare

| Champ | Sens |
| --- | --- |
| `mode` | Toujours `inspect` pour cette commande. |
| `mission`, `executor` | Identité seulement après validation du dossier. Le texte de mission n'est pas recopié. |
| `canonicalState` | `unknown` ici : ce checkout n'est pas le store canonique HQ. |
| `docker.daemon` | `available`, `unavailable` ou une sonde en échec. |
| `docker.container` | `not_observed`. Ce n'est pas `absent`. |
| `lock` | `not_requested`, `absent`, `free`, `held` ou `unknown`. Le fichier de verrou n'est pas créé. |
| `prerequisites.authenticationVerified` | Faux. Un répertoire de politique ou un fichier de configuration ne prouve pas l'authentification. |
| `prerequisites.authorizationPresent` | Faux. Un dossier de préparation n'est pas une autorisation d'exécution. |
| `blockCategory` | `real_mission_not_ready` tant qu'une preuve exigée manque. |
| `nextAction` | Rester en inspection. Ne pas réconcilier ni relancer. |
| `readyForRealMission` | Faux tant que les preuves manquantes ne sont pas observées. |
| `independentValidationPassed` | Faux. Un agent synthétique n'est pas une mission modèle. |

Le code 0 veut dire que le rapport a été écrit. Le code 2 est un refus, sans chemin, contenu de dossier ni secret. `--force` n'existe pas.

## Commandes distinctes

- Préparer un clone isolé : `prepare_job.py`. Cela crée un répertoire de travail et refuse de le réutiliser.
- Réconcilier une revendication déjà protégée : `reconcile_launch.py`. Cette commande peut écrire une transition. Elle ne se substitue pas à l'inspection.
- Exécuter un job déjà autorisé : `run_host_job.py`, sans `--inspect`. `--inspect` sur cette entrée reste une lecture root d'un hôte déjà préparé.

Les qualifications connectées (`qualify_hq_postgrest.py`, Docker, PostgreSQL, agent synthétique) ne font pas partie de cette inspection. Les exécuter exige un hôte où Docker répond réellement. Leur réussite ne doit pas être recopiée comme une mission fournisseur.
