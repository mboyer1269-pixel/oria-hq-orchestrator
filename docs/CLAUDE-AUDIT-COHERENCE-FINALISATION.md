# Audit de cohérence — finalisation du plan HQ

**Auteur :** Claude Code (session revue spécialisée indépendante)
**Date :** 30 septembre 2026
**Mandat :** revue indépendante en lecture seule du code HQ pour finaliser le plan complet. Livrable unique : ce fichier.
**Autorisé par :** Michael.

---

## 1. Périmètre, méthode et limites

### Sources lues

| Source | Référence exacte | Rôle |
| :--- | :--- | :--- |
| Plan de consolidation | `PLAN-HQ-CONSTRUCTEUR.md` §« Plan de consolidation actuel », lignes 3-30 | exigences de sortie |
| Direction commune | `docs/HQ-DIRECTION-COMMUNE-HERMES.md` | propriétaires et critère final |
| Règles dépôt produit | `C:/Users/micha/Dev/Oria.HQ/AGENTS.md` | garde-fous, validation obligatoire |
| Code HQ | `C:/Users/micha/Dev/Oria.HQ`, branche `codex/hq-mission-dossier`, HEAD `e9ff840`, arbre propre | objet de la revue |
| Lot backend Antigravity | WSL `/home/michael_/.gemini/antigravity/scratch/oria-hq-intake-bridge`, branche `antigravity/hq-intake-bridge-handoff`, HEAD `d4ce3d7` (4 commits au-dessus de `e9ff840`), arbre propre | lecture seule |

### Zones examinées

`src/server/auth/` (owner, user-context, workspace-context) · admission des missions (`src/server/missions/`, `src/app/api/missions/development/`, `src/app/api/orchestration/openhands/`) · `src/server/ai/model-router.ts` et `src/server/ai/cost-ladder.ts` · front mission (`src/features/missions/`, `src/app/hq/missions/page.tsx`, `src/app/hq/runtime/page.tsx`).

### Méthode de preuve

- Lecture de code uniquement sur `Oria.HQ` et sur le lot Antigravity. **Aucun fichier d'un autre agent n'a été modifié. Aucun secret, `.env` ni credential lu ou écrit. Aucun appel de modèle externe. Aucune action sur la production.**
- Une reproduction exécutable a été faite **hors du dépôt** (script jetable dans le répertoire temporaire de cette session, chargé via le `jiti` déjà présent dans `Oria.HQ`), sur les fonctions pures du routeur et de l'échelle de coût. Aucun provider contacté, aucun fichier du dépôt touché. Les sorties mesurées sont citées verbatim dans les constats 2 et 3.
- Le lot Antigravity a été lu via WSL en lecture seule. **Sa reproduction en exécution n'a pas été faite** (la session a ensuite été isolée dans un worktree qui interdit l'appel WSL) : les constats 5 et 7 sur le CLI reposent sur la lecture du code et du rapport, pas sur une exécution observée.

### Non-duplication assumée

- **Identification du runtime Hermes** : périmètre de l'autre session Claude. Je ne la refais pas et n'avance aucune capacité Hermes. Je signale seulement, au constat 7, qu'un autre lot a écrit une identification Hermes figée **hors de son périmètre déclaré**.
- **Contrôleur de preuves** : périmètre de Cursor (`integrations/qualification-evidence/`). Je ne reproduis pas son travail ; les écarts rapport/preuve que je cite sont là pour qu'il les instruise, pas pour les trancher.

### Limites explicites

Ce n'est pas un audit exhaustif des 15 domaines du produit ni une revue de sécurité complète. 8 constats priorisés, choisis parce qu'ils bloquent ou faussent le parcours « demande → mission → exécution → preuve ». Aucun test `npm run typecheck/lint/build/smoke` n'a été rejoué : je n'ai rien modifié dans `Oria.HQ`, donc je n'ai rien à valider au sens d'`AGENTS.md`.

---

## 2. Les 8 constats prioritaires

| # | Constat | Classe | Impact utilisateur | Responsable proposé |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Barrière propriétaire des 44 routes API contournable par une propriété globale, sans garde production | **bug certain** | autorisation désactivable sur tout `/api`, exécution d'agent incluse | propriétaire app HQ (à désigner) |
| 2 | Budget du Cost Ladder débité par décision de routage, en mémoire, sans dimension workspace | **bug certain** | compteur de coût faux ; dégradation réelle du routage après ~50 tours | propriétaire app HQ |
| 3 | Message « rétrogradé vers l'étage gratuit » affiché alors que le modèle payant économie est retenu | **bug certain** | explication fausse donnée à l'opérateur sur un basculement de coût | propriétaire app HQ |
| 4 | Après rechargement, le formulaire de mission transforme un enregistrement en relecture et affiche l'ancien titre | **bug certain** | l'opérateur croit avoir créé une mission ; rien n'est écrit | propriétaire app HQ |
| 5 | Les échecs antérieurs à toute écriture sont rendus comme « résultat incertain » | **bug certain** | l'état « issue inconnue », pivot du plan, est fabriqué à tort et bloque l'opérateur | propriétaire app HQ + Antigravity (CLI) |
| 6 | Deux autorités d'admission des missions, avec deux formes d'identité, sur la même table | **dette de conception** | traçabilité d'acteur ambiguë sur la table `missions` | Codex (arbitrage) + Antigravity (CLI) |
| 7 | Le lot Antigravity rejoue la simulation mémoire déjà refusée et fige une identification Hermes hors périmètre | **bug certain (preuve)** | un commit annonce la chaîne complète « qualifiée » sans exécution réelle | Antigravity, acceptation Cursor/Codex |
| 8 | Insert-or-ignore global sur l'id puis relecture cloisonnée workspace : conflit d'un autre workspace rendu comme incertitude irrécupérable | **hypothèse** | blocage définitif sur un identifiant de demande, sans explication | Antigravity (harnais réel) pour qualifier |

Chemins relatifs à `C:/Users/micha/Dev/Oria.HQ`, sauf mention WSL.

---

### Constat 1 — La barrière propriétaire des routes API est contournable par une propriété globale

**Classe : bug certain** (défaut de défense en profondeur ; aucun module de production ne pose la propriété aujourd'hui).

**Preuve.** `src/server/auth/owner.ts:96-103` :

```ts
export async function requireOwnerApiSession(): Promise<NextResponse | null> {
  const globals = globalThis as typeof globalThis & {
    __ownerApiSessionTestResult?: NextResponse | null;
  };
  if (Object.prototype.hasOwnProperty.call(globals, "__ownerApiSessionTestResult")) {
    return globals.__ownerApiSessionTestResult ?? null;
  }
  const user = await getCurrentAuthUser();
```

La dérivation est consultée **avant** toute vérification de session et **sans garde d'environnement**. Retourner `null` signifie « autorisé ». Le même motif est correctement gardé ailleurs dans le dépôt — `src/server/arena/get-arena-service.ts:12-21` commence par `if (process.env.NODE_ENV === "production") return defaultArenaEvaluationService;`.

Portée mesurée : 44 fichiers de route sous `src/app/api` appellent `requireOwnerApiSession` (`grep -rln "requireOwnerApiSession" src/app/api | wc -l` → 44), dont `src/app/api/agents/[agentId]/execute/route.ts`, `src/app/api/agents/execution-intents/[intentId]/approve/route.ts` et `src/app/api/orchestration/missions/dispatch/route.ts`.

**Reproduction sans production.** Les tests du dépôt font exactement ce geste : `globalThis.__ownerApiSessionTestResult = null` à `src/server/orchestration/paperclip-read.test.mjs:82` et `src/server/agents/execution-intent-rail-api.test.mjs:90`. Dans un processus Node, poser cette propriété puis appeler `requireOwnerApiSession()` retourne `null` sans aucune session Supabase. Aucun déploiement nécessaire.

**Impact utilisateur.** Tout code capable de poser une propriété sur `globalThis` côté serveur — un utilitaire de test importé par mégarde dans un bundle, une dépendance compromise, un crochet d'instrumentation — désactive silencieusement l'autorisation propriétaire sur l'ensemble de l'API, y compris l'approbation d'intentions d'exécution et le dispatch de missions. Aucune trace n'apparaît : la fonction ne journalise pas sa dérivation.

**Correction minimale.** Encadrer la dérivation exactement comme `get-arena-service.ts` :

```ts
if (process.env.NODE_ENV !== "production"
    && Object.prototype.hasOwnProperty.call(globals, "__ownerApiSessionTestResult")) {
```

Deux lignes, aucun test existant cassé (tous tournent hors production). **Responsable :** le dépôt `Oria.HQ` n'a aujourd'hui aucun propriétaire d'écriture déclaré pour `src/server/auth/` (voir §3, exigence 1) — à désigner par Michael ; Codex peut arbitrer.

---

### Constat 2 — Le budget du Cost Ladder compte des décisions, pas des appels, en mémoire et sans workspace

**Classe : bug certain.**

**Preuve.** Le débit se fait dans la décision de routage, pas au point d'appel. `src/server/ai/model-router.ts:301-303` :

```ts
const estimatedCost = rung === decision.rung ? decision.estimatedCost : RUNG_COST_WEIGHT.economy;
store.add(agentId, dayKey, estimatedCost);
```

`applyCostLadder` est invoqué depuis `chooseModel` (`model-router.ts:396`), qui ne contacte aucun provider. Trois sites de débit :

- `src/server/joris/brain.ts:297-307` — route pré-intention, `taskClass:"general"`, à chaque tour de conversation ;
- `src/server/joris/brain.ts:384-394` — route post-intention, `taskClass: taskClassForIntent(intent)`, dans le même tour ;
- `src/server/missions/mission-draft-control.ts:44-55` (`buildRoute`, appelé en `:109` pour « annule » et `:151` pour « confirme »), avec `agentId:"mission"` codé en dur. Le commentaire de ce site dit lui-même « No provider call changes » — et débite pourtant.

Le magasin : `src/server/ai/cost-ladder.ts:290-300`, `Map` en mémoire dont la clé est `` `${agentId}::${dayKey}` `` — **aucune dimension workspace** ; `model-router.ts:261` en fait un singleton de module ; `resetLadderBudget()` (`model-router.ts:264`) n'est appelé que par les tests, donc la `Map` croît sans purge de fin de journée. Budget par défaut : 100 unités (`cost-ladder.ts:79`), poids `free 0 / economy 1 / premium 5` (`cost-ladder.ts:72-76`).

**Reproduction sans production** (fonctions pures, script hors dépôt, aucun provider) :

```
spend après UN tour de conversation ordinaire (2 appels chooseModel) : 2
spend après UN tour « consulte le board » ajouté                     : 12
tours de conversation ordinaires pour atteindre le budget du jour     : 50   spend: 100
```

Un tour ordinaire coûte 2 unités ; un tour « board » en coûte 10 (les deux routes du tour atterrissent en premium via le mot-clé stratégique) ; **50 tours** suffisent à épuiser le budget quotidien, sans qu'aucun appel de modèle n'ait eu lieu.

**Impact utilisateur.** Deux effets distincts.
1. `/hq/runtime` affiche « Coût estimé » et « Budget-bound » depuis ce journal (`src/app/hq/runtime/page.tsx:110`, puis `:280-284`). L'encart est honnête sur la base (`basis: estimated/in-memory only`, « pas de facturation réelle, pas de persistance ») mais **pas** sur le fait que l'unité comptée est une décision de routage et non un appel : le même tour de conversation est compté deux fois, et une confirmation de brouillon est comptée comme une dépense. Le nombre ne mesure donc ni une dépense ni une activité modèle. Il repart à zéro à chaque redémarrage de processus et diverge entre instances.
2. Passé le seuil, le comportement **réel** du routage change pour le reste de la journée-processus (voir constat 3). Une consommation fictive provoque donc une dégradation réelle.

**Correction minimale.** Débiter au point d'appel, là où une réponse provider est effectivement obtenue, et laisser `chooseModel` sans effet de bord ; porter la clé à `workspaceId::agentId::dayKey` ; en attendant un magasin durable, étiqueter l'indicateur « décisions de routage observées », pas « budget ». Le plan (§5 : « Budget durable et contrôle au point d'appel à qualifier ») demande déjà cette qualification : ce constat en est la preuve négative. **Responsable :** propriétaire app HQ.

---

### Constat 3 — « Rétrogradé vers l'étage gratuit » est affiché alors que le modèle payant économie est retenu

**Classe : bug certain.**

**Preuve.** Dans `src/server/ai/cost-ladder.ts`, `budgetBound` est calculé **avant** le repli, puis le rung passe de `free` à `economy` quand aucun modèle gratuit n'est éligible :

```
224  const budgetBound = overBudget && RUNG_ORDER[rung] < RUNG_ORDER[targetRung];
229  if (rung === "free") {
230    freeModel = selectFreeModel(input.freeCatalog);
231    if (!freeModel) {
233      rung = "economy";
234      noFreeAvailable = true;
```

`buildReason` teste ensuite `budgetBound` (`:268`) **avant** `noFreeAvailable` (`:274`), et renvoie donc le message de rétrogradation gratuite alors que le rung final est `economy`.

Ce chemin n'est pas théorique : `freeCatalog` n'est fourni par **aucun** appelant — `model-router.ts:288` lit `input.freeCatalog ?? []`, et ni `brain.ts` ni `mission-draft-control.ts` ne renseignent le champ. L'étage gratuit est donc toujours vide, et le repli vers `economy` est le seul comportement possible dès que le budget est atteint.

**Reproduction sans production** (mêmes fonctions pures) :

```
decideLadder({taskClass:'general',baseRung:'economy',freeCatalog:[],currentSpend:100,dailyBudget:100})
→ {"rung":"economy","budgetBound":true,"estimatedCost":1,
   "reason":"Budget agent du jour atteint: routage rétrogradé vers l'étage gratuit."}

chooseModel après épuisement → modelId: gpt-4o-mini | mode: economy | via: cost-ladder
reason affichée              → "Budget agent du jour atteint: routage rétrogradé vers l'étage gratuit."
```

**Impact utilisateur.** La raison de routage est transportée dans `ModelRouteDecision.reason` (`model-router.ts:409-415`) et enregistrée comme `routeReason` dans le journal de route (`model-router.ts:375-384`). L'opérateur et le journal affirment donc un basculement vers un étage gratuit qui n'a pas eu lieu : l'appel reste sur le modèle payant `gpt-4o-mini`. C'est précisément le « faux état » et le « basculement non conforme à ce qui est annoncé » que le plan interdit (§5 : « Aucun basculement silencieux payant » ; §4 : « retour observable »).

**Correction minimale.** Recalculer `budgetBound` **après** le repli, et ordonner `buildReason` pour que `noFreeAvailable` précède `budgetBound` (ou composer les deux : « budget atteint, aucun modèle gratuit éligible : repli économie payante »). Trois lignes dans `cost-ladder.ts`. **Responsable :** propriétaire app HQ.

---

### Constat 4 — Après rechargement, le formulaire de mission relit un ancien reçu au lieu d'enregistrer

**Classe : bug certain, interface.**

**Preuve.** `src/features/missions/components/development-mission-form.tsx:11`, dans `run()` :

```ts
const previous = sessionStorage.getItem(key);
...
id = requestId ?? previous ?? crypto.randomUUID();
if (previous && !requestId) readOnly = true;
```

`requestId` est un `useState<string|null>(null)` (`:7`) et **n'est jamais réhydraté** depuis `sessionStorage` — aucun `useEffect` dans le composant. Après un rechargement de page, `requestId` est donc `null` tandis que `sessionStorage` conserve l'identifiant. Un envoi (`run(false)`) est alors converti en relecture, et la construction du payload (`:12`, gardée par `!readOnly`) est sautée.

**Reproduction sans production** (dev local, `/hq/missions`) :
1. remplir les quatre champs, cliquer « Enregistrer le brouillon » → reçu `saved` ;
2. recharger la page (F5) **sans** cliquer « Préparer une autre mission » ;
3. le bouton « Enregistrer le brouillon » est de nouveau affiché (`:22`, conditionné par `!requestId`), les champs sont éditables ; saisir un **nouveau** titre et un nouveau périmètre ;
4. cliquer « Enregistrer le brouillon ».

Observé par le code : la requête partie est `GET /api/missions/development?requestId=<ancien id>` (`:14`), pas un `POST`.

**Impact utilisateur.** La ligne d'état (`:23`) affiche `Mission enregistrée : <titre de la mission précédente>` et le bouton d'enregistrement disparaît. L'opérateur conclut qu'une nouvelle mission de développement a été admise ; **aucune écriture n'a eu lieu** et le contenu qu'il vient de saisir est perdu. Si l'ancien reçu a disparu côté serveur, il obtient « Aucune mission retrouvée avec cet identifiant », sans aucune indication que sa saisie a été ignorée. Le plan exige (§4) que « chaque contrôle ait effet » et un « retour observable » ; ici le contrôle ment sur son effet.

**Correction minimale.** Réhydrater `requestId` depuis `sessionStorage` au montage, afin que l'affordance de reprise (`:24` « Vérifier le dernier reçu » / `:25` « Réessayer avec le même identifiant ») remplace le bouton d'enregistrement ; et distinguer dans la ligne d'état un reçu **relu** (« reçu existant : … ») d'une mission **enregistrée**. **Responsable :** propriétaire app HQ.

---

### Constat 5 — Les échecs antérieurs à toute écriture sont rendus comme « résultat incertain »

**Classe : bug certain.**

**Preuve.** Trois sites fusionnent « l'écriture a peut-être eu lieu » et « on a échoué avant de toucher la base ».

1. `src/app/api/missions/development/handlers.ts:13` — un seul `try/catch` enveloppe la résolution de contexte **et** la création :
   ```ts
   try{return json(await deps.create(parsed.data,{...deps.context(),actorId:actor.actorId}));}
   catch{return json({status:"outcome_unknown"},503);}
   ```
   `deps.context()` (câblé en `src/app/api/missions/development/route.ts:7` sur `getActiveWorkspaceContext()`) remonte jusqu'à `getServerUserContext()`, qui **lève volontairement** quand aucun propriétaire réel n'est configuré (`src/server/auth/user-context.ts:53-59`). Une erreur de configuration devient donc une incertitude d'écriture.
2. `src/server/missions/development-mission.ts:36-39` — le `catch` couvre à la fois `store.save` et la vérification post-écriture de `:37` ; toute exception retourne `outcome_unknown`.
3. CLI du lot Antigravity, WSL `src/scripts/development-mission.mjs:46-48` — un `catch` nu transforme un `argv` invalide, un fichier de configuration illisible, un échec de parse Zod et un stdin surdimensionné en `{status:'outcome_unknown'}`, code de sortie 2.

**Reproduction sans production.** Sites 1 et 2 : appeler le handler avec un `context()` qui lève (c'est le comportement nominal de `getServerUserContext()` sans `MICHAEL_HQ_OWNER_ID` hors production) → HTTP 503 `{"status":"outcome_unknown"}`. Site 3 : `node src/scripts/development-mission.mjs` sans argument, ou avec un chemin de configuration inexistant, suit les lignes 18-21 puis le `catch` final → `{"status":"outcome_unknown"}`. **Cette exécution du CLI n'a pas été faite** (isolation worktree ⇒ WSL indisponible en fin de session) : le constat repose sur la lecture du code.

**Impact utilisateur.** Le message rendu est, dans l'interface, « Résultat incertain. Aucun nouvel identifiant ni renvoi automatique : vérifie le reçu. » (`development-mission-form.tsx:20`). Le plan s'appuie précisément sur cet état pour **bloquer une relance aveugle** (§3 : « L'issue inconnue reste visible et bloque la relance aveugle »). Le fabriquer pour des échecs qui n'ont provablement rien écrit dévalue le seul signal de sécurité du parcours et envoie l'opérateur vérifier un reçu qui ne peut pas exister. À l'inverse, un vrai doute d'écriture devient indiscernable du bruit.

**Correction minimale.** Séparer le `catch` : échec avant toute tentative d'écriture → `invalid_request` (400) ou `unavailable` (503) ; `outcome_unknown` réservé à un échec **après** la tentative. Le motif existe déjà dans le dépôt : `src/server/missions/openhands-launch.ts:78,97,109` porte un drapeau `attempted` et choisit `reconciliation_required` ou `unavailable` selon ce drapeau — le réutiliser tel quel. **Responsables :** propriétaire app HQ pour les sites 1-2 ; Antigravity pour le site 3 (son fichier).

---

### Constat 6 — Deux autorités d'admission des missions, deux formes d'identité, une seule table

**Classe : dette de conception** (certaine sur la traçabilité ; l'intégrité des données reste protégée, voir ci-dessous).

**Preuve.** Deux chemins écrivent dans `missions` via `createDevelopmentService()` avec des règles d'identité incompatibles.

- **HTTP** — `src/app/api/missions/development/route.ts:7` : session Supabase obligatoire (`getCurrentAuthUser`), autorisation propriétaire (`isOwnerUser`), `actorId = user.id` (UUID Supabase), workspace et mode imposés côté serveur par `getActiveWorkspaceContext()`.
- **CLI** (lot Antigravity, WSL) — `src/scripts/development-mission.mjs:19-25` et `:43` : `workspaceId`, `modeId` et `actorId` proviennent d'un **fichier JSON local passé en `argv[2]`**. Aucune session, aucune vérification propriétaire ; le client Supabase service-role est utilisé via `createDevelopmentService()`. Le harnais de chaîne du même lot passe `actorId:"hermes"` (`proofs/prove-hermes-intake-openhands-chain.mjs:36,157`) et `workspaceId:"michael-hq"`.

Divergence d'identité **à l'intérieur même du chemin HTTP** : `src/server/auth/owner.ts:24-31` autorise sur l'identifiant **ou** le courriel, tandis que `src/core/workspace-context.ts:31-33` et `src/server/auth/user-context.ts:42-49` dérivent le workspace **et** `currentOwnerUser.id` de la configuration `MICHAEL_HQ_OWNER_ID`. Le dépôt documente lui-même ce décalage (`owner.ts:56-69`) et a introduit `getAuthenticatedActorId()` pour l'attribution au ledger — mais le côté workspace reste dérivé de la configuration. Une session valide par courriel, dont l'`id` Supabase diffère de la configuration, agit donc sous une identité de workspace qui n'est pas la sienne.

**Garde-fou existant, à créditer.** `src/server/missions/development-mission.ts:33` inclut `actorId` et `modeId` dans `payloadHash`, et `:37` compare ce hash après écriture. Une réutilisation du même `requestId` par un acteur différent retourne donc `conflict`, pas un écrasement silencieux. L'intégrité est préservée ; c'est la lisibilité de l'autorité qui ne l'est pas.

**Reproduction sans production.** Admettre une mission par le CLI avec `{"context":{"workspaceId":"michael-hq","modeId":"hq","actorId":"hermes"}}`, puis lister `missions` : la ligne porte `workspace_id = michael-hq` et `input.development.createdBy = "hermes"`, indistinguable au niveau colonne d'une admission HTTP authentifiée. Aucune session n'a été présentée.

**Impact utilisateur.** Le plan exige (§2) « authentification et workspace imposés côté serveur » et (§1, §Livraison commune) « une seule référence de mission et un responsable d'écriture par périmètre ». Aujourd'hui, l'origine d'une mission admise n'est pas reconstructible : un reçu attribué à `hermes` et un reçu attribué à un UUID Supabase cohabitent dans la même table et le même espace d'identifiants déterministes (`development-mission.ts:14-18`, dérivé de `workspaceId` + `requestId` seuls). Une revue d'incident ne peut pas distinguer « admis par le propriétaire connecté » de « admis par un script local ».

**Correction minimale.** Deux options, à trancher, pas à cumuler : (a) faire du CLI un simple client de la route HTTP derrière une session ou un jeton réel ; ou (b) le confiner à un préfixe de workspace non productif et inscrire `source:"cli"` dans `input.development` pour que l'origine soit lisible en base. Dans les deux cas, refuser l'admission HTTP quand `user.id !== MICHAEL_HQ_OWNER_ID` (ou dériver le workspace de la session) afin de supprimer le décalage courriel/identifiant. **Responsables :** Antigravity pour son CLI ; Codex pour arbitrer l'autorité d'admission unique.

---

### Constat 7 — Le lot Antigravity rejoue la simulation mémoire déjà refusée et fige une identification Hermes hors de son périmètre

**Classe : bug certain** sur la preuve et la déclaration ; **dette** sur le contrôle de permissions non implémenté.

**Preuve.** WSL `/home/michael_/.gemini/antigravity/scratch/oria-hq-intake-bridge`, commit `eb48ffa` dont le sujet est *« feat(backend): qualifier la chaîne complète Hermes -> mission durable -> arbitrage -> worker OpenHands »*. Ce commit n'ajoute qu'un fichier : `proofs/prove-hermes-intake-openhands-chain.mjs` (358 lignes).

- En-tête, `:1-14` : « Qualification de la chaîne complète isolée : Hermes → Admission Mission Durable HQ → Arbitrage Humain Explicite → Délégation Worker OpenHands → Preuves & Ledger ».
- `:45-48` : `// ── 2. PASSERELLE HTTP SIMULÉE EN MÉMOIRE POUR LE CONTRAT HQ ──`, `const missionsDb = new Map();`, `const server = http.createServer(...)`.
- `:147` et `:170` : ce serveur est injecté comme `NEXT_PUBLIC_SUPABASE_URL` dans l'environnement du CLI, avec `SUPABASE_SERVICE_ROLE_KEY = "synthetic-disposable-qualification-key"`.

C'est exactement le simulateur de contrat HTTP en mémoire que le lot a lui-même formellement requalifié après la revue Codex : `docs/ANTIGRAVITY-PONT-REPRISE.md:12-20` acte le renommage en `prove-cli-simulated-contract.mjs` et le retrait de toute mention de « qualification complète ». Le nouveau fichier reprend le motif sans l'étiquette.

- `:26-42` : `NOUS_HERMES_IDENTIFICATION` est une **constante codée en dur** — `hostModel:"hermes3:8b"`, `upstreamVersion:"0.15.2"`, `modelFootprintBytes: 4660000000`, « 27.62s au démarrage à froid », `verifiedDate:"2026-09-29"`. Aucune sonde à l'exécution. Or le §7 du même rapport (commit `d4ce3d7`) déclare l'identification du runtime Hermes **périmètre exclusif de la session Claude** et s'engage à ne pas la dupliquer.
- Le fichier n'apparaît dans **aucune** ligne du tableau de preuves du rapport (§5), qui liste les 12 tests unitaires CLI, le test de contrat simulé (6/6), typecheck/lint/build/smoke, et le harnais réel PostgreSQL en **BLOQUÉ (127)**. Aucune exécution de ce harnais de chaîne n'est donc consignée.

**Fait d'infrastructure vérifié.** Le rapport §2 consigne `which docker podman psql postgres postgrest` → aucun binaire trouvé, et `proofs/run-intake-real-db.sh` sort en 127 avec un blocage explicite. Déclaration honnête, et conséquence directe : **l'exigence 2 du plan — qualifier admission, concurrence, réponse perdue et redémarrage sur PostgreSQL/PostgREST réels — n'a aujourd'hui aucune preuve réelle.**

**Écart annexe, à instruire par Cursor.** Le tableau §5 crédite les 12 tests unitaires de valider « refus de symlink, config `0o600` ». Le CLI ne vérifie que `isFile()`, `isSymbolicLink()` et `size>16384` (`src/scripts/development-mission.mjs:19-21`) — **aucun contrôle de mode de fichier** ; et `src/scripts/development-mission.test.mjs` ne contient aucune assertion de permission (recherche `chmod|0600|0o6|permission|symlink` sur les 12 tests : aucune occurrence). Le `0o600` n'existe que dans le harnais, qui crée le fichier lui-même puis n'en teste rien.

**Impact utilisateur.** Un lecteur de la branche voit un commit qui annonce la chaîne complète qualifiée ; l'unique artefact exécutable derrière est un simulateur en mémoire, et une identification Hermes figée que personne n'a sondée à l'exécution. Le plan interdit exactement cela (§2 : « Aucun faux vert avec simulation » ; §Autocritique : « les tests synthétiques ne suffisent pas à déclarer cette preuve réelle acquise »). Risque concret : décider la suite du parcours sur une preuve inexistante.

**Correction minimale.** Renommer `prove-hermes-intake-openhands-chain.simulated.mjs`, inscrire la frontière simulée dans l'en-tête **et** dans le tableau §5 ; supprimer `NOUS_HERMES_IDENTIFICATION` et consommer le rapport de sonde de Claude comme dépendance déclarée, conformément au §7 que le lot a écrit ; corriger la ligne `0o600` du tableau, ou implémenter la vérification de mode dans le CLI et la couvrir d'un test. **Responsable :** Antigravity, sur ses seuls fichiers ; acceptation par Cursor et Codex. **Je n'ai modifié aucun de ces fichiers.**

---

### Constat 8 — Insert-or-ignore global sur l'id, relecture cloisonnée workspace : un conflit ailleurs devient une incertitude irrécupérable

**Classe : hypothèse** — mécanisme vérifié dans le code, déclencheur non prouvé.

**Preuve.** `src/server/missions/mission-draft-durable-repository.ts:41-68` :

```ts
const { error } = await supabase.from("missions").upsert({ id: mission.id, ... },
  { onConflict: "id", ignoreDuplicates: true });          // unicité GLOBALE sur l'id
...
const { data, error: readError } = await supabase.from("missions").select()
  .eq("id", mission.id).eq("workspace_id", mission.workspaceId).single();   // relecture CLOISONNÉE
if (readError || !data) throw new MissionDraftDurableRepositoryError("Persisted mission is unavailable in this workspace.");
```

L'insertion est ignorée sur collision d'identifiant **tous workspaces confondus** ; la relecture est restreinte au workspace de la mission et utilise `.single()`, qui échoue sur zéro ligne. Un identifiant déjà présent dans un **autre** workspace produit donc : insertion silencieusement ignorée → relecture vide → exception → `src/server/missions/development-mission.ts:39` → `outcome_unknown`, de façon **déterministe à chaque nouvelle tentative** du même `requestId`.

Le déclencheur suppose une collision d'identifiant hors du namespace UUIDv5 de `developmentMissionId` (`development-mission.ts:14-18`) : par exemple un identifiant issu de `createMissionDraftId` (`src/server/missions/mission-draft-builder.ts`), du jeu de données de démonstration (`src/features/missions/seed`), d'un import futur ou d'une restauration de sauvegarde. Je n'ai pas prouvé qu'une telle collision est atteignable aujourd'hui — d'où le classement en hypothèse.

**Reproduction sans production.** Exactement le harnais que le lot Antigravity a écrit mais n'a pas pu exécuter (`proofs/run-intake-real-db.sh`, bloqué 127) : base jetable, insérer une ligne `missions` portant l'identifiant cible sous un `workspace_id` différent, puis appeler `persistMissionDraftDurable` pour le workspace légitime. Attendu : `MissionDraftDurableRepositoryError` et, en bout de chaîne, `outcome_unknown`. **C'est le cas de test à ajouter à ce harnais.**

**Impact utilisateur.** L'opérateur est bloqué sur « Résultat incertain » pour un identifiant de demande donné, sans voie de sortie et sans savoir que la cause est une ligne existante ailleurs. Le message l'invite à vérifier un reçu que la relecture cloisonnée ne lui montrera jamais. Le plan (§3) demande que l'incertitude soit visible **et** exploitable ; ici elle est visible et sans issue.

**Correction minimale.** Remplacer `.single()` par `.maybeSingle()`, puis relire sans filtre de workspace pour distinguer trois cas : absent (→ `unavailable`), présent dans ce workspace (→ reçu), présent ailleurs (→ `conflict`, message explicite). Alternativement, qualifier l'unicité par workspace dans le schéma. **Responsable :** Antigravity pour couvrir le cas dans le harnais réel ; propriétaire app HQ pour la correction.

---

## 3. Matrice — exigences du plan de consolidation contre preuves existantes

Exigences numérotées comme dans `PLAN-HQ-CONSTRUCTEUR.md` §« Séquence de livraison et critères de sortie ».

| Exigence | Preuve existante et vérifiée | Preuve manquante | Verdict |
| :--- | :--- | :--- | :--- |
| **1. Consolider les sources** — un responsable d'écriture par fichier, une seule référence de mission | `docs/HQ-DIRECTION-COMMUNE-HERMES.md` attribue 4 périmètres. Dans le dépôt produit, `missions` est bien l'unique table de référence. | Aucun propriétaire déclaré pour `src/server/auth/`, `src/server/ai/`, `src/features/missions/` — les trois zones des constats 1 à 4. Les répertoires attribués `integrations/hermes-runtime-probe/` (Claude) et `integrations/qualification-evidence/` (Cursor) **n'existent pas** dans l'Orchestrator (vérifié sur `codex/cursor-recovery-handoff`). | **non tenue** |
| **2. Fermer le backend** — admission, concurrence, réponse perdue, redémarrage, sur PostgreSQL/PostgREST **réels** | 12 tests unitaires CLI passent (rapport Antigravity §5) ; test de contrat simulé 6/6 ; code d'admission durable fail-closed (`mission-draft-durable-repository.ts:30-40`) ; autorité OpenHands durable avec relecture canonique (`openhands-authority-store.ts:36-45`). | **Aucune exécution sur PostgreSQL/PostgREST réels** : `which docker podman psql postgres postgrest` → rien ; `run-intake-real-db.sh` → 127. Concurrence, réponse perdue et redémarrage ne sont prouvés que sur `new Map()`. Cas du constat 8 non couvert. | **bloquée (infrastructure)** |
| **2bis. Authentification et workspace imposés côté serveur** | Les routes d'admission exigent session + propriétaire (`missions/development/route.ts:7`, `orchestration/openhands/route.ts:9-14`) ; workspace jamais choisi par le client. Garde de production sur les variables critiques (`src/lib/server-env.ts:126-144`). | Barrière API contournable par propriété globale (constat 1). Workspace dérivé de la configuration et non de la session, avec autorisation courriel-ou-identifiant (constat 6). Seconde autorité d'admission sans session (constat 6). | **partielle, défauts ouverts** |
| **2ter. Aucun faux vert avec simulation** | Requalification du premier simulateur, actée et assumée (rapport Antigravity §1). Étiquette honnête sur `/hq/runtime` (`basis: estimated/in-memory only`). | Nouveau harnais « chaîne complète » bâti sur `new Map()` et annoncé comme qualification (constat 7). Claim `0o600` non soutenu par le code ni par les tests. | **non tenue** |
| **3. Relier la conversation au travail** — directive → mission unique, reconnexion et double clic sans doublon, issue inconnue visible | Admission idempotente par `requestId` avec identifiant déterministe (`development-mission.ts:14-18`) ; insert-or-ignore (`mission-draft-durable-repository.ts:59`) ; `payloadHash` incluant acteur et mode (`:33`) ; verrou de double soumission côté client (`development-mission-form.tsx:9`, `openhands-launch.tsx:15-19`) ; une question seule ne lance rien (`mission-draft-control.ts`, confirmation explicite requise). | Le parcours complet depuis Discuter n'est pas démontré. L'état « issue inconnue » est fabriqué sur des échecs sans écriture (constat 5) et sans issue sur collision ailleurs (constat 8). Après rechargement, l'enregistrement ne se produit pas (constat 4). | **partielle** |
| **4. Maquette puis frontend** — chaque contrôle a effet, états chargé/vide/erreur/indisponible, retour observable | Honnêteté réelle à créditer : `openhands-launch.tsx:27,44,50` annonce « n'est pas encore raccordé », « Aucun démarrage confirmé », « le plafond de tokens n'est pas un arrêt technique garanti » ; `missions/page.tsx:141` affiche la source réelle (Supabase / données locales) ; états vides explicites sur `/hq/runtime`. | Contrôle sans effet et retour faux au constat 4. Explication de routage fausse au constat 3. `src/features/missions/components/mission-system-status.tsx` est un tableau d'états **codé en dur** et **jamais rendu** (aucun import dans le dépôt) : code mort à supprimer avant qu'il ne soit branché par erreur. Maquette non validée par Michael ; aucun test navigateur mobile/clavier consigné. | **partielle** |
| **5. Maîtriser modèles et coûts** — budget durable, contrôle au point d'appel, pas d'unités internes présentées comme dollars, aucun basculement silencieux payant | Les unités internes ne sont **jamais** présentées en dollars : `COST_LADDER_SNAPSHOT_BASIS = "estimated/in-memory only"` (`cost-ladder.ts:360`) et l'encart `/hq/runtime:270-277` dit « pas de facturation réelle, pas de persistance ». Le plancher premium de `client_audit` est effectif et testable (`cost-ladder.ts:63-69`). | Budget en mémoire, débité par décision et non au point d'appel, sans dimension workspace (constat 2). Message de basculement faux (constat 3). `requestedMode` n'est transmis par **aucun** appelant de `chooseModel` : les branches `economy` et `manual` (`model-router.ts:159-164,179-186`) sont inatteignables, donc « accès/modèle visibles » et « séparer abonnement, API et modèle local » n'ont aucune implémentation. Aucune comparaison qualité/coût/latence sur missions identiques. | **non tenue** |
| **6. Recette de livraison** — vraie modification utile, refus hors projet, interruption/reprise sans double effet, rollback éprouvé, journal expurgé | Chemin de réconciliation explicite et fail-closed (`openhands-launch.ts:86-93,109`) ; autorité de lancement à expiration 10 min (`openhands-launch-store.ts:61`) ; dispatch externe refusé à la création (`mission-draft-durable-repository.ts:38-40`). | Aucune modification réelle livrée depuis HQ. Rollback et sauvegarde/restauration non éprouvés. Reprise après échec transitoire du constat 5 sans voie de sortie documentée pour l'opérateur. | **non tenue** |

### Lecture d'ensemble

Le code d'admission et d'autorisation est, dans l'ensemble, nettement plus prudent que ce que le plan redoutait : identifiants déterministes, insert-or-ignore, relecture canonique, hash de charge incluant l'acteur, étiquettes d'honnêteté dans l'interface. **Les deux verrous qui restent sont ailleurs** : (a) une infrastructure PostgreSQL/PostgREST absente, qui empêche toute qualification réelle de la concurrence et de la reprise ; (b) une couche coût/routage qui produit des chiffres et des explications faux, et une barrière d'autorisation API contournable. Aucun de ces deux verrous ne demande un nouveau framework ni une nouvelle couche.

---

## 4. Séquence minimale de déblocage proposée

Ordonnée par ce qu'elle débloque, pas par effort. Aucune nouvelle plateforme, aucun nouveau routeur, aucun nouveau registre de missions.

1. **Constat 1** — deux lignes dans `owner.ts`. Rien ne peut être déclaré « authentification imposée côté serveur » avant.
2. **Constats 3 puis 2** — corriger le message, puis déplacer le débit au point d'appel et clé par workspace. Débloque l'exigence 5 et retire un faux état visible de l'interface.
3. **Constat 4** — réhydrater `requestId`. Débloque la première mission réelle depuis l'interface : aujourd'hui un rechargement de page suffit à perdre une admission.
4. **Constat 5** — séparer les échecs avant écriture des incertitudes d'écriture, en réutilisant le drapeau `attempted` déjà présent dans `openhands-launch.ts`. Rend le signal « issue inconnue » à nouveau fiable, ce dont dépendent les exigences 3 et 6.
5. **Infrastructure** — une instance PostgreSQL + PostgREST jetable, par Docker ou un Postgres local. **C'est la seule dépendance qui demande une décision ou une autorisation de Michael.** Elle débloque l'exigence 2 entière, le harnais déjà écrit par Antigravity, et le cas de test du constat 8.
6. **Constat 7** — Antigravity corrige l'étiquetage et retire l'identification Hermes figée ; Cursor et Codex acceptent. Sans cela, la revue suivante repart d'une preuve fausse.
7. **Constat 6** — Codex tranche l'autorité d'admission unique ; une seule des deux options, pas les deux.
8. **Constat 8** — couvert par le harnais réel une fois l'étape 5 faite.

À faire d'abord, hors constats : **désigner un propriétaire d'écriture pour `src/server/auth/`, `src/server/ai/` et `src/features/missions/`**. Six des huit constats tombent dans ces trois répertoires et aucun n'a de responsable dans la direction commune actuelle.

---

## 5. Autocritique

**Quelle hypothèse pourrait invalider ces résultats.** Les constats 2 et 3 ont été reproduits via `jiti` sur les fichiers TypeScript réels, mais hors du runtime Next.js : si une couche d'appel non lue passait un `freeCatalog` ou un `budgetStore` non vide, le constat 3 perdrait son caractère systématique. J'ai vérifié par recherche textuelle qu'aucun appelant ne renseigne ces champs dans `src/` ; je n'ai pas inspecté d'éventuelle injection côté `instrumentation` ou middleware.

**Quel scénario adverse a été vérifié.** J'ai cherché à faire tomber chaque constat. Le constat 6 a été volontairement affaibli : j'avais d'abord noté un risque d'écrasement croisé entre les deux autorités d'admission, et la lecture de `development-mission.ts:33` (acteur et mode dans `payloadHash`) l'a écarté — il reste une dette de traçabilité, pas une perte de données. De même, j'ai envisagé une faille dans le verrou optimiste de `openhands-launch-store.ts:50-56` (comparaison `eq` sur une colonne `jsonb` via chaîne de requête) ; la sémantique PostgREST et `jsonb` normalisé rend ce chemin probablement correct, et je ne le rapporte donc pas. Le constat 1 est présenté comme un défaut de défense en profondeur, pas comme une faille active : aucun module de production ne pose la propriété aujourd'hui.

**Ce qui demeure inconnu.** L'exécution du CLI du lot Antigravity (constat 5, site 3) n'a pas été observée. Le constat 8 n'a pas de déclencheur prouvé. Le comportement multi-instances du budget en mémoire est déduit du code, pas mesuré sur un déploiement. Aucune capacité réelle du runtime Hermes n'est affirmée ici : ce périmètre reste celui de l'autre session Claude, et son rapport n'existe pas encore dans l'Orchestrator. Je n'ai ni rejoué ni contredit les preuves de Cursor.

**Ce que je n'ai pas fait, volontairement.** Aucune modification dans `Oria.HQ` ni dans le lot Antigravity. Aucun nouveau répertoire, aucune nouvelle couche, aucun secret lu. Aucun appel de modèle externe. Aucune action sur la production. Un seul agent, aucun sous-agent.
