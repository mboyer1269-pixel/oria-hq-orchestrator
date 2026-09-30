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
