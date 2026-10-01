# Revue ciblée — « generateStructuredJson never throws » face à un gate qui rejette

**Auteur :** Claude Code (revue indépendante, lecture seule)
**Date :** 1er octobre 2026
**Source figée :** WSL `/home/michael_/.gemini/antigravity/scratch/hq-budget-review-20261001.tHgOIf`,
arbre produit `cb461c21`.
**Propriétaire du correctif :** Cursor. **Aucun fichier produit modifié, aucune correction codée.**

## Verdict

**Le contrat est rompu dans les trois cas.** `generateStructuredJson` déclare « Never throws toward
the caller » (`llm-json-provider.ts:15`) ; une Promesse rejetée par `reserve`, `markEmitted` ou
`consume` remonte telle quelle à l'appelant.

Les trois `await` sont hors du `try` fournisseur (`llm-json-provider.ts:343-377`), et
`authorizeCallAttempt` n'a aucun `try/catch` :

| Appel | Fichier:ligne |
| :--- | :--- |
| `await gate.reserve(...)` | `call-reservation.ts:306` |
| `await gate.markEmitted(...)` | `call-reservation.ts:316` |
| `await gate.consume(...)` | `llm-json-provider.ts:380` |

## Résultat observé

Sonde bornée `Orchestrator/.validation/reservation-exceptions/probe.mjs`, Node 22.14 (WSL), jiti et
motif de montage des tests existants (`call-reservation.test.mjs`). Gate injecté, `fetchFn` injecté
synthétique, clé factice, `HQ_CALL_RESERVATION=1`, aucun modèle, aucun réseau. « sockets » = appels
du `fetchFn`, c'est-à-dire requêtes fournisseur que la couche aurait émises.

```
HQ_CALL_RESERVATION actif=true  accessClass(claude-haiku-4-5-20251001)=api

-- Contrôle : les trois méthodes résolvent ---------------------------
aucun rejet            REND  sockets=1  ok=true json={"probe":"model-result"}  reservation=consumed  cost=observed_usage  gate: reserve -> markEmitted -> consume

-- Les trois cas du mandat : la Promesse du gate est rejetée ---------
reserve rejette        LÈVE  sockets=0  ReservationStoreError: reserve: store connection lost        gate: reserve
markEmitted rejette    LÈVE  sockets=0  ReservationStoreError: markEmitted: store connection lost    gate: reserve -> markEmitted
consume rejette        LÈVE  sockets=1  ReservationStoreError: consume: store connection lost        gate: reserve -> markEmitted -> consume
```

Le contrôle établit que le harnais atteint bien les trois méthodes et qu'un parcours nominal rend
`ok:true`. Seule la nature **rejetée** de la Promesse change le résultat.

### Lecture des trois cas

- **`reserve` rejette — 0 socket.** Aucune requête fournisseur n'a été émise, aucun résultat modèle
  n'existe, et l'état de la réservation est indéterminé : l'exception ne dit pas si une ligne a été
  posée côté store avant la perte de connexion.
- **`markEmitted` rejette — 0 socket.** `reserve` a réussi, donc **un montant est tenu**. Le `release`
  de `call-reservation.ts:323` n'est **jamais atteint** : il n'est appelé que lorsque `markEmitted`
  *retourne* un état incohérent. Sur rejet, la retenue reste en place sans aucune trace rendue à
  l'appelant.
- **`consume` rejette — 1 socket.** Le plus coûteux : la requête fournisseur a abouti,
  `result.ok === true`, le JSON du modèle existe en mémoire à cet instant — et l'exception le
  **détruit** avant le `return` de `llm-json-provider.ts:386-401`. L'appelant ne reçoit ni le résultat
  payé, ni `attempts`, ni `cost`, ni `reservation`. La retenue reste en `emitted_unknown`.

## Distinction avec le cas attribué à Cursor

Le cas de Cursor est un **état retourné** : `markEmitted` rend un instantané `unavailable` ou
incohérent, la condition `call-reservation.ts:317-322` est vraie, `release` est appelé puis refusé, et
la fonction rend proprement `emit:false` avec `reason:"mark_failed"`. Ce chemin est couvert et
observable. Ici rien n'est retourné : la Promesse est **rejetée**, donc aucune de ces conditions n'est
évaluée et aucun `release` n'est tenté. Les deux défauts ne se recouvrent pas et le correctif de
Cursor sur le budget ne ferme pas celui-ci.

## Recommandation (non codée, à Cursor)

Encadrer les trois `await` de façon à rendre un résultat au lieu de lever, en préservant deux choses
que la sonde montre comme actuellement perdues :

1. **Le résultat modèle éventuel.** Pour `consume`, l'échec du store est postérieur à une réponse
   fournisseur réussie : rendre `ok:true` avec son `json`, `rawText`, `tokenUsage` et ses `attempts`,
   et porter l'échec dans la réservation — non dans la perte du résultat payé.
2. **L'incertitude de la réservation.** Sur rejet, l'état réel du store est inconnu. L'instantané rendu
   doit le dire explicitement — statut indéterminé et `reconciliationRequired`, le champ existant à
   cet usage — plutôt que de présenter une retenue comme libérée ou consommée.

Deux interdits qui découlent directement des observations : **aucune relance** du fournisseur (en cas
`consume`, la requête a déjà été émise et facturable), et **aucune libération supposée** (en cas
`markEmitted`, `release` n'a jamais été tenté ; l'écrire comme libéré serait faux).

## Limites

Trois cas seulement, ceux du mandat ; ce n'est pas une revue du module ni un audit du budget. Gate et
transport injectés : aucune exécution contre le store SQL réel, donc l'état réellement laissé en base
après une perte de connexion n'est pas observé — la sonde prouve le comportement du contrat, pas celui
de PostgreSQL. Aucun appel modèle réel, aucun résultat ici n'est présenté comme tel. Les quatre portes
n'ont pas été rejouées sur du code inchangé. Aucun commit, aucun push.
