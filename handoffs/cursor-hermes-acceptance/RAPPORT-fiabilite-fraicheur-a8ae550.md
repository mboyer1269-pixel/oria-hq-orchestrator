# Fraîcheur free-models (delta après a8ae550)

## Application

```bash
# Sur main 74dfd2f si besoin :
git am cursor-catalogue-acp-default-guard-main74dfd2f.patch   # → a8ae550
git am cursor-catalogue-fiabilite-fraicheur-a8ae550.patch     # → d85572f
```

## Défaut (reproduit)

Avec garde ACP seul : réécriture de `config/openrouter.free-models.json` + `utimesSync` pour figer le mtime → `loadFreeModelCatalogSnapshot` et hold OpenRouter restaient stale (mtime-only).

## Correctif

Hash SHA-256 du contenu (BOM retiré) invalide le cache module et le hold OpenRouter (`freeCatalogContentSha256`).

## Limite

Réécriture **identique** après normalisation UTF-8/BOM : pas d’invalidation (documenté dans `free-model-catalog.ts`).

## Vérification

53 tests catalogue ciblés + `npm run typecheck` OK sur `d85572f`.

Patch ACP `cursor-catalogue-acp-default-guard-main74dfd2f.patch` : **non modifié** (intégration Codex).
