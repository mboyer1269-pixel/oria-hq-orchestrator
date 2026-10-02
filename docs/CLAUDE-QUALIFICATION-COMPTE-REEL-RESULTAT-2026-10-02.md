# Qualification compte réel — tranche ciblée — résultat

2 octobre 2026. Mandat : `docs/CLAUDE-QUALIFICATION-COMPTE-REEL.md`. Correctif
`be92146` confirmé accepté ; narrowing Cursor corrigé par Codex,
`npx tsc --noEmit` passe sur tout le dépôt (**0 erreur**, vérifié avant toute
modification de ce lot). Périmètre : missions/sonde/runtime uniquement.

## Inspection officielle, en lecture seule, sans login/appel modèle/secret

Les trois CLI (`claude`, `codex`, `gemini`) sont installés sur cette
machine — traité comme l'environnement d'inspection le plus proche de
l'environnement runner prévu, puisqu'aucun hôte runner réel n'existe. Rien
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

## Fraîcheur — vérifiée, pas supposée

Réhorodater à `now()` ne prouve rien par construction : déjà noté au lot
précédent, toujours vrai (ce gate capture `now()` une fois par décision et
l'utilise pour l'horodatage ET l'évaluation — jamais périmé entre les deux
par construction, pas par un contrôle contournable). Ce qui MANQUAIT : une
vérification que la commande elle-même ne lit pas un état local mis en
cache sans jamais revérifier le serveur. Mesuré, pas supposé : `claude auth
status --json` prend **~1,95 s** sur cette machine — incompatible avec une
simple lecture de fichier local (qui prendrait quelques millisecondes),
cohérent avec un aller-retour réseau réel de vérification/rafraîchissement
du jeton. Ce n'est pas une preuve cryptographique de fraîcheur côté serveur
— présenté comme indice mesuré, pas comme certitude.

Test de donnée périmée AU BON NIVEAU (celui où la péremption peut
réellement être représentée) : `model-emission-gate.test.mjs`, « a stale
INDIVIDUAL provider entry is blocked... », déjà existant, réutilisé sans
modification — c'est la seule couche où un horodatage de capacité
indépendant de `now()` du gate peut exister et donc être testé comme
périmé. Le gate appelant lui-même ne peut structurellement pas produire
cette situation (expliqué au rapport précédent) — pas une lacune cachée.

## Tests — fixtures distinguées de la preuve runtime

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
2. L'`orgId` de Claude est réel et stable, mais reste un identifiant
   d'ORGANISATION, pas littéralement d'individu — suffisant pour détecter
   un changement de compte/organisation sous le même profil, ce qui est
   exactement ce que le mandat demandait.
3. Aucun hôte runner réel n'existe : la preuve d'intégration ci-dessus est
   une preuve de MÉCANISME (fixture SSH), jamais présentée comme preuve
   qu'un compte réel a été observé en production.
4. La mesure de latence (~1,95 s) est un indice, pas une preuve
   cryptographique de fraîcheur côté serveur.
