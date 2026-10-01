# Qualification locale des accès — 1 octobre 2026

Lot Cursor reçu par la [PR privée 10](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/10), appliqué et revu par Codex. Produit : branche `codex/hq-delivery-integration`, base `3af7ec6`, candidat `cf4fc4addee7ffe8ef4f0a2d6a1027b0d643b6c6`, arbre `73f9985d65f97d41879d7835fcb05ac363952711`. Huit fichiers de tests, bancs et documentation ajoutés; aucune modification des migrations ou de la logique applicative.

## Résultat contrôlé

- Assemblage réel `route.ts` / contrôle propriétaire / service, clients d'authentification et de base remplacés : 401 sans session, 403 pour un non-propriétaire, acteur issu de la session, contexte fixé par le serveur, refus des champs usurpés sans écriture. Aucune authentification réelle revendiquée.
- Suite ciblée sous Node 22.14 et Ubuntu 24.04 : **10 tests, zéro échec, zéro exclusion**, 480 ms. Lint des quatre fichiers JavaScript ciblés : exit 0, sans sortie.
- Banc explicite Docker `postgres:16.4-alpine` : **run `1790843349_80260`, exit 0**, sur cet arbre final. Migrations réelles `0001`, `0005`, `0028`; rôles locaux `anon`, `authenticated`, `service_role` sans superutilisateur ni BYPASSRLS.
- Les clients ne peuvent exécuter les RPC du budget. Le contrôle positif du rôle de service exécute les RPC autorisées. Les tables missions et budget sont protégées par les ACL, puis la RLS est éprouvée avec des droits de table accordés dans une transaction annulée : lecture et INSERT/UPDATE/DELETE, effet nul, lignes complètes inchangées pour chacun des deux rôles clients. Le rôle effectif est vérifié avant l'essai; un échec de `SET ROLE` arrête le banc.
- La suite ciblée utilise un exécutable Docker factice pour le cas moteur indisponible. Elle ne lance plus de conteneur implicitement. La recette réelle est une commande distincte.
- Conteneur `oria-admission-rls-pg-1790843349_80260`, volume `oria-admission-rls-1790843349_80260` et réseau `oria-admission-rls-net-1790843349_80260` absents après nettoyage, contrôlés indépendamment.

## Reproduction depuis le produit

```sh
node --test --test-concurrency=1 src/app/api/missions/development/route-owner-boundary.test.mjs proofs/admission-boundary-structure.test.mjs
sh proofs/run-admission-rls-real-db.sh
```

La deuxième commande exige Docker et crée uniquement ses ressources jetables nommées. Docker absent donne `NON EXECUTE`, exit 127; cela ne vaut pas réussite. Journaux indépendants dans Orchestrator : `.validation/admission-final/targeted.log`, `lint.log`, `real-db.log`; [copie publiable du résultat](evidence/2026-10-01-admission-final.txt). Le run antérieur `1790842532_79642` ne couvre pas le supplément.

Empreintes des patches contrôlées : initial `8041679e12194d91b677906a568b5d965147e76eef343b99ef8055a2913c1cb3`; supplément `a083fa2a95806346e94c63973471bfaba68cd90837bb27ea1e6e2f47a6632fb5`. Égalité de l'arbre après application vérifiée. Les quatre validations globales du code `286a211` restent référencées dans [l'acceptation budget](HQ-BUDGET-ACCEPTATION-2026-10-01.md); elles n'ont pas été répétées pour des bancs et documents seuls.

## Limites et suite

Ce banc n'authentifie aucun compte Supabase, ne produit aucun JWT réel, n'utilise aucune clé service réelle et ne reproduit pas son privilège de contournement RLS. Il ne qualifie ni le VPS, ni Hermes, ni OpenHands, ni une mission modèle réelle. Les tarifs, plafonds et flags restent inchangés.

Le lot local est clos. Les prochaines actions des agents sont celles du [contrat courant](HQ-LIVRAISON-2026-10-01.md) : Claude qualifie le runtime après autorisation d'accès; Antigravity raccorde le parcours existant après cette observation et n'intègre la maquette qu'après validation de Michael; Cursor revoit alors ce parcours. Aucun audit supplémentaire à lancer pour occuper l'attente. La livraison du HQ demeure incomplète jusqu'à une directive authentifiée donnant une modification testée, revue et essayable, avec reprise sans doublon.
