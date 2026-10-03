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

`loggedIn: true` établit une CONNEXION réelle via abonnement — pas une
autorisation HQ, pas une identité de compte (conforme à la correction du
lot précédent : aucune identité par-utilisateur n'est extraite ni
fabriquée ici, et `orgId` reste absent de toute façon). `codex-acp` dans
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
