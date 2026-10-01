# Coût agrégé quand le fallback est bloqué

Même correctif de registre, commit suivant. Le patch `15fef1f9…` n'est pas modifié. Base `2694df17036b92948184fb2ada2de6d655092826`. Aucun tarif, aucun seed, flag éteint, aucun appel modèle.

`reservation_blocked` ne renvoie plus `refused()`. Le coût est `aggregateCost(attempts)`.

Primaire émis puis en échec (HTTP 503 ou exception après socket), fallback déjà autorisé mais registre `unavailable` ou rejeté : une seule émission. L'agrégat reste `failed_maybe_billed`, `networkRequestSent` vrai, `monetaryUsd` null. Ce n'est pas un refus global à zéro réseau. La tentative bloquée, elle, reste `refused`.

La branche `consume` qui échoue après succès modèle garde `unknown_cost` et `networkRequestSent` vrai. Une sortie sans tentative préalable reste un refus sans réseau, via le même `aggregateCost`.

## Commandes

Node 22.14.0.

- `node --test --test-concurrency=1 src/server/ai/call-reservation.test.mjs src/server/ai/llm-json-provider.test.mjs` — 22 tests, 0 échec, exit 0
- `npx eslint` sur `llm-json-provider.ts` et `call-reservation.test.mjs` — exit 0
- `npx tsc --noEmit` — exit 0
- PostgreSQL non rejoué. Build, smoke et les quatre portes ne sont pas relancés.
