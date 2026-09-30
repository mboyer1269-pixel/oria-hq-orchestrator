# Contrôle des preuves d'admission

Outil hors ligne. Il lit un JSON déjà écrit. Il ne démarre pas PostgreSQL, ne contacte pas le réseau et ne modifie aucun script Antigravity.

Le guide humain est `docs/CURSOR-VALIDATEUR-PREUVES.md`. Le contrat des champs est `SCHEMA.md`.

Vérifier le contrôleur :

```sh
python3 -m unittest discover -s integrations/qualification-evidence -p 'test_*.py'
```

Lire un rapport :

```sh
python3 integrations/qualification-evidence/validate_evidence.py rapport.json
```

Le code de sortie est 2 (`incomplete`), 3 (`refused`) ou 4 (`reviewable`). Il n'est jamais 0. `reviewable` ne veut pas dire que le pont est accepté.
