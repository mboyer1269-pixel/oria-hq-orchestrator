# Intégration HQ — patch catalogue PR #13 (`cursor-catalogue-acp-default-guard.patch`)

Orchestrateur : [PR #13](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/13).  
Produit cible : **Oria.HQ.Michael.HQ-APP** (dépôt application HQ, pas ce dépôt orchestration).

## Objectif

Empêcher l’id ACP/profil **`default`** (mode session ACP) d’apparaître comme **modèle fournisseur tarifable** dans le catalogue consultatif (`/hq/runtime`). Aucun changement bridge, runner, VPS, autorisations de lancement, exécution Claude ou mission réelle.

## Branche HQ cible et prérequis

1. **Base qualifiée documentée** : `f0e42a531c1a1e2d47726f870d15f0f905f367d8` (`codex/hq-delivery-integration`), cf. `docs/HQ-COORDINATION-HERMES-2026-10-01.md`.
2. **Chaîne catalogue consultation** (si pas déjà sur la branche d’intégration) : patches `handoffs/cursor-hermes-acceptance/cursor-routage-catalogue*.patch` + `cursor-consultation-*.patch` jusqu’à **`0834abd`** (voir `MANIFEST.txt` / branche `cursor/hermes-acceptance`). Ne pas réappliquer les correctifs tarifs déjà livrés ailleurs.
3. **Prérequis direct du patch PR #13** : commit produit **`0b5269c`** (`cursor-catalogue-fiabilite-fraicheur.patch`, parent **`0834abd`**). Sans ce parent, `git am` sur le garde ACP peut échouer ou omettre le contexte free-models.

Ordre recommandé sur la branche d’intégration HQ :

```text
… → 0834abd (consultation cumul + deltas déjà validés localement)
  → git am cursor-catalogue-fiabilite-fraicheur.patch   # 0b5269c
  → git am cursor-catalogue-acp-default-guard.patch       # 071dbf7
```

## Application du patch PR #13

Depuis la racine du clone **produit** HQ, avec working tree propre :

```bash
# Vérifier le parent (tree doit contenir free-model-catalog.test.mjs et hold mtime de 0b5269c)
git log -1 --oneline
git status -sb

# Appliquer (format mailbox)
git am /chemin/vers/handoffs/cursor-hermes-acceptance/cursor-catalogue-acp-default-guard.patch

# En cas de conflit : résoudre, puis
git add src/server/ai/gateway-catalog.ts \
        src/server/ai/gateway-catalog.test.mjs \
        src/server/ai/model-catalog-consultation.ts \
        src/server/ai/hq-model-catalog.test.mjs
git am --continue
```

Alternative équivalente si la branche contient déjà `071dbf7` :

```bash
git cherry-pick 071dbf70cdbec910d7462393df6ac3be83a08fec
```

Commit attendu : **`071dbf7`** — *Exclude ACP profile id default from provider catalog rows*.

## Fichiers à intégrer (PR #13 uniquement)

| Fichier | Rôle |
|---------|------|
| `src/server/ai/gateway-catalog.ts` | `isProviderCatalogModelId()` ; filtre à l’ingestion OpenRouter/Nara |
| `src/server/ai/model-catalog-consultation.ts` | Filtre des entrées snapshot free-models dans `defaultCache()` |
| `src/server/ai/gateway-catalog.test.mjs` | Régression ingestion + `assessServerEmission("default")` → `not_listed` |
| `src/server/ai/hq-model-catalog.test.mjs` | Régression vue catalogue + non-régression `refresh: "now"` / `chooseModel` |

## Fichiers à ne pas toucher pour cette intégration

- **Bridge / OpenHands** : `integrations/openhands-*`, `src/server/missions/openhands-*`, routes `/api/orchestration/openhands*`
- **Runner / VPS / deploy** : `deploy/*`, Dockerfiles pilot, scripts qualification VPS
- **Autorisations & exécution** : `src/server/auth/*`, `llm-json-provider.ts`, `model-router.ts`, `execution-models.ts`, réservations d’appel, binding ACP côté lancement
- **UI hors catalogue runtime** : Atelier, cockpit Hermes, missions (pas de refonte libellés « modèle observé OpenHands » dans ce lot)
- **Routeur / coûts métier** : pas de modification de `chooseModel`, ladder d’émission, ni registre Claude

Si un conflit apparaît hors des 4 fichiers ci-dessus, **stopper** et trancher avec le coordinateur — ne pas élargir le diff.

## Tests ciblés (obligatoires après intégration)

Installation des deps si besoin : `npm ci` à la racine produit.

```bash
# Lot catalogue complet (51 tests au moment de la qualification)
node --test --test-concurrency=1 \
  src/server/ai/gateway-catalog.test.mjs \
  src/server/ai/hq-model-catalog.test.mjs \
  src/server/ai/model-catalog-consultation.test.mjs \
  src/server/ai/free-model-catalog.test.mjs
```

**Régression `default` uniquement** (doit passer ; si `default` réapparaît comme ligne tarifable, ces tests échouent) :

```bash
node --test --test-concurrency=1 src/server/ai/gateway-catalog.test.mjs \
  --test-name-pattern 'ACP profile id default is not ingested'

node --test --test-concurrency=1 src/server/ai/hq-model-catalog.test.mjs \
  --test-name-pattern 'provider catalog rows exclude the ACP profile id default'
```

Critères de succès :

- Aucune observation `modelId === "default"` après `normalizeGatewayCatalog` sur fixture `/models`.
- Aucune ligne `line.modelId === "default"` dans `loadHqModelCatalog` sur la même fixture.
- `assessServerEmission` avec `modelId: "default"` reste `emit: false`, `block: "not_listed"` (pas de tarif inventé).

## Libellés UI (vérification statique, sans refonte)

Périmètre vérifié : **`src/app/hq/runtime/page.tsx`** + couche `hq-model-catalog.ts`.

| Surface | Comportement attendu |
|---------|-------------------|
| Widget **Catalogue modèles** | Titre *Consultation — non exécutable* ; mention *Accès et quota : inconnus* ; colonnes **Fournisseur / Modèle / Tarif** = liste fournisseur uniquement (OpenRouter, Nara). |
| Colonne **Vérifié** | Date d’observation catalogue (`observedAt`) ou `inconnu` — pas l’identité ACP approuvée. |
| Colonne **État** | `périmé` / `indisponible` / `inconnu` (pas « gratuit illimité »). |
| Widget **Coût & routing — observé** | Distinct du catalogue ; *pas de facturation réelle* ; poids shadow — ne confond pas avec quota fournisseur. |

L’identité ACP approuvée (`modeId` / profil `default`) **n’est pas affichée** dans ce tableau catalogue ; elle reste côté session OpenHands/ACP (hors ce patch). Les modèles **observés chez le fournisseur** après exécution (`executedModelId`) ne sont pas fusionnés dans cette grille — aligné avec `chooseModel` / tests « loading the catalog does not change the approved model choice ».

## Risques restants

| Risque | Mitigation |
|--------|------------|
| Parent produit ≠ `0b5269c` | Appliquer d’abord `cursor-catalogue-fiabilite-fraicheur.patch` ou cherry-pick `0b5269c`. |
| Autre id ACP (futur) confondu avec un vrai modèle | Seul `default` est filtré ; extension = nouveau garde explicite + test, pas heuristique large. |
| `readCache` injecté en test avec `default` | Chemin production filtré ; les tests manuels avec mock custom peuvent encore injecter `default` — ne pas confondre avec prod. |
| UI Atelier / preuve `agent_returned` | Libellés mission vs catalogue non unifiés dans ce lot ; intégration UX OpenHands = travail séparé. |
| Commits produit `4bfd061` / `2ed003a` non fetchables | Ne pas reconstituer une ancienne implémentation ; signaler base manquante au coordinateur. |
| Suite complète / déploiement | Hors scope ; ce guide ne remplace pas `npm run typecheck`, build ou qualification VPS. |

## Références orchestrateur

- Patch : `handoffs/cursor-hermes-acceptance/cursor-catalogue-acp-default-guard.patch`
- Manifeste : `MANIFEST-catalogue-acp-default-guard.txt`
- Prérequis fraîcheur : `cursor-catalogue-fiabilite-fraicheur.patch`, `MANIFEST-catalogue-fiabilite-fraicheur.txt`
- Contrats : `CONTRAT-CATALOGUE-DYNAMIQUE-OPENROUTER-NARA.md`, `CONTRAT-CATALOGUE-SERVEUR.md`
