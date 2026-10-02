# Reprise backend HQ — résultat

2 octobre 2026. Mandat complet : `docs/CLAUDE-REPRISE-BACKEND-2026-10-02.md`.
Travaillé dans le worktree Orchestrator existant `codex-acp-candidate`
(corrigé en cours de lot — voir § 0) et directement dans le worktree
compagnon `C:/Users/micha/Dev/Oria.HQ/.claude/worktrees/hq-acces-reprise`
(non entré via un nouvel outil cette session, donc **non commité** par ce
lot — voir § 6). Aucun nouveau worktree, aucun sous-agent, aucun login,
aucun appel modèle, aucun déploiement, aucune copie de credentials.

## § 0. Base de travail corrigée avant toute modification

Le worktree `codex-acp-candidate` avait été fondé par défaut sur
`origin/main`, qui ne contenait pas le lot politique `914775e` déjà livré
(provider_policy.py, providerProfileSchema). Corrigé par `git reset --hard`
du worktree sur la pointe réelle de `codex/cursor-recovery-handoff` avant
tout changement — aucun commit perdu, le worktree n'avait que des fichiers
non suivis à ce moment-là.

## § 1. Registre du gate aligné sur les variantes strictes Claude/Codex

`src/server/missions/model-emission-launch-gate.ts` :
`PROVIDER_PROFILE_TO_REGISTRY_PROVIDER_ID` et `DEFAULT_EXECUTOR_PROVIDER_REGISTRY`
portent maintenant deux entrées explicites et complètes (`claude-code-cli`,
`codex-acp-cli`), miroir exact du dictionnaire Python
`PROVIDER_POLICIES` déjà livré côté Orchestrator (lot `914775e`). Aucun
second routeur : même mécanisme statique, même forme, juste une deuxième
entrée. `resolveExecutorProviderBinding` (fonction pure, déjà testée
indépendamment) résout maintenant correctement un plan Codex vers
`codex-acp-cli`, jamais vers Claude et jamais fusionné.

## § 2. Sonde réelle compte dans l'environnement runner — jamais depuis la présence d'un fichier

Nouveau fichier `src/server/agents/models/runner-executor-connection-probe.ts`
(HQ). Ferme exactement le trou nommé dans l'en-tête de
`model-emission-launch-gate.ts` : *"No live probe exists yet for the
'claude' executor account... that would need to run on the OpenHands
runner host, not Michael's laptop and not the Hermes VPS."*

- Réutilise `classifyClaudeCodeProbe` (`local-runtime-probe.ts`) **sans
  modification** — seul le transport change (SSH vers le runner au lieu
  d'un `execFile` local). Aucune logique de parsing JSON/liste blanche
  réécrite.
- Ne lit et ne vérifie **jamais** la présence d'un fichier `auth.json` ou
  d'un compte Hermes. La seule preuve acceptée est la sortie réelle de
  `claude auth status --json` exécutée sur l'hôte runner lui-même.
- Distingue trois états propres : `connected` (preuve positive réelle),
  `connection_required` (installé, preuve négative réelle — pas connecté),
  `unknown` (aucune preuve exploitable : timeout, refus, erreur de spawn,
  sortie malformée). Jamais de `connected` par défaut.
- **Aucune approbation écrite par défaut** (`RUNNER_EXECUTOR_PROBE_APPROVAL =
  {status:"not_approved"}`), contrairement aux sondes locale et Hermes qui
  ont une approbation réelle déjà enregistrée : aucun hôte runner OpenHands
  n'existe aujourd'hui pour qu'une approbation ait un sens. Toute variable
  manquante (approbation, hôte SSH, fichier d'identité) produit un refus
  explicite nommant exactement le prérequis absent — rien ne devine, rien
  ne spawn.
- `codex-acp-cli` reçoit un message de lacune spécifique et nommé (pas
  l'abstention générique) : le candidat `integrations/openhands-codex-runtime/`
  n'expose aucune commande de lecture de statut de connexion non
  interactive aujourd'hui (seulement `login` interactif et le protocole
  ACP complet) — documenté, jamais contourné en parlant ACP JSON-RPC ici.
- Câblée comme nouveau défaut du gate (`DEFAULT_CONNECTION_PROBE`,
  remplace l'ancien `DEFAULT_UNVERIFIABLE_PROBE`). **Comportement observable
  inchangé dans cet environnement** : toujours `unknown` pour les deux
  fournisseurs, donc `confirm_launch` reste honnêtement bloqué — la
  différence est structurelle (une vraie sonde testable existe et est
  câblée), pas comportementale.

Tests directs : `src/server/agents/models/runner-executor-connection-probe.test.mjs`,
16 cas, **16 passés** — environnement, approbation absente, préréquis SSH
manquants un par un, classification réutilisée (connecté/bloqué/inconnu),
lacune Codex nommée, abstention générique, construction par défaut
(aucun SSH réel ne part jamais dans ces tests : l'approbation bloque avant
tout spawn).

## § 3. Révocation fermée — identité mission/workspace/approbation, pas seulement statut

Nouvelle fonction pure exportée, `approvalStillAuthorizes` (dans
`model-emission-launch-gate.ts`), appelée une seconde fois juste avant de
déléguer au vrai commit (`deps.launch`). Compare le réenregistrement frais
à celui qui a servi à la décision par **identité** (`id`, `approvedBy`,
`approvedAt`), jamais par statut seul : une approbation différente qui dit
encore "approved" (révocation suivie d'une approbation non liée, ou
substitution) est refusée tout autant qu'une vraie révocation. Réutilise
`deriveMissionApprovalConfirmation` existant, n'invente aucun second
mécanisme de dérivation. Nouveau statut `approval_changed_before_commit`.

Fenêtre résiduelle, documentée explicitement dans l'en-tête du fichier (pas
cachée) : entre ce second relevé et le `compareAndSwap` réel de
`openhands-launch-store.ts` — même nature de fenêtre, déjà acceptée pour la
valeur MISSION elle-même. Fermer complètement nécessiterait une transaction
réelle partageant les deux tables (`missions`, `mission_approvals`), hors
périmètre et non inventée comme nouvelle couche.

Tests directs ciblés sur la fonction pure (indépendants du chantier Cursor
en cours — voir § 5) : révocation, absence de réenregistrement, expiration
découverte au second relevé, substitution ("mauvais compte" — même statut
"approved", identité différente), et stabilité sous concurrence (deux
lectures identiques du même enregistrement autorisent toujours) —
**6 cas, 6 passés**. Un test de non-régression confirme que le
réenregistrement n'est jamais atteint quand le gate bloque déjà pour une
autre raison (connexion/autorisation).

## § 4. Budgets préservés, aucun élargissement de plafond

Aucun champ `maxCostCents`/`maxTokens`/`maxIterations`/`timeoutSeconds` ni
leur validation touché. `src/server/ai/*` (Cursor) non modifié. Voir
`docs/CLAUDE-APPROVED-SERVER-BINDING-RACCORDEMENT-REQUIS-2026-10-02.md`
pour le raccordement `ApprovedServerBinding` requis, documenté sans
modifier le code Cursor, avec la découverte faite en cours de lot que
Cursor modifie `src/server/ai/` en parallèle dans le même worktree.

## § 5. État des tests — ce qui est à moi, ce qui est préexistant

`npx tsc --noEmit` sur tout le dépôt Oria.HQ : **14 erreurs, stables**,
confinées à `src/server/ai/llm-json-provider.ts` (9),
`src/server/ai/model-router.ts` (3), `src/server/missions/model-emission-gate.ts`
(2) — aucune dans un fichier touché par ce lot. Cause exacte et preuve :
voir le document ApprovedServerBinding.

`node --test src/server/missions/model-emission-launch-gate.test.mjs` :
24 passés / 4 échecs. Les 4 échecs sont **préexistants**, pas écrits par ce
lot, et échouent pour la même cause runtime que `model-emission-gate.test.mjs`
(11/11 échecs, fichier jamais touché) — prouvé par comparaison directe.
Tous les tests ajoutés ou modifiés par ce lot passent : alignement du
registre (binding pur, 2 cas), sonde runner (16 cas), `approvalStillAuthorizes`
(6 cas), non-régression du court-circuit existant (1 cas).

`node --test src/core/openhands-launch-contract.test.mjs` : 6/6 (hérité du
lot politique précédent, revérifié intact).

`node --test src/server/missions/*.test.mjs` (dossier complet) : 215 passés,
le reste des échecs se décompose en (a) le chantier Cursor ci-dessus et
(b) deux lacunes intentionnelles déjà trackées comme telles par le projet
(`openhands-launch-model-connection-gap.test.mjs`, convention
`*-gap.test.mjs` du dépôt — rouge par construction tant qu'elles ne sont
pas câblées, non liées à ce mandat).

## § 6. Oria.HQ non commité — décision délibérée

Ce job a entré le worktree Orchestrator via l'outil dédié (donc commité et
poussé ci-dessous), mais n'a PAS entré le worktree Oria.HQ
`hq-acces-reprise` via cet outil — il a travaillé dedans directement, comme
demandé par le mandat (`"Travaille dans ton worktree codex-acp-candidate
existant; produit compagnon [chemin Oria.HQ]"`). La consigne de session
est claire sur ce point : ne jamais commiter dans un worktree qu'on n'a pas
soi-même entré sans demander d'abord. Les fichiers modifiés/ajoutés côté
Oria.HQ restent donc **non commités**, à côté du travail Cursor déjà en
cours (non touché, préservé intégralement) :

```
 M src/app/api/orchestration/openhands/route.ts
 M src/core/openhands-launch-contract.ts            (lot précédent, déjà en place)
 M src/server/missions/model-emission-launch-gate.ts
 M src/server/missions/model-emission-launch-gate.test.mjs
?? src/core/openhands-launch-contract.test.mjs       (lot précédent, déjà en place)
?? src/server/agents/models/runner-executor-connection-probe.ts
?? src/server/agents/models/runner-executor-connection-probe.test.mjs
```

(Les fichiers `src/server/ai/*` et `src/server/ai/server-capability-catalog.test.mjs`
visibles dans `git status` à côté de ceux-ci sont le travail Cursor en
cours — non touchés par ce lot, non commités par ce lot.)

## Commandes reproductibles

```sh
# Orchestrator — déjà commité et poussé par ce lot
cd C:/Users/micha/Documents/ChatGPT/Orchestrator/.claude/worktrees/codex-acp-candidate
git log --oneline -3

# Oria.HQ — à exécuter depuis le worktree compagnon, rien n'est commité
cd C:/Users/micha/Dev/Oria.HQ/.claude/worktrees/hq-acces-reprise
npx tsc --noEmit
node --test src/server/missions/model-emission-launch-gate.test.mjs
node --test src/server/agents/models/runner-executor-connection-probe.test.mjs
node --test src/core/openhands-launch-contract.test.mjs
```

## Prochains prérequis (hors périmètre de ce lot)

1. Qualifier un vrai hôte runner OpenHands (Claude et/ou Codex) pour que
   `RUNNER_EXECUTOR_PROBE_APPROVAL` cesse d'être `not_approved` — approbation
   écrite réelle de Michael requise avant tout spawn SSH.
2. Côté Cursor : terminer le patch `ApprovedServerBinding` (en cours,
   observé pendant ce lot), puis raccorder `model-emission-gate.ts` —
   `accountId` dérivé de la preuve de connexion réelle, `revision` dérivé
   du `policySha256` de la policy qualifiée (recommandation documentée,
   rien codé).
3. Exposer une lecture de statut non interactive côté candidat
   `openhands-codex-runtime` avant qu'un probe Codex réel puisse exister
   sans deviner.
4. Qualifier Gemini CLI séparément d'Antigravity, comme déjà cadré dans
   `docs/HQ-ABONNEMENTS-EXECUTANTS.md` — non touché par ce lot.
