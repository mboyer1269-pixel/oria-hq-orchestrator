# Reprise — jalon mission essayable

1er octobre 2026. Branche `cursor/validateur-preuves`. Ne pas fusionner. Ne pas appeler de modèle. Ne pas toucher `integrations/antigravity/`.

## Fait

Le défaut de `2b614bc` est corrigé dans le schéma stable version 2. Une assertion `real` doit avoir `passed: true`, `expected` et `observed` égaux et de même type. Une sortie doit avoir `expectedExitCode` égal à `exitCode`, y compris quand ce code n'est pas 0. Les contradictions, `passed: false`, les négatifs et les types malformés sont refusés. La version 1 sort `incomplete`.

Vérification :

```sh
python3 -m unittest discover -s integrations/qualification-evidence -p 'test_*.py'
```

## Non fait, et pourquoi

Le parcours Discuter Hermes, admission HQ, autorisation, OpenHands, résultat n'est pas qualifié. Les manques sont dans `docs/CURSOR-MATRICE-MANQUES-INTEGRATION.md`. Le commit `be61d26` est absent. Aucun rapport collecté version 2 n'est dans le dépôt. En fabriquer un serait une fausse preuve.

## Prochaine action utile

Attendre le harness PostgreSQL/PostgREST d'Antigravity et le passer au contrôleur :

```sh
python3 integrations/qualification-evidence/validate_evidence.py rapport.json
```

Lire le verdict. Ne pas le traduire en mission réussie. Brancher Hermes seulement après identification du binaire 0.15.2. N'autoriser un appel modèle que par une décision séparée.
