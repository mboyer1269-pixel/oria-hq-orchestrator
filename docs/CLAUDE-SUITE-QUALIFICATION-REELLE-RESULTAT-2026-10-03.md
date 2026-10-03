# Suite de livraison : qualification réelle — résultat

3 octobre 2026. Mandat : `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, avec sa
« Clarification du responsable », son « Livrable attendu maintenant », sa
« Revue du script trivial en cours » et son « Constat revue immédiat ».
Périmètre : runner/runtime/qualification (`integrations/`, Orchestrator) +
un patch additif séparé pour Oria.HQ — jamais `src/server/ai/*` (Cursor),
jamais le chantier en cours non commité dans `hq-acces-reprise`.

**Ce document remplace les sections 2/3+4/Revue de sa version précédente** :
une seconde revue a rejeté l'approche raw ACP, trouvé que les fichiers du
patch identité avaient été laissés non suivis dans `hq-acces-reprise`
(malgré le mandat de patch séparé), que le README affirmait un nombre
d'erreurs TS obsolète, et qu'email seul comme clé fusionnerait des comptes
de fournisseurs distincts. Les trois corrigés ci-dessous.

## 1. Correction : pas de « connexion fournisseur vérifiée » (inchangé)

`auth status --json` sous `--network none` lit UNIQUEMENT l'état de
session déjà persisté localement — jamais contacté un serveur distant.
Corrigé dans `integrations/openhands-claude-runtime/RESULTS.md` et les deux
résultats du 2 octobre. Toujours vrai, non revisité cette passe.

## 2. Raccordement accountId — patch corrigé, zéro trace dans hq-acces-reprise

**Défauts de la version précédente, corrigés** :
1. Les fichiers `account-identity-binding.ts`/`.test.mjs` avaient été
   laissés non suivis (`??`) dans `hq-acces-reprise` après extraction du
   patch — le mandat de patch séparé interdit d'écrire dans cette copie,
   même sans les committer. **Supprimés** de `hq-acces-reprise` ; cette
   passe n'y a plus RIEN écrit. Le patch a été réécrit, testé et extrait
   entièrement depuis un répertoire externe (`node:module` `createRequire`
   pointé sur le `package.json` de `hq-acces-reprise` pour emprunter son
   `jiti`/`typescript` installés, sans y copier aucun fichier), puis
   construit programmatiquement et vérifié par application réelle
   (`git apply`) dans un dépôt jetable séparé — jamais dans `hq-acces-reprise`.
2. Le README du patch affirmait « mêmes 12 erreurs TS Cursor » — faux,
   jamais revérifié contre l'état réel. **Remplacé par la sortie exacte de
   cette passe** : `npx tsc --noEmit` sur tout `hq-acces-reprise`, exécuté
   à l'instant, **zéro erreur, exit 0**.
3. La clé du store était `email` seul — fusionnerait silencieusement un
   compte Claude et un compte Codex séparé partageant le même email humain,
   ou le même fournisseur sous deux workspaces différents. **Corrigé** :
   clé étendue à `(provider, workspaceId, email)`. Deux tests nouveaux
   prouvent exactement ce défaut (même email, fournisseur différent →
   `accountId` différent ; même email, workspace différent → `accountId`
   différent). **13/13** tests, exécutés depuis l'extérieur du dépôt
   (`node --test <chemin externe>` avec `cwd=hq-acces-reprise` pour
   résoudre `jiti`), zéro fichier créé dans le dépôt pour les faire
   tourner.

Limite nommée explicitement (pas dissimulée) : le module livré n'est PAS un
raccordement opérationnel — seul un store en mémoire (test uniquement) est
fourni ; aucun store persistant/protégé réel n'existe. Détail complet,
prérequis, exemple de code à jour :
`docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RACCORDEMENT-COMPTE-PROPOSITION-2026-10-03.md`.
Patch : `patches/hq-account-identity-binding/`.

## 3+4. Script raw ACP rejeté ; preuve réelle via le vrai contrat de lancement SDK

**`qualify_trivial_mission.py` retiré comme critère de livraison**, comme
demandé : raw ACP stdio contourne `BudgetPermissionAgent` entièrement — le
binaire `claude-agent-acp` réellement bundlé n'expose aucun passthrough
`maxTurns`/`maxBudgetUsd`/`meta`, donc ce chemin ne peut structurellement
jamais imposer `maxCostCents`/`maxTokens`, quoi que son propre gate
prétende vérifier. Fichier conservé non exécutable par défaut (ses
variables d'environnement requises restent absentes), docstring mise à
jour nommant explicitement ce rejet et renvoyant vers le vrai contrat —
aucun développement supplémentaire de cette piste, aucun deuxième chemin
raw ACP créé.

**Priorité donnée au vrai runner/SDK déjà construit**, comme demandé.
`integrations/openhands-runner/run_mission.py::execute()` est le contrat de
lancement réel : construit un vrai `openhands.sdk.Conversation` avec un
vrai `BudgetPermissionAgent`, qui transmet réellement `maxTurns`/
`maxBudgetUsd` au CLI Claude via le mécanisme SDK `ACPSessionMeta`
(`integrations/openhands-permission-extension/budget_agent.py`) — chose
que raw ACP stdio ne peut pas atteindre. `qualify_run_mission.py` (déjà
existant, déjà qualifié sur VPS le 30 septembre, jamais réécrit par ce
lot) exerce ce contrat avec un pair ACP SYNTHÉTIQUE (`budget_peer.py`) —
zéro appel modèle.

**L'absence d'hôte runner déployé n'empêche pas une qualification locale
isolée du runner déjà construit** — confirmé en le faisant, cette passe :

1. Images réutilisées/complétées sans reconstruction générale :
   `oria-openhands-qualification:sdk1.50.0`,
   `oria-openhands-qualification:permissions1` (déjà construites, lot
   précédent) ; alias ajouté `oria-openhands-claude:qualification1` →
   l'image déjà construite `oria-openhands-claude-runtime:candidate1`
   (même ID, aucune reconstruction — correction d'une incohérence de nom
   que j'avais introduite au lot précédent, les scripts `qualify_run_mission.py`/
   `Dockerfile.budgets`/`qualify.sh` attendaient tous ce nom) ; nouvelle
   couche additive `oria-openhands-claude:budgets1`
   (`integrations/openhands-permission-extension/Dockerfile.budgets`, hash
   du patch de budget vérifié enchaîné sur le hash déjà documenté du patch
   de permissions) ; nouvelle image `oria-openhands-runner:qualification1`
   (`integrations/openhands-runner/Dockerfile`, le contrat de lancement
   réel packagé).
2. Exécution isolée, cette passe, sortie exacte :
   ```
   $ docker run --rm --network none --read-only --cap-drop ALL \
       --security-opt no-new-privileges --pids-limit 256 --memory 1g --cpus 1 \
       --tmpfs /tmp:rw,nosuid,nodev,size=128m \
       --tmpfs /home/runner:rw,nosuid,nodev,size=32m,uid=10001,gid=10001 \
       --entrypoint python oria-openhands-runner:qualification1 \
       /runner/qualify_run_mission.py

   {"payloadHash": "f063eb83d217a0306f9d3a2eb53a52db7be6c49527a4be1157ee372d7801dfa4",
    "state": "agent_returned", "independentValidationPassed": false,
    "hardTokenLimitEnforced": false, "permissions": "default_deny",
    "externalDeadlineRequired": true, "sdkExecutionStatus": "finished",
    "actualSdk": true, "syntheticAcpPeer": true, "modelCalls": 0,
    "repeatDenied": true, "conversationPersisted": true}
   exit=0
   ```
   `--tmpfs /home/runner` ajouté après un premier échec réel et honnête
   (`OSError: Read-only file system: '/home/runner/.openhands'` — le SDK a
   besoin d'un HOME inscriptible pour son profile store ; exigence
   technique réelle, pas une concession de sécurité, même montage que
   `qualify.sh` utilise déjà ailleurs dans ce dépôt).
3. Preuve, pas promesse : vraie SDK (`actualSdk`), pair ACP synthétique
   (`syntheticAcpPeer`), zéro appel modèle (`modelCalls:0`), garde
   une-seule-fois confirmée (`repeatDenied` — une seconde invocation
   identique a été refusée par le fichier `started.json` déjà créé),
   conversation persistée sur disque (`conversationPersisted`),
   `permissions:"default_deny"` (politique de refus par défaut de
   `BudgetPermissionAgent` active). Conteneur supprimé (`--rm`), vérifié
   sans résidu par label.

**Ce qui reste bloqué pour une mission RÉELLEMENT authentifiée (pas le pair
synthétique)** — nommé précisément, rien de fabriqué :
1. **Corrigé par rapport à la rédaction initiale** : `provider_policy.py`
   exige `os.name=='posix'`, mais `docker info` confirme un backend Linux
   réel sur cette machine — n'importe quel conteneur déjà construit ici
   satisfait cette exigence. Ce n'est donc PAS un hôte manquant ; le point
   réel est qu'aucun objet `AUTHORIZATION` réel n'est encore écrit par
   l'opérateur dans une configuration root-only, où que ce soit —
   l'infrastructure existe, l'autorisation écrite non.
2. Aucun mécanisme d'identité de compte sûr n'est encore RACCORDÉ (§ 2/2bis)
   — le patch persistant existe, testé, non appliqué ; même appliqué,
   `local-runtime-probe.ts` n'appelle pas encore `resolveOpaqueAccountId`.
3. Le relai réseau restreint est qualifié avec un pair synthétique
   uniquement — non activé pour une session Claude réellement authentifiée.

Aucun de ces trois points n'est une case que ce lot peut remplir seul.
**Ne pas assimiler l'absence de coût observé à un coût nul** : aucune
mission réelle n'a été lancée, donc aucun usage n'a été consommé — pas la
preuve qu'il aurait été nul.

## 2bis. Stockage réel livré (remplace le helper mémoire), après qualification SDK

Corrections additionnelles reçues : `docker info` confirme un backend
Linux réel (vérifié : `OSType: linux`) — l'absence d'hôte runner déployé
était un écart d'assemblage de ma part, pas une contrainte d'OS ; et les
fichiers non suivis dans `hq-acces-reprise` sont des lots déjà intégrés
par le parent, pas une activité concurrente — « pas de modifications
concurrentes » ne s'appliquait plus à ces fichiers précis.

Livré : `patches/hq-account-identity-binding/account-identity-repository.patch`,
stockage RÉEL remplaçant le helper en mémoire, réutilisant le pattern déjà
approuvé `approval-record-repository.ts` (Supabase en production, repli
mémoire local gardé par `isLocalPersistenceFallbackAllowed`, échec fermé
en production) — aucun mécanisme de stockage inventé. Clé toujours
`(provider, workspaceId, email)`. Écrit en place dans `hq-acces-reprise`
cette fois (nouveaux fichiers sous contrôle parent, rien d'autre touché,
vérifié par comptage de statut avant/après), pour un `tsc --noEmit` réel
avec résolution des alias `@/*` — propre, exit 0, tout le dépôt. 12/12
tests (identité stable, restart, changement de compte par fournisseur/
workspace/email, refus explicite sur champ vide, non-déterminisme,
non-fuite d'email, normalisation, échec fermé en production).

## Nettoyage et provenance

L'helper mémoire `account-identity-binding.ts`/`.test.mjs` a été supprimé
de `hq-acces-reprise` puis remplacé par le stockage réel
`account-identity-repository.ts`/`.test.mjs` (§ 2bis), laissé en place
sous contrôle parent — rien d'autre dans ce worktree touché (vérifié par
comptage de statut avant/après). Conteneur de qualification SDK supprimé
(`--rm`), vérifié sans résidu par label. Images Docker locales conservées
intentionnellement (livrable réutilisable, pas des ressources temporaires).
`__pycache__` nettoyé. Aucun fichier de credentials touché. Aucune mission
modèle réelle lancée, aucun déploiement, catalogue Cursor non touché,
qualification Antigravity du lanceur non touchée.

## Revue ciblée (sur le patch identité, avant les corrections ci-dessus)

Un sous-agent natif en lecture seule (`Explore`), contexte limité au diff
du patch + critères de revue, a trouvé deux défauts réels sur la PREMIÈRE
version du patch (aucune fuite) : test de non-déterminisme insuffisant (ne
prouvait qu'une dérivation écartée, pas l'aléa réel) et absence de
normalisation de l'email avant usage comme clé. Les deux corrigés, avec
tests nommés, avant la seconde revue utilisateur qui a ensuite trouvé les
trois défauts de process/clé listés en § 2 ci-dessus — tous corrigés dans
cette version.

## Fichiers modifiés / ajoutés (Orchestrator, ce worktree)

```
M integrations/openhands-claude-runtime/RESULTS.md
M docs/CLAUDE-BUILD-CANDIDAT-CONNEXION-RESULTAT-2026-10-02.md
M docs/CLAUDE-REPRISE-OPENHANDS-OPERATIONNELLE-RESULTAT-2026-10-02.md
M docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RACCORDEMENT-COMPTE-PROPOSITION-2026-10-03.md
M docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RESULTAT-2026-10-03.md (ce fichier)
D patches/hq-account-identity-binding/account-identity-binding.patch (superseded)
A patches/hq-account-identity-binding/account-identity-repository.patch
M patches/hq-account-identity-binding/README.md
M integrations/openhands-claude-runtime/qualify_trivial_mission.py (docstring de rejet)
A integrations/openhands-claude-runtime/test_qualify_trivial_mission.py (lot précédent, inchangé)
```

Côté Oria.HQ (`hq-acces-reprise`) : deux fichiers neufs présents, sous
contrôle parent — `src/server/agents/models/account-identity-repository.ts`
et son `.test.mjs` (non suivis, non committés, jamais entré ce worktree via
l'outil dédié). Les deux fichiers de l'ancien helper mémoire ont été
supprimés avant ceux-ci (jamais committés, suppression sûre). Aucun autre
fichier de ce worktree touché, y compris le chantier en cours.

Images Docker locales (non versionnées, listées pour provenance) :
`oria-openhands-qualification:sdk1.50.0`,
`oria-openhands-qualification:permissions1`,
`oria-openhands-claude-runtime:candidate1` =
`oria-openhands-claude:qualification1` (alias, même ID
`sha256:9e23766db51e3e215d0fe4ae1b146b7b3c827e28a65e3105a0c2a724a9a089b5`),
`oria-openhands-claude:budgets1`, `oria-openhands-runner:qualification1`.

## Prochaine action concrète unique

Décision de Michael sur les trois blocages nommés en § 3+4 (écrire une
autorisation réelle sur un hôte déjà disponible — infrastructure, pas
déploiement ; appliquer et raccorder le patch d'identité § 2bis dans
`classifyClaudeCodeProbe` ; activer le relai réseau restreint pour une
session réellement authentifiée) — pas une approbation abstraite, ces
trois décisions précises.
