# Validateur de preuves d'admission

Contrôleur automatique du rapport d'admission, hors du backend Antigravity. Il rend impossible un feu vert documentaire : un JSON ne peut pas se déclarer prêt, ni transformer une `Map` ou un lookup en preuve réelle. Il ne fournit ni preuve cryptographique ni backend prêt.

## Commande

Depuis la racine du dépôt :

```sh
python3 -m unittest discover -s integrations/qualification-evidence -p 'test_*.py'
```

Cette commande vérifie le contrôleur. Elle ne qualifie pas un pont. Pour lire un rapport déjà collecté :

```sh
python3 integrations/qualification-evidence/validate_evidence.py rapport.json
```

## Ce que l'outil fait

Il valide la version 2 du schéma décrit dans `integrations/qualification-evidence/SCHEMA.md`. La version 1 est refusée comme close : un identifiant d'assertion ne suffit plus. Un scénario `real` exige `passed: true` avec `expected` égal à `observed`, et `expectedExitCode` égal à `exitCode`. Ces codes peuvent être différents de 0 quand le conflit ou la perte de réponse l'attendent. Une assertion échouée, contradictoire, malformée ou négative ne peut pas laisser le rapport `reviewable`.

Le verdict calculé est seulement `incomplete`, `refused` ou `reviewable`. `readyForProduction` et `authenticatesExecution` restent faux dans la réponse. Un champ du même nom dans le rapport, ou un verdict annoncé par l'auteur, est ignoré ou refuse le paquet.

| Verdict | Sortie | Lecture |
|---|---|---|
| `incomplete` | 2 | Scénario absent, `not_run`, `failed` ou `simulated`. Pas de feu vert. |
| `refused` | 3 | Un statut `real` est contredit par le rapport. |
| `reviewable` | 4 | Le JSON est cohérent. Un humain peut le lire. Rien n'a été exécuté par cet outil. |

La sortie 0 n'est pas utilisée, pour qu'un script ne prenne pas le contrôle d'un rapport pour une réussite.

## Refus d'un statut real

- `backendKind` `map`, `mock`, `http-in-process`, ou un texte qui contient `Map` ou `createServer`.
- Digest, migration, version ou contrainte `pg_constraint` manquants. Une définition sans UNIQUE, PRIMARY KEY ou EXCLUDE, ou un lookup applicatif, ne compte pas.
- `lost_response_after_commit` dont la procédure ou la seule phase est un lookup.
- Commit du rapport, d'un scénario ou d'une sortie qui n'est pas le même.
- Redémarrage sans les deux assertions `sql_count_before_restart` et `sql_count_after_restart`, ou avec des comptes différents.
- Admission sans les trois comptes, ou avec `admissionMeansExecution` vrai.
- `fixtureClass` égal à `synthetic`.

## Fixtures

`integrations/qualification-evidence/fixtures/synthetic/` ne contient que des rapports synthétiques identifiés. Ils couvrent la Map, le lookup étiqueté perte de réponse, les commits mélangés, le redémarrage sans compte SQL, l'admission confondue avec l'exécution, et un rapport autrement cohérent mais encore étiqueté synthétique. Aucun ne doit sortir `reviewable`.

## Limites

L'outil ne se connecte à aucune base et n'ajoute pas de second banc. Il ne relit pas le commit `be61d26`, absent de ce dépôt au moment de la checklist. Une cohérence JSON ne remplace pas les sorties d'un PostgreSQL/PostgREST jetable, ni une mission réelle.
