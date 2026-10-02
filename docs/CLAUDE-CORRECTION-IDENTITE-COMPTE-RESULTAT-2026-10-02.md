# Correction prioritaire — identité compte réelle — résultat

2 octobre 2026. Mandat : `docs/CLAUDE-CORRECTION-IDENTITE-COMPTE.md`. Le
contrôle indépendant a raison : `const accountId = providerProfile.id`
(introduit au complément précédent) est un bug, pas un raccourci acceptable.
Un profil nomme une POLICY ("claude-default"), jamais le compte réellement
connecté derrière. Deux comptes différents peuvent partager un profil ; les
identifiants réels derrière un profil peuvent changer sans que son id change
jamais. Corrigé dans le périmètre backend existant, sans nouvelle couche ni
nouveau fournisseur.

## Diff ciblé

**`src/server/agents/models/provider-connection-discovery.ts`** — nouvel axe
optionnel `accountId?: string` sur `ProviderConnectionProbeOutcome` et
`ProviderConnectionEntry`. Attestation sûre et non brute, jamais un email/
token/nom d'organisation ; absente quand la sonde n'a pas de preuve par
compte. Validée par la fonction `isNonEmptyId` déjà existante dans ce
fichier — aucune nouvelle validation inventée. Doctrine du module mise à
jour pour nommer explicitement cet axe.

**`src/server/agents/models/runner-executor-connection-probe.ts`** — aucun
changement de comportement. En-tête complété : la sonde réelle ne peut PAS
attester un compte aujourd'hui, par construction — la liste blanche de
`classifyClaudeCodeProbe` (`loggedIn`/`authMethod`/`apiProvider`/
`subscriptionType`) ne contient aucun champ qui distingue sûrement un compte
d'un autre configuré de façon identique. Hacher ces champs pour fabriquer un
« identifiant » aurait été exactement l'identité inventée que le mandat
interdit — deux comptes avec le même type d'abonnement hacheraient de façon
identique, donc cela ne prouverait rien. Test ajouté le confirmant
explicitement (`"accountId" in outcome === false` même quand `loggedIn:true`).

**`src/server/missions/model-emission-launch-gate.ts`** — le cœur de la
correction :
- `accountId` n'est plus `providerProfile.id`. Il vient maintenant de
  `connectionEntry.accountId` — l'entrée de connexion réelle retournée par
  `resolveProviderConnectionDiscovery` pour le fournisseur lié
  (`binding.registryProviderId`), jamais de la configuration.
- **Sans identité réellement attestée : refus explicite**, nouveau statut
  `account_identity_unverifiable`, posé AVANT même d'appeler
  `evaluateModelEmissionGate` — jamais de repli vers le profil, jamais
  d'identité inventée.
- **Liaison stable compte/workspace/modèle** : conservée et renforcée — la
  vérification `subscriptionAuthorized` compare déjà
  `capability.accountId === accountId && capability.workspaceId ===
  context.workspaceId && capability.modelId === modelId` (du lot
  précédent), maintenant alimentée par la vraie attestation.
- **Liaison stable à la « version d'accord »** : réutilise le mécanisme
  d'approbation déjà existant (`approvalStillAuthorizes`) — pas de nouveau
  champ « version » inventé ; l'identité de l'approbation EST la version
  d'accord dans le vocabulaire de ce système.
- **Révocation/changement de compte juste avant le commit** : nouvelle
  fonction pure exportée `attestedAccountStillMatches(authorizedAccountId,
  recheckEntry)` — re-sondée (via `resolveProviderConnectionDiscovery`,
  réutilisé, jamais une deuxième mécanique) immédiatement avant
  `deps.launch`, aux côtés du re-contrôle d'approbation déjà en place.
  Refuse si l'identité change OU si `isExecutionReady` devient faux (compte
  déconnecté) — nouveau statut `account_identity_changed_before_commit`.
  Effet de bord positif, pas un ajout séparé : ceci ferme aussi la lacune de
  révocation de connexion que l'en-tête du fichier signalait explicitement
  comme non couverte au lot précédent.

## Tests exécutés

`node --test src/server/missions/model-emission-launch-gate.test.mjs` :
**39/39, zéro échec.** Dont, nouveaux ou corrigés pour cette correction :
- Changement de compte sous le même profil, découvert juste avant le
  commit → `account_identity_changed_before_commit`, `deps.launch` jamais
  appelé. Preuve décisive que le bug est corrigé : `providerProfile.id`
  reste "claude-default" tout du long, jamais utilisé.
- Sonde sans identité (connectée, mais sans `accountId`) →
  `account_identity_unverifiable`, jamais de repli vers le profil — testé
  à la fois comme scénario explicite dédié et comme comportement par
  défaut réel (aucune sonde fournie).
- Révocation du compte (déconnecté) découverte juste avant le commit →
  même refus, via `isExecutionReady`, pas seulement l'égalité d'identité.
- Concurrence : deux confirmations simultanées avec une attestation stable
  passent toutes les deux le gate ; la vraie CAS de `openhands-launch-store.ts`
  reste ce qui sérialise, pas ce gate.
- 7 tests purs dédiés à `attestedAccountStillMatches` (même doctrine que
  `approvalStillAuthorizes`) : stable, absent, compte différent, déconnecté,
  evidence déclarée seulement, concurrence.
- Tous les tests préexistants cassés par cette correction (6, listés dans
  le rapport précédent comme utilisant une sonde hypothétique sans identité)
  corrigés pour fournir une attestation réelle au lieu d'être affaiblis.

`node --test src/server/agents/models/runner-executor-connection-probe.test.mjs` :
**16/16**, avec la nouvelle preuve que la vraie sonde n'attache jamais
`accountId` aujourd'hui.

`node --test src/server/missions/model-emission-gate.test.mjs src/core/openhands-launch-contract.test.mjs` :
**27/27**, inchangés.

`npx tsc --noEmit` sur tout le dépôt : **12 erreurs, stables, confinées à
`src/server/ai/llm-json-provider.ts` (9) et `src/server/ai/model-router.ts`
(3)** — exactement les erreurs que Cursor doit corriger dans son périmètre,
non touchées ici.

Combiné (`missions/*` + `ai/*` + `agents/models/*` +
`openhands-launch-contract`) : **zéro échec hors des deux lacunes
intentionnelles déjà trackées par le projet**
(`openhands-launch-model-connection-gap.test.mjs`, convention
`*-gap.test.mjs`, non liées à ce mandat).

## Limites — dites explicitement, pas cachées

1. **"Attestation périmée" n'est pas re-testée comme scénario dédié de ce
   gate.** Ce gate re-sonde avec un `now()` fraîchement capturé pour
   l'entrée ET l'évaluation à chaque décision — les deux ne peuvent jamais
   diverger à l'intérieur d'un seul appel, donc une lecture de décision
   périmée est structurellement impossible ici, par construction, pas par
   un contrôle qui pourrait être contourné. Le contrôle de péremption lui-
   même existe déjà et est déjà prouvé (`model-emission-gate.test.mjs`,
   « a stale INDIVIDUAL provider entry is blocked... », réutilisé sans
   modification via le même `checkedAtIso` que ce gate transmet).
2. **`accountId` reste absent en pratique aujourd'hui.** La correction
   construit le circuit complet et le prouve avec des sondes injectées en
   test, mais la vraie sonde (`runner-executor-connection-probe.ts`) n'a
   aucun champ sûr à partir duquel attester un compte spécifique — testé et
   documenté explicitement, pas supposé. Résultat observable en production :
   tout `confirm_launch` reste bloqué par `account_identity_unverifiable`,
   avant même d'atteindre le blocage « aucun hôte runner » déjà connu.
   Exposer un signal plus fort mais toujours sûr est une décision séparée
   sur ce qu'il est acceptable de divulguer — pas prise ici.
3. **Logique non déclarée complète sur la seule base des mocks.** Les tests
   ci-dessus prouvent la LOGIQUE du gate (ordre des contrôles, refus
   explicite, re-vérification) avec des sondes injectées — ils ne prouvent
   ni ne prétendent prouver qu'un compte réel a été observé en production.
   Aucun login, aucun appel modèle, aucun déploiement, aucun élargissement
   de permission n'a eu lieu.
4. **`src/server/ai/*` non touché.** Les 12 erreurs TypeScript restantes
   sont dans le périmètre de Cursor exclusivement ; je ne les ai pas
   corrigées et n'ai pas tenté de les masquer.

## Fichiers modifiés (Oria.HQ, non commités — voir note de session)

```
 M src/server/agents/models/provider-connection-discovery.ts
 M src/server/missions/model-emission-launch-gate.ts
 M src/server/missions/model-emission-launch-gate.test.mjs
 M src/server/agents/models/runner-executor-connection-probe.test.mjs
```

Ce lot a travaillé directement dans `hq-acces-reprise` (worktree compagnon,
non entré via l'outil dédié cette session) ; les changements restent donc
non commités, à côté du travail Cursor en cours (préservé intégralement —
voir `git status` complet dans le rapport du lot précédent pour la liste des
fichiers `src/server/ai/*` concernés, inchangée).
