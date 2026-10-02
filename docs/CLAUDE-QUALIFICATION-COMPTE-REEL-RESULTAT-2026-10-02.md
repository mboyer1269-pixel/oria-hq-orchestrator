# Qualification compte réel — tranche ciblée — résultat

2 octobre 2026. Mandat : `docs/CLAUDE-QUALIFICATION-COMPTE-REEL.md`. Correctif
`be92146` confirmé accepté ; narrowing Cursor corrigé par Codex,
`npx tsc --noEmit` passe sur tout le dépôt (**0 erreur**, vérifié avant toute
modification de ce lot). Périmètre : missions/sonde/runtime uniquement.

## Inspection officielle, en lecture seule, sans login/appel modèle/secret

Les trois CLI (`claude`, `codex`, `gemini`) sont installés sur cette
machine — traité comme l'environnement d'inspection le plus proche de
l'environnement runner prévu, puisqu'aucun runner QUALIFIÉ n'est câblé à
ce gate aujourd'hui. (Correction ultérieure : ceci ne signifiait pas
qu'aucune installation n'existe nulle part — voir
`docs/CLAUDE-CORRECTION-PORTEE-IDENTITE-RESULTAT-2026-10-02.md` pour
l'inventaire réel d'une ancienne installation Docker non qualifiée.) Rien
exécuté qui ne soit déjà dans l'allowlist approuvée existante
(`PROBE_COMMAND_ALLOWLIST`, `LOCAL_RUNTIME_PROBE_APPROVAL`, déjà accordée) ou
une commande `--help`/`doctor --json` (« redacted machine-readable report »,
texte officiel du programme lui-même) tout aussi non destructive.

### Claude — identité stable trouvée

`claude auth status --json` retourne, au-delà des quatre champs déjà
whitelistés (`loggedIn`, `authMethod`, `apiProvider`, `subscriptionType`) :
`email`, `orgId`, `orgName`, `analyticsDisabled`, `projectsDirectory`.
Vérifié sans jamais afficher la valeur réelle (uniquement noms de champs,
types, longueurs et motifs de format) :

- `orgId` : chaîne de 36 caractères, ne contient pas `@`, format compatible
  UUID — stable par compte/organisation, jamais un email, jamais un jeton
  rotatif.
- `email`/`orgName` : directement identifiants humains — jamais lus pour
  cet usage, exactement comme avant.

C'est précisément le type d'identité que le mandat autorise : ni profil, ni
provider, ni simple `loggedIn`, ni hash d'un jeton. **Oui** — une identité
stable peut être attestée.

### Codex — champ manquant, preuve exacte

`codex login status` (texte brut, pas de `--json`) : une seule ligne, 23
caractères, aucune donnée au-delà du statut connecté/non-connecté déjà
capté par `classifyCodexProbe`.

`codex doctor --json` (« Emit a redacted machine-readable report », texte
officiel) : rapport exhaustif, mais sa section `checks["auth.credentials"].details`
ne contient que des booléens de présence — vérifié directement sur les
longueurs de chaîne (`stored API key` : 5 car., `stored ChatGPT tokens` :
4 car., `stored agent identity` : 5 car. — motifs compatibles avec
`"true"/"false"/"none"`, jamais une valeur). Aucun champ ne distingue un
compte d'un autre.

**Non** — aucune identité stable n'est exposée par les surfaces officielles
actuelles de Codex. Proposition concrète unique : exposer, dans
`codex doctor --json` (ou une nouvelle sous-commande `codex auth status
--json`), un identifiant de compte/session stable et déjà rédigé — analogue
à l'`orgId` de Claude — plutôt qu'un booléen de présence. Intervention
indispensable et hors de ce périmètre : l'équipe officielle de l'outil
Codex CLI (OpenAI) devrait ajouter ce champ ; rien côté HQ ne peut le faire
apparaître sans le fabriquer, ce que ce lot refuse explicitement de faire.

## Implémenté — Claude uniquement, contrats réutilisés

> **CORRECTION, même jour** (`docs/CLAUDE-CORRECTION-PORTEE-IDENTITE-RESULTAT-2026-10-02.md`) :
> l'implémentation décrite ci-dessous a été bloquée en revue avant
> activation et **annulée**. `orgId` identifie l'organisation, pas
> l'utilisateur ; le hasher ne changeait pas cette portée. L'état réel,
> après correction : `classifyClaudeCodeProbe` ne lit plus `orgId` pour
> cet usage et ne retourne jamais `accountId` pour Claude — même absence
> honnête que pour Codex. Section conservée ci-dessous comme trace de ce
> qui a été tenté puis corrigé, pas comme état courant.

- **`src/server/agents/runtimes/local-runtime-probe.ts`** —
  `classifyClaudeCodeProbe` lit maintenant `orgId` (jamais ajouté à la
  liste blanche d'évidence — le test existant « email/orgId never enter
  Claude auth evidence » reste vert sans modification) et retourne
  UNIQUEMENT son hash SHA-256 (nouvelle fonction `hashAccountIdentity`,
  `node:crypto`, déjà une dépendance du runtime) comme nouveau champ
  optionnel `accountId` sur `ProbedRuntimeEntry` — jamais la valeur brute.
  Absent si `orgId` est absent/vide/non connecté. `sanitizeProbedEntry`
  efface explicitement `accountId` sur toute déclassification.
- **`src/server/agents/models/runner-executor-connection-probe.ts`** —
  `accountId` transmis tel quel de `classifyClaudeCodeProbe` vers
  `ProviderConnectionProbeOutcome`, sans transformation supplémentaire.
  Doctrine d'en-tête et message `codex-acp-cli` mis à jour pour refléter
  la preuve exacte ci-dessus (plus de phrase générique).
- **Aucun changement dans `model-emission-launch-gate.ts`** : son contrat
  (`connectionEntry.accountId`, refus explicite si absent,
  `attestedAccountStillMatches` avant commit) était déjà correctement
  câblé par le correctif précédent — il consomme maintenant une vraie
  attestation au lieu d'une absence systématique, sans qu'une seule ligne
  de ce fichier n'ait besoin de changer.

## Fraîcheur — CORRECTION (revue `docs/CLAUDE-CORRECTION-PORTEE-IDENTITE.md`) : inférence retirée

Réhorodater à `now()` ne prouve rien par construction : déjà noté au lot
précédent, toujours vrai (ce gate capture `now()` une fois par décision et
l'utilise pour l'horodatage ET l'évaluation — jamais périmé entre les deux
par construction, pas par un contrôle contournable).

**Ligne originale retirée** : ce document affirmait qu'une latence mesurée
de ~1,95 s sur `claude auth status --json` était « cohérent avec un
aller-retour réseau réel de vérification/rafraîchissement du jeton ». La
revue a raison de rejeter cette inférence : une durée d'exécution ne prouve
ni qu'une requête serveur a eu lieu, ni la fraîcheur de quoi que ce soit —
une commande peut être lente pour d'innombrables raisons sans lien avec une
vérification réseau (chargement de modules, accès disque, latence de
démarrage du processus), et une commande RAPIDE pourrait tout autant lire
un cache local périmé sans jamais recontacter le serveur. Mesurer une durée
n'établit aucune des deux. La seule chose honnêtement établie : l'horodatage
de CETTE observation précise (`claude auth status --json`, mesuré sur cette
machine, 2 octobre 2026, ~1,95 s) — sans inférence de fraîcheur serveur à
partir de cette mesure, et sans affirmation que la source n'est pas un
cache. Une source dont le caractère cache/live est inconnu doit rester
documentée comme telle, jamais reclassée "fraîche" sur la base d'un
chronométrage.

Test de donnée périmée AU BON NIVEAU (celui où la péremption peut
réellement être représentée) : `model-emission-gate.test.mjs`, « a stale
INDIVIDUAL provider entry is blocked... », déjà existant, réutilisé sans
modification — c'est la seule couche où un horodatage de capacité
indépendant de `now()` du gate peut exister et donc être testé comme
périmé. Le gate appelant lui-même ne peut structurellement pas produire
cette situation (expliqué au rapport précédent) — pas une lacune cachée.

## Tests — fixtures distinguées de la preuve runtime

> **Décomptes dépassés par la correction** : les tests `6b`/`logged in WITH
> a real orgId`/le `FIXTURE PROOF` initial listés ci-dessous ont été
> réécrits ou remplacés dans la correction du même jour — les décomptes
> faisant foi sont ceux de
> `docs/CLAUDE-CORRECTION-PORTEE-IDENTITE-RESULTAT-2026-10-02.md`
> (22/22, 18/18, 41/41).

Aucun login, aucun appel modèle, aucun déplacement de credentials, aucune
sortie de secret brut dans ces tests ou ce rapport.

- `local-runtime-probe.test.mjs` : **20/20** (2 nouveaux cas :
  attestation stable/opaque/discriminante avec un orgId réel *fixture*;
  absence sur orgId manquant/vide/non-JSON et sur déclassification).
- `runner-executor-connection-probe.test.mjs` : **17/17** (1 cas corrigé
  — l'ancienne assertion « jamais d'accountId » était vraie seulement
  pour cette fixture précise, pas en général ; 1 cas nouveau prouvant le
  passage intact de l'attestation à travers ce pont).
- `model-emission-launch-gate.test.mjs` : **40/40** (1 nouveau test
  explicitement étiqueté « FIXTURE PROOF (not runtime proof) » — câble
  les vraies fonctions de production (`createRunnerClaudeCliConnectionProbe`
  → `classifyClaudeCodeProbe` → hash réel → gate → commit) avec UNIQUEMENT
  le transport SSH simulé, puisqu'aucun hôte runner réel n'existe ;
  prouve le mécanisme, ne prouve pas qu'un compte réel a été observé en
  production).
- `npx tsc --noEmit` sur tout le dépôt : **0 erreur** (avant et après ce
  lot).
- Combiné (`missions/*` + `ai/*` + `agents/models/*` + `agents/runtimes/*`
  + `openhands-launch-contract`) : **zéro échec** hors des deux lacunes
  intentionnelles déjà trackées (`*-gap.test.mjs`), non liées à ce mandat.

## Limites dites explicitement

1. Codex n'a aucune identité attestable aujourd'hui — refus honnête
   maintenu, rien fabriqué. Voir la proposition concrète ci-dessus.
2. **CORRIGÉ** (voir `docs/CLAUDE-CORRECTION-PORTEE-IDENTITE-RESULTAT-2026-10-02.md`) :
   le point 2 original affirmait que l'`orgId` de Claude « suffit à détecter
   un changement de compte/organisation sous le même profil ». C'était
   l'erreur de portée que la revue indépendante a bloquée avant activation :
   `orgId` identifie l'ORGANISATION, pas l'utilisateur — deux personnes
   différentes dans la même organisation partagent le même `orgId`, donc un
   hash d'`orgId` ne les distingue jamais. L'implémentation a été annulée ;
   `accountId` reste désormais absent pour Claude aussi, honnêtement, comme
   pour Codex (point 1). Claude n'a aujourd'hui aucune identité STABLE
   PAR UTILISATEUR officiellement documentée.
3. **CORRIGÉ** : « aucun hôte runner réel n'existe » était une
   généralisation excessive. Une ancienne installation Docker configurée
   (`ghcr.io/openhands/agent-canvas:1.0.0-rc.11`, conteneur
   `openhands-agent-canvas`, a réellement tourné du 9 au 30 juillet 2026
   avec les montages de credentials réels) existe sur cette machine —
   arrêtée, non qualifiée pour ce gate, mais pas absente. Distinction
   correcte : aucun runner QUALIFIÉ et approuvé n'est câblé à ce gate ;
   une installation non qualifiée existe. Voir le rapport de correction
   pour l'inventaire exact et la cible/le blocage concrets.
4. **CORRIGÉ** : la mesure de latence (~1,95 s) a été retirée comme indice
   de fraîcheur serveur — une durée d'exécution ne prouve ni une requête
   serveur ni l'absence de cache. Voir la section Fraîcheur ci-dessus.
