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
leur validation touché. `src/server/ai/*` (Cursor) non modifié.

## § 4bis. Complément 2 octobre 2026 — `ApprovedServerBinding` raccordé, preuve de lancement obtenue

Suite à `docs/CLAUDE-COMPLEMENT-DIRECTION-ACP.md` : le patch Cursor
`ApprovedServerBinding` est confirmé appliqué et stable (`src/server/ai/*.test.mjs` :
**106/106, zéro skip**, revérifié). Lu `server-capability-catalog.ts` et
`llm-json-provider.ts` **sans modification** pour comprendre le contrat réel
avant de raccorder quoi que ce soit.

Découverte en lisant `llm-json-provider.ts` : `assessServerEmission` refuse
désormais explicitement d'ÉMETTRE (appel JSON mesuré) une capacité
`billingKind: "subscription"`/`"verified_free"` — nouveau variant
`{emit:false, disposition:"non_api", capability, billingKind}`. C'est
correct pour le chemin JSON de Cursor (un abonnement ne peut structurellement
pas être mesuré par appel), mais ce n'est **pas** "cette capacité est
inutilisable partout" : une exécution OpenHands n'appelle jamais le modèle
via JSON mesuré — la session CLI d'abonnement EST l'exécution. C'est la
phrase du mandat rendue concrète une seconde fois : *"non_api_authorized ne
vaut pas exécution"* se lit dans les deux sens — ni comme un succès
automatique, ni comme un échec automatique ; chaque appelant doit décider ce
que "non_api" signifie pour son propre chemin, jamais le supposer.

**`model-emission-gate.ts` raccordé** (hors périmètre nommé à l'origine, mais
nécessaire pour "terminer le mandat" — sans ce fichier compilable, aucune
preuve de lancement n'est possible) :
- `ModelEmissionGateRequest` porte deux nouveaux champs requis, `accountId`
  et `catalogRevision` — jamais optionnels, jamais inventés par défaut.
- Validés dans le même bloc `invalid_request` que les autres champs requis.
- Stampés sur l'unique `ServerCapability`/`ServerCapabilityCatalog`
  synthétique que ce module construit, et transmis à `assessServerEmission`
  (`accountId` toujours fourni, contrairement à Cursor qui le rend optionnel
  pour son propre usage).
- Aucune logique de blocage existante modifiée (budget_missing, staleness,
  workspace/provider mismatch — tout intact).

**`model-emission-launch-gate.ts` raccordé** :
- `accountId` = `providerProfile.id` (l'identité qualifiée qui traverse déjà
  tout le `LaunchConfig` confirmé — la sonde de connexion n'expose
  délibérément rien de plus fort, voir § 2). `catalogRevision` =
  `providerProfile.policySha256` (le digest déjà verrouillé par le schéma et
  par `provider_policy.py`). Les deux sont des identités réelles déjà
  qualifiées, jamais fabriquées à la volée — exactement ce que
  "pas branchement fictif" interdit de faire autrement.
- Nouvelle condition de succès explicite, `subscriptionAuthorized` :
  `disposition === "non_api" && billingKind === "subscription"`, **re-vérifié**
  contre les mêmes `accountId`/`workspaceId`/`modelId` demandés (belt-and-
  braces — structurellement garanti par construction puisque ce gate ne
  construit jamais qu'une seule entrée, mais vérifié explicitement plutôt que
  supposé, conformément à "aucun profil générique ne doit contourner contrôle
  compte/modèle/approbation"). `apiAuthorized` (`emit===true`) conservé pour
  un futur exécuteur réellement facturé à l'appel — aucun n'existe aujourd'hui.

**Preuve minimale de lancement obtenue** : avec un plan Claude lié, une
approbation vérifiée et une sonde de connexion (même injectée/hypothétique en
test) qui répond "connecté", la chaîne complète — alignement de registre,
sonde, réassessment Cursor, re-vérification de révocation — appelle
réellement `deps.launch` et retourne `{status:"claimed",...}`. Avant ce
complément, c'était structurellement impossible : `model-emission-gate.ts`
ne compilait même pas, et la logique de succès de `model-emission-launch-gate.ts`
visait une branche (`emit:true` pour un abonnement) que le nouveau contrat
Cursor ne produit plus jamais.

## § 5. État des tests — ce qui est à moi, ce qui est préexistant

`npx tsc --noEmit` sur tout le dépôt Oria.HQ : **12 erreurs, stables,
confinées à 2 fichiers exclusivement Cursor** — `src/server/ai/llm-json-provider.ts`
(9), `src/server/ai/model-router.ts` (3). `model-emission-gate.ts` et
`model-emission-launch-gate.ts` : **0 erreur**, confirmé après le
raccordement ci-dessus. Les 12 erreurs restantes sont le même type d'erreur
(un narrowing TypeScript sur `assessment.disposition` manquant avant lecture
de `.block`/`.billingKind`) répété dans le code Cursor lui-même — non
touché, non corrigé par ce lot.

`node --test src/server/missions/model-emission-gate.test.mjs` :
**21/21, zéro échec** (10 tests réécrits pour le nouveau contrat `disposition`,
2 tests nouveaux pour `accountId`/`catalogRevision` requis, 9 inchangés).

`node --test src/server/missions/model-emission-launch-gate.test.mjs` :
**28/28, zéro échec** — les 3 échecs préexistants documentés précédemment
(causés par le chantier Cursor alors en cours) sont maintenant **tous
verts**, sans qu'aucune de leurs assertions n'ait dû être affaiblie. Le test
TOCTOU déjà corrigé au tour précédent (`2`→`4` sondes) reste vert.

`node --test src/server/ai/*.test.mjs` (Cursor) : **106/106, zéro skip**,
revérifié intact — rien modifié.

`node --test src/core/openhands-launch-contract.test.mjs` : 6/6, intact.

`node --test src/server/agents/models/runner-executor-connection-probe.test.mjs` :
16/16, intact.

`node --test src/server/missions/*.test.mjs` (dossier complet) : **zéro
échec** hors des deux lacunes intentionnelles déjà trackées par le projet
(`openhands-launch-model-connection-gap.test.mjs`, convention
`*-gap.test.mjs` — rouge par construction, non liées à ce mandat).

Combiné (`ai/*` + `missions/model-emission-gate` + `missions/model-emission-launch-gate`
+ `runner-executor-connection-probe` + `openhands-launch-contract`) :
**zéro échec, toutes suites confondues.**

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
 M src/server/missions/model-emission-gate.ts
 M src/server/missions/model-emission-gate.test.mjs
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
   écrite réelle de Michael requise avant tout spawn SSH. C'est la **seule**
   chose qui sépare encore ce gate d'un lancement réel : la logique est
   maintenant prouvée correcte de bout en bout (§ 4bis), il ne manque qu'un
   hôte et une connexion réelle — jamais une copie de jeton.
2. Exposer une lecture de statut non interactive côté candidat
   `openhands-codex-runtime` avant qu'un probe Codex réel puisse exister
   sans deviner.
3. `accountId` reste aujourd'hui un proxy honnête (`providerProfile.id`),
   jamais une identité de compte humaine/API réelle — la sonde expose
   délibérément moins que ça (§ 2). Si un identifiant de compte plus fort
   doit un jour exister, c'est une décision séparée sur ce qu'il est sûr
   d'exposer, pas une extension silencieuse de ce lot.
4. Les 12 erreurs TypeScript restantes (`llm-json-provider.ts`,
   `model-router.ts`) sont internes au code Cursor — narrowing manquant sur
   `assessment.disposition` avant lecture de `.block`/`.billingKind`, même
   classe d'erreur que celle corrigée ici côté HQ. Signalé, pas corrigé :
   fichiers hors périmètre.
5. Qualifier Gemini CLI séparément d'Antigravity, comme déjà cadré dans
   `docs/HQ-ABONNEMENTS-EXECUTANTS.md` — non touché par ce lot. Antigravity
   vérifie séparément les possibilités ACP sans toucher au backend, par
   ailleurs.
