# Construction candidate — 30 septembre 2026

Image `oria-openhands-claude:qualification1` construite sur VPS. Base permissions identifiée par manifest `c92b2bba697284fb1596593c0aab8e34d3ae024ae11b7f4372d90066a64e91b4`, référencée via tag local dédié `permissions-c92b2bba`. Un FROM utilisant directement `sha256:…` était interprété comme nom de dépôt par BuildKit et a été remplacé par ce tag; le log vérifie le digest résolu.

Image finale manifest `eeb0cd98335fd8398e4c001ca37290912025eeb25ee46e9117f07143ae34cccb`. Paquet ACP 0.84.0 installé sans scripts npm, binaire Claude embarqué 2.1.284. Inventaire et package-lock restent dans `/opt/claude-acp` de l'image; premier install transitif résolu, pas encore verrou externalisé et revu pour reconstruction.

Deux commandes terminent code0 : `--cli --version` et `--cli auth login --help`. Réseau none, root filesystem readonly, capabilities retirées, utilisateur10001, tmpfs privés bornés, mémoire1Go/CPU1. L'aide distingue abonnement `--claudeai` (défaut) de Console/API `--console`. Aucun login ni appel modèle effectué, aucun credential Paperclip lu ou copié.

Reste : lock reproductible, initialisation ACP réelle sans credentials, puis connexion officielle dédiée et mission isolée avec autorisation/budget avant tout effet. Les services existants restent inchangés.

## Initialisation et dépendances verrouillées
Initialisation ACP réelle réussie sans session/prompt/auth, protocole1. Premier échec permission dossier montage corrigé uniquement sur scriptsqualification nonsecrets. Package-lock officiel extrait image,113entrées resolved toutes npmregistry+integrity, puis Dockerfile passé npmci ignore-scripts. Reconstruction code0, manifest3e240595164cab4c41fbaef76d5911983aed48087ce72064ac2e69a350dd0ce7. Initialisation réelle rejouée code0 dans image reconstruite. Aucune connexion fournisseur ni requêtemodèle. authMethods vide àinitialize ne prouve pas login; commandeCLI officielle reste cheminauth à qualifier.

## Session réelle et outils de développement
Adaptateur accepte session/new sur workspace vide sansauth ni promptmodèle. Image enrichie Git+certificats système et npm/npx du Nodeofficiel, absents auparavant. Reconstruction code0; manifest0c894a12d134550817570bb5727854bf8da5f708165ba011916b80eec2b1c2c4. Versionsoutils puis initialize/sessionnew revérifiés réseauoff. Aptprovient dépôtDebian au build; inventairedpkg conservé, résolutionapt nonverrouillée par snapshot. Sessioncréée ne prouve aucune authentication ni capacitéàinférer.

## Capacité des outils sans modèle
qualify_tools.py exécuté dans image finale sous UID10001, réseauoff, rootreadonly et tmpfsbornés : créationGit/commit, npmtestofflinepass, erreurintroduite détectée, correctiontestée et diff limité fichierattendu. Code0. Ce parcours utilise un scriptdéterministe sur projetjetable; aucun résultatattribué à un modèle. Aucun test de l'applicationHQ réelle dans ce conteneur encore.

## Correction du verdict de session

Le contrôle rejetait visiblement une réponse `session/new` en erreur mais pouvait
terminer avec un code zéro. Il échoue maintenant explicitement dans ce cas et
refuse aussi une identité de session vide. Le script corrigé a été transféré dans
le répertoire de qualification du VPS et rejoué avec le véritable adaptateur :
initialisation et session réussies, code zéro, réseau désactivé, aucun prompt
modèle. Cela confirme le parcours positif; les réponses de refus ne constituent
pas une preuve d'authentification et ne peuvent plus être annoncées comme succès.

Six tests de protocole simulé passent sous Python optimisé (`-O`), localement
et sur VPS : succès explicitement non authentifié, refus d'initialisation,
protocole incompatible, refus de session, identité absente/vide, déconnexion.
Tous vérifient la fermeture du processus et l'absence de prompt/authentification.
Les assertions d'initialisation ont été remplacées par des contrôles explicites
pour rester actifs sous Python optimisé. Le véritable adaptateur a ensuite
repassé l'initialisation et la création de session sans réseau ni modèle.

## Reprise opérationnelle — comparaison avec une installation Docker ancienne (2 octobre 2026)

Mandat : `docs/CLAUDE-REPRISE-OPENHANDS-OPERATIONNELLE.md`. Ce lot compare ce
candidat à `ghcr.io/openhands/agent-canvas:1.0.0-rc.11`, une image OFFICIELLE
différente (all-in-one agent-server + automation + frontend), déjà présente
sur cette machine (pas ce candidat, pas la même construction) sous trois
conteneurs arrêtés : `openhands-agent-canvas` (a tourné du 2026-07-09 au
2026-07-30, exit255), `-old` et `-backup` (quelques heures chacun, exit137 —
tués, pas arrêtés proprement). Les trois montent les mêmes répertoires hôte
persistants : `C:\Users\micha\.openhands` (état session/automation),
`C:\Users\micha\Dev\openhands-projects`, et
`C:\Users\micha\Dev\openhands-credentials\{claude,codex,gcloud-adc,gemini}`.

**Risque de reprise automatique évalué avant tout démarrage** : l'entrypoint
réel (`tini -- /opt/agent-canvas/entrypoint.sh`, extrait en lecture seule
via `docker create`+`docker cp`+`docker rm`, jamais exécuté) démarre sans
condition trois services — agent-server, automation server (base SQLite
`automations.db` sous `~/.openhands`), frontend — dès qu'il est lancé,
indépendamment de toute connexion ultérieure de l'opérateur. Si `.openhands`
est monté, l'automation server y trouve son état persistant et peut
reprendre un travail planifié de façon autonome. **Mitigation retenue** :
la sonde de ce lot ne monte jamais `.openhands`, jamais `openhands-projects`,
jamais le socket Docker, et remplace entièrement l'entrypoint par un script
shell de diagnostic — aucun des trois services ne démarre, donc aucune
reprise n'est possible, par construction et non par une simple convention.

**Sonde isolée exécutée** (`qualify_existing_image_account.sh` +
`qualify_existing_image_account_probe.sh`, dans ce dossier) : conteneur
`--rm`, réseau `bridge` (nécessaire pour un contrôle d'authentification
réel), `--read-only`, `--cap-drop ALL`, UID réel de l'image (10001), seul
montage réel : `openhands-credentials/claude` → `~/.claude`, **en lecture
seule** — originaux jamais modifiés, aucune copie de credentials ailleurs.
Résultat, redigéré (valeurs des quatre champs déjà whitelistés ailleurs dans
ce dépôt ; email/orgId/orgName jamais affichés, ici de toute façon `null`) :

```
claude-agent-acp --cli --version → 2.1.114 (Claude Code)
claude-agent-acp --cli auth status --json → exit 0
  loggedIn = true
  authMethod = "claude.ai"      (abonnement, pas une clé API)
  apiProvider = "firstParty"
  subscriptionType = "pro"
  email / orgId / orgName : absents (type null)
stderr (texte d'aide officiel, pas un secret) : fichier de profil
  ~/.claude.json introuvable ; une sauvegarde horodatée existe sous
  ~/.claude/backups/ avec la commande cp exacte pour la restaurer —
  non exécutée par ce lot (préserve l'original).
```

**Correction (lot suivant, `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`)** :
`loggedIn: true` indique qu'un identifiant de session d'abonnement est
PRÉSENT et structurellement lisible localement par ce CLI — pas une
autorisation HQ, pas une identité de compte (conforme à la correction du
lot précédent). Le réseau `bridge` était atteignable pendant cette sonde,
mais aucune preuve n'a été recueillie qu'un appel réseau réel de validation
ait eu lieu (ni capture, ni log réseau conservé) : ne pas lire ce résultat
comme une validation distante confirmée, seulement comme une reconnaissance
locale cohérente. `codex-acp` dans
cette image n'a aucune sous-commande `login`/`doctor`/`auth` (confirmé par
`--help` : seulement `-c/--config` et `-h/--help`, aucun binaire `codex`
nu sur le PATH) — aucune tentative, rien à rediger.

Conteneur supprimé après l'unique exécution (`--rm`) ; aucune image ni
volume laissé. Aucun login interactif, aucun appel modèle, aucune
production/VPS touchée.

**Anomalie observée, non liée à ce mandat** : après ces commandes, trois
conteneurs supplémentaires aux noms Docker auto-générés
(`festive_ardinghelli`, `suspicious_chatelet`, `unruffled_rosalind`)
existaient, utilisant cette même image avec des volumes anonymes Docker
(jamais mes montages hôte) et des commandes comme `git --version`/
`python3 --version` — signature d'un mécanisme de vérification interne de
l'environnement d'exécution (harness), pas de ce lot. Non modifiés, non
supprimés (hors de mon périmètre et de ma compréhension de cet outillage) ;
signalé pour transparence.

### Delta minimal de réutilisation vs ce candidat

| | Image ancienne (agent-canvas) | Ce candidat (`openhands-claude-runtime`) |
|---|---|---|
| Adaptateur ACP Claude | `@agentclientprotocol/claude-agent-acp@0.30.0` | `0.84.0` |
| CLI Claude embarqué | `2.1.114` | `2.1.284` |
| Connexion abonnement | **Déjà active** (claude.ai, pro, firstParty) | Jamais tentée |
| codex-acp | `@zed-industries/codex-acp@0.15.0`, déprécié, sans surface auth | Non applicable (candidat Codex séparé) |

Le seul élément réellement réutilisable sans reconstruction : le répertoire
de credentials hôte `C:\Users\micha\Dev\openhands-credentials\claude`
contient déjà une session d'abonnement Claude fonctionnelle. Rien n'indique
qu'elle soit liée à la version 2.1.114 spécifiquement — les jetons OAuth
Claude sont conçus pour être indépendants de la version du CLI — mais ceci
n'est PAS vérifié pour ce candidat (0.84.0/2.1.284) et doit l'être
séparément avant toute réutilisation réelle.

### Recette d'une mission de qualification (non exécutée)

1. Construire réellement ce candidat localement ou retrouver le manifest
   VPS déjà construit (`PERMISSION_BASE` manquant sur cette machine,
   documenté dans `RESULTS.md` ci-dessus).
2. Monter `openhands-credentials/claude` en LECTURE SEULE dans l'image
   construite (jamais `.openhands`, jamais `openhands-projects`) et
   rejouer exactement la même sonde `--cli auth status --json` que
   ci-dessus, pour vérifier que la session existante reste valide sous
   l'adaptateur/CLI plus récent de ce candidat.
3. Si incompatible : lancer `claude-agent-acp --cli auth login --claudeai`
   officiel et indépendant (jamais une copie de jeton) dans ce même
   environnement candidat.
4. Obtenir l'approbation écrite explicite de Michael pour : (a) un montage
   en lecture-écriture si un rafraîchissement de jeton s'avère nécessaire,
   (b) une policy/compte approuvés dans le registre existant
   (`provider_policy.py`, `validate_authorization`), (c) un budget borné
   (`maxCostCents`/`maxTokens`/`maxIterations` déjà existants, jamais
   élargis).
5. Seulement alors : une mission réelle unique, bornée et minimale, pour
   observer coût/usage réels et clore la qualification — pas avant.

Aucun remplacement général des contrôles HQ existants ; aucune désactivation
de `provider_policy.py` ni du gate `model-emission-launch-gate.ts`. Aucune
vraie mission modèle exécutée par ce lot.

## Build réel du candidat + sonde corrigée (2 octobre 2026)

Mandat : `docs/CLAUDE-BUILD-CANDIDAT-CONNEXION.md`, complété par
`docs/CLAUDE-COORDINATION-REVUE-CIBLEE.md`. Fait suite directement à la
section précédente : construit réellement ce qui n'était qu'une recette.

### 1. Correction préalable exigée (PREREQUIS du mandat)

`qualify_existing_image_account_probe.sh` et `qualify_existing_image_account.sh`
(section précédente) sont supprimés. Remplacés par
`qualify_connection_account.py`, module Python pur, et
`test_qualify_connection_account.py` (23 tests). Défauts corrigés, prouvés
par test, jamais par promesse :
- Aucun stderr ni `--version` brut n'est jamais imprimé ; seules quatre
  valeurs de champs whitelistées (`loggedIn`, `authMethod`, `apiProvider`,
  `subscriptionType`) sont imprimées, et seulement si leur forme est sûre
  (≤32 car., charset restreint) — sinon rejetées (`rejectedUnsafeShape`),
  jamais fuitées.
- Code de sortie réel et distinct : 0 = diagnostic classifié (connecté ou
  non, les deux sont un succès honnête) ; 2 = la commande auth OU version
  elle-même a échoué à s'exécuter ; 3 = JSON invalide ; 4 = stderr présent
  mais non classifiable en sécurité (refus, jamais deviné) ; 5 = `--version`
  exécuté mais sortie de forme inattendue. Le script précédent finissait
  toujours sur un `echo`, donc toujours code 0 — corrigé.
- Un sous-agent natif en lecture seule (`Explore`, demandé par le complément
  de coordination, contexte limité au diff + critères) a relu ce module
  avant toute construction d'image et a prouvé deux défauts réels (aucune
  fuite trouvée) : (a) un échec de la commande `--version` elle-même était
  classé dans le même code de sortie que "sortie illisible", contredisant
  la documentation du contrat ; (b) la reconnaissance du message stderr
  connu-sûr utilisait une recherche de sous-chaîne, acceptant n'importe quel
  texte contenant les deux phrases même entouré de contenu injecté non
  vérifié. Les deux corrigés par moi-même (jamais délégués) avec un test de
  régression nommé par défaut, avant toute sonde réelle. Revue bornée à une
  seule exécution, aucune récursion, aucun accès credentials/Docker donné
  au relecteur.

### 2. Construction locale réelle (base manquante, résolue sans redemander)

Aucune des trois images n'existait localement. Construites dans l'ordre
documenté par les Dockerfiles existants, versions et digests déjà épinglés,
sans modifier un seul Dockerfile ni affaiblir une permission :

1. `deploy/openhands-qualification/Dockerfile` → `oria-openhands-qualification:sdk1.50.0`
   (`python:3.12-slim` par digest épinglé, `openhands-sdk==1.50.0` épinglé).
2. `integrations/openhands-permission-extension/Dockerfile` → `oria-openhands-qualification:permissions1`.
   SHA256 du patch obtenus : original `8c949ea7053c74ef42d5ee1f775069cbefe7fe4f59d922ccf724595717f541f9`,
   patché `7a496b59265b8139e3dd965e9ef95e28133db5cfa4b48ee20da12c328e152455`
   — **identiques** à ceux déjà documentés pour l'image VPS dans
   `integrations/openhands-permission-extension/RESULTS.md` : reconstruction
   locale prouvée équivalente, pas une permission affaiblie ou différente.
3. `integrations/openhands-claude-runtime/Dockerfile` (`PERMISSION_BASE=oria-openhands-qualification:permissions1`)
   → `oria-openhands-claude-runtime:candidate1`, ID
   `sha256:9e23766db51e3e215d0fe4ae1b146b7b3c827e28a65e3105a0c2a724a9a089b5`.

**Défaut réel trouvé et corrigé pendant la construction** : le lanceur
`claude-agent-acp` versionné dans ce dépôt avait des fins de ligne CRLF
(`#!/bin/sh\r\n`), cassant l'interprétation du shebang par le noyau Linux
(`execve` renvoie ENOENT sur l'interpréteur `/bin/sh\r` introuvable) —
reproduit et confirmé indépendant de tout drapeau de sécurité Docker
(testé avec et sans `--network none`/`--read-only`/`--cap-drop ALL`/
`--security-opt no-new-privileges`, échec identique dans tous les cas).
Fichier réécrit avec fins de ligne LF ; `.gitattributes` complété
(`integrations/openhands-claude-runtime/claude-agent-acp text eol=lf`) pour
empêcher la régression sur un futur checkout Windows. Image reconstruite
(étape 3) après correction.

### 3. Sonde isolée contre le candidat construit — exécutée, nettoyée

`probe_connection_candidate.sh` (nouveau) : `docker create --rm --network
none --read-only --cap-drop ALL --security-opt no-new-privileges
--pids-limit 128 --memory 512m --cpus 1`, deux `--tmpfs` (`/tmp`,
`/home/runner`), `--entrypoint python` explicite (jamais la commande par
défaut de l'image), seuls montages réels : le répertoire hôte
`openhands-credentials/claude` en **lecture seule** sur `/home/runner/.claude`
et le script `qualify_connection_account.py` lui-même en lecture seule.
Jamais `.openhands`, jamais `openhands-projects`, jamais le socket Docker —
aucun service ne démarre, donc aucune reprise de job possible par
construction, pas seulement par promesse. `--network none` : aucun appel
modèle/API, facturé ou non, n'est même joignable. Nettoyage : `trap` sur
EXIT/INT/TERM supprime le conteneur ; vérifié après coup, aucun conteneur ni
image résiduel portant le label `oria.purpose=openhands-claude-runtime-candidate-connection-probe`.

Résultat (code de sortie **0**, diagnostic entièrement classifié) :
```
{"version": {"status": "ok", "version": "2.1.284 (Claude Code)"}}
{"authStatus": {"ok": true, "connected": true, "fields": {"loggedIn": true,
  "authMethod": "claude.ai", "apiProvider": "firstParty",
  "subscriptionType": "pro"}, "otherFieldsPresent": ["analyticsDisabled",
  "configDirectory", "email", "orgId", "orgName", "projectsDirectory"],
  "stderr": {"kind": "profile_cache_missing_backup_available", "occurrences": 2}}}
```
`otherFieldsPresent` liste des NOMS uniquement, jamais de valeur (email,
orgId, orgName compris). Le stderr observé (message "fichier de config
introuvable, sauvegarde disponible" répété deux fois par ce CLI plus
récent, avec une commande `cp "..." "..."` citée) a été structurellement
examiné (longueur, présence de marqueurs comme `token`/`Bearer `/`email`/
`orgId` — tous absents — puis contenu redigé caractère-par-caractère) avant
d'élargir le motif connu-sûr de façon précise et ancrée (1 ou 2 occurrences
exactement, jamais un nombre arbitraire) ; un test de non-régression prouve
qu'un troisième répétition reste refusée. Aucune valeur brute de ce stderr
n'a été imprimée à aucun moment, dans le script ni dans cette investigation.

### 4. Statut réellement observé — reconnaissance locale, pas une validation distante

**Correction par rapport à la rédaction initiale de ce lot**
(`docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, point 1) : cette sonde a
tourné sous `--network none` — aucun appel réseau n'est possible, donc
`auth status --json` n'a pu lire QUE l'état local déjà persisté sur disque
(fichier de credentials existant), jamais contacté un serveur Anthropic.
**Session d'abonnement reconnue LOCALEMENT** par ce candidat (0.84.0/CLI
2.1.284) : `loggedIn=true`, `authMethod="claude.ai"`,
`apiProvider="firstParty"`, `subscriptionType="pro"`. Ceci prouve que le
CLI plus récent de ce candidat PARSE et ACCEPTE STRUCTURELLEMENT le même
format de fichier de credentials que l'ancien, sans erreur — PAS que le
jeton OAuth qu'il contient est toujours valide ou accepté par le
fournisseur distant aujourd'hui. Cette question (compatibilité OAuth
réellement acceptée côté serveur) reste OUVERTE et n'est volontairement pas
testée ici : le mandat interdit tout appel modèle/API, donc le réseau a été
supprimé par construction, pas seulement par promesse. Ne plus annoncer une
« connexion fournisseur vérifiée » sur la seule base de ce résultat. Aucun
login interactif n'a été nécessaire. Identité utilisateur (email, orgId,
orgName) : présente dans la
réponse mais jamais lue ni imprimée par valeur — reste explicitement
inconnue pour ce rapport, conformément à la correction du lot précédent
(un `orgId` n'est pas un identifiant utilisateur). Codex : toujours aucune
sous-commande auth dans ce candidat — non retesté, rien de nouveau à
rediger.

### 5. Nettoyage

Conteneur de sonde supprimé (vérifié par label, section 3). Les trois
images construites (`sdk1.50.0`, `permissions1`, `candidate1`) sont
conservées intentionnellement — ce sont le livrable du mandat, pas des
ressources temporaires, et remplacent le besoin de reconstruire à chaque
sonde future. Aucun ancien conteneur (`openhands-agent-canvas*`) ni
production touché. Les trois conteneurs d'anomalie d'environnement
(`festive_ardinghelli`, `suspicious_chatelet`, `unruffled_rosalind`, notés
dans la section précédente) toujours non touchés.

### Recette d'une première mission (mise à jour, toujours NON exécutée)

Les étapes 1 et 2 de la recette précédente sont maintenant faites (build
réel, sonde rejouée, session locale reconnue — compatibilité OAuth distante
réellement acceptée toujours NON vérifiée, volontairement, par absence de
réseau). Restant avant toute mission réelle :

1. Obtenir l'approbation écrite explicite de Michael pour : (a) une policy/
   compte approuvés dans le registre existant (`provider_policy.py`,
   `validate_authorization`), (b) un budget borné (`maxCostCents`/
   `maxTokens`/`maxIterations`, jamais élargis).
2. Lancer `oria-openhands-claude-runtime:candidate1` avec un montage
   `openhands-credentials/claude` en lecture-seule identique à la sonde,
   mais cette fois via le vrai point d'entrée ACP (pas l'override de
   diagnostic), dans un réseau isolé, pour une tâche réelle unique, bornée
   et minimale.
3. Observer coût/usage réel sur cette tâche unique et clore la
   qualification — pas avant, pas de mission répétée sans nouvelle
   approbation.

Aucun remplacement des contrôles HQ existants ; aucune désactivation de
`provider_policy.py` ni du gate `model-emission-launch-gate.ts`. Aucune
vraie mission modèle exécutée par ce lot ; aucun déploiement ; catalogue
Cursor non touché.
