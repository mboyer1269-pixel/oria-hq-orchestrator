# Registre rejeté — correctif supplémentaire

Part de `8ec216414359f7b2484b05c62bf18281fcf8fb8a`, arbre `087a126fa1d063b4a29aa7dbb0cd272b281b93b2`. Les patchs budget, délai `bea0c309` et écarts ne sont pas remplacés. Aucun tarif, aucun seed, `HQ_CALL_RESERVATION` n'est pas allumé. Aucun appel modèle.

`generateStructuredJson` ne propage plus un rejet de `reserve`, `markEmitted`, `release` ou `consume`.

- Avant émission, un `reserve` rejeté ou `unavailable` refuse l'appel. Aucun socket, aucun fallback. Le motif `malformed` ne passe plus au fournisseur suivant.
- Après un mark incertain, le montant confirmé par `reserve` reste, ici 40 cents USD, même si `mark` et `release` rejettent ou répondent `unavailable`. Le statut n'est pas fabriqué en `released`. `reconciliation_required` reste vrai.
- Si `consume` rejette ou répond `unavailable` après une réponse modèle réussie, le JSON obtenu est rendu, l'état reste `emitted_unknown` avec les cents connus, et le modèle n'est pas rappelé. Une seule émission.

## Commandes

Node 22.14.0.

- `node --test --test-concurrency=1 src/server/ai/call-reservation.test.mjs src/server/ai/llm-json-provider.test.mjs` — 21 tests, 0 échec, exit 0
- `node --test --test-concurrency=1` sur les clients JSON, le routeur, l'échelle de coût et `routing-execution` — 63 tests, 0 échec, exit 0
- `npx tsc --noEmit` — exit 0
- `npx eslint` sur `call-reservation.ts`, `llm-json-provider.ts`, `call-reservation.test.mjs` — exit 0
- PostgreSQL non rejoué. Ce commit ne touche pas le SQL. Le run `1790840244_77530` reste celui de l'arbre `087a126`.
- Build, smoke et les quatre portes globales ne sont pas relancés ici.
