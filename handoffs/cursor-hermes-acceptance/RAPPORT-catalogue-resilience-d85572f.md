# Résilience lecture free-models (post-d85572f)

## Base

`d85572f381e048e23434aa7af0c01d0dabe5e799` (patches fraîcheur + ACP déjà intégrés par Codex).

## Scénarios vérifiés

| Scénario | Résultat attendu | Observé |
|----------|------------------|---------|
| JSON tronqué / invalide | Pas de crash ; snapshot vide (non exécutable) | OK |
| Fichier absent (ENOENT) | Pas de crash ; snapshot vide | OK |
| Réécriture concurrente + hold OpenRouter | Hold invalidé par hash ; Nara reste consultable | OK (d85572f) |
| `Promise.all` double `loadHqModelCatalog` + fichier corrompu | `ok: true`, Nara présent, `executionAuthorized: false` | OK |
| Cache vide **mal épinglé** avec hash valide (race TOCTOU) | Ne pas servir le vide comme « frais » si le disque parse | **Défaut reproduit** → corrigé |

## Défaut corrigé

Après une course lecture/réécriture, le cache pouvait conserver `{ entries: [] }` avec le **hash du fichier valide** : les appels suivants hit cache et masquaient le contenu réel (consultation free-models / `defaultCache` vide alors que le fichier est bon).

**Correctif** : sonde `readSnapshotFromDisk()` sur hit cache vide + relecture si le hash disque a changé pendant le premier `read`.

## Patch incrémental

`cursor-catalogue-free-model-resilience-d85572f.patch` → commit `2bc64e3`, parent **`d85572f`**.

57 tests catalogue ciblés + `npm run typecheck` OK.

Hors scope respecté : pas d’appel modèle, VPS, merge, UI, runner.
