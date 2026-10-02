# Lot Codex ACP — résultat (code minimal, non activé)

2 octobre 2026. Mandat : `docs/CLAUDE-CODEX-ACP-CANDIDAT.md` (texte complet
du mandat, conservé tel quel). Périmètre exclusif respecté : Orchestrator
`integrations/openhands-*` et le contrat compagnon
`Oria.HQ/.claude/worktrees/hq-acces-reprise/src/core/openhands-launch-contract.ts`
+ ses tests directs. Aucun `src/server/ai` (Cursor), aucun UI, aucun nouveau
sous-agent.

## Base de travail corrigée avant toute modification

Le worktree créé automatiquement pour ce lot (`codex-acp-candidate`) a été
fondé par défaut sur `origin/main`, qui ne contient pas le travail déjà fait
sur `provider_policy.py` (gate d'autorisation `validate_authorization` /
`authorized_profile`). C'était exactement la « base périmée » que le mandat
interdit. Corrigé avant tout changement : `git reset --hard` du worktree sur
la pointe réelle de `codex/cursor-recovery-handoff` (aucun commit perdu, le
worktree n'avait encore que des fichiers non suivis). Vérifié ensuite par
diff que le fichier correspond exactement à celui du checkout principal.

## Découverte en cours de lot : image locale `agent-canvas` arrêtée

Michael a signalé une image Docker locale arrêtée
(`ghcr.io/openhands/agent-canvas:1.0.0-rc.11`, construite 2026-06-12, cœur
OpenHands `v1.28.1`) avec des montages existants vers
`C:/Users/micha/Dev/openhands-credentials/{claude,codex,gemini,gcloud-adc}`
et `C:/Users/micha/.openhands`. Conformément à son instruction, le
runtime n'a pas été reconstruit avant comparaison, et aucun fichier sous ces
deux chemins n'a été lu, listé ou monté — seule l'image elle-même a été
inspectée (métadonnées, historique de build, une exécution bornée
`--network none --read-only --cap-drop ALL` sans montage listant les
binaires déjà présents, sans connexion ni appel modèle).

Résultat vérifié (pas supposé) : l'image bundlait déjà trois adaptateurs ACP
sous `/opt/acp-node` avec scripts `/usr/local/bin/{claude-agent-acp,codex-
acp,gemini}` :

| Adaptateur | Version dans l'image arrêtée | Version officielle actuelle |
|---|---|---|
| Claude | `@agentclientprotocol/claude-agent-acp@0.30.0` | `0.84.0` (déjà qualifiée séparément) |
| Codex | `@zed-industries/codex-acp@0.15.0` | `@agentclientprotocol/codex-acp@2.1.1` |
| Gemini | `@google/gemini-cli@0.38.0` | hors périmètre de ce lot |

Le registre npm marque lui-même `@zed-industries/codex-acp` (versions 0.15.0
et 0.16.0) comme dépréciée : « replaced by @agentclientprotocol/codex-acp ».
C'est aussi un binaire natif différent (CLI Rust sans flag `--version`
standard), antérieur au déplacement du projet vers l'organisation GitHub
`agentclientprotocol` que la documentation officielle OpenHands
(`ACP_AGENTS.md`) cite aujourd'hui. **Conclusion vérifiée : l'adaptateur
Codex déjà présent dans l'image arrêtée n'est pas réutilisable comme
candidat qualifié** — il faudrait lui-même le qualifier comme un artefact
non officiel et obsolète, ce qui contredit l'exigence de provenance du
mandat. Le patron de l'image (runtime Node privé + scripts wrapper PATH) est
en revanche un précédent valide, déjà utilisé ailleurs dans ce lot sous une
forme plus étroite (un conteneur par fournisseur, pas un all-in-one).

Détails complets, versions exactes et commandes reproductibles :
`integrations/openhands-codex-runtime/README.md` et `RESULTS.md`.

## Livrables de ce lot

1. **`integrations/openhands-runner/provider_policy.py`** — `EXPECTED` (un
   seul vendeur en dur) remplacé par `PROVIDER_POLICIES = {'claude': {...},
   'codex': {...}}`, chaque entrée explicitement écrite (pas une énumération
   élargie sur un seul champ). `validate_profile`/`validate_manifest`
   sélectionnent le template par le `provider` déclaré du profil et
   refusent toute valeur hors de cette liste (`Unsupported provider`) ou
   tout champ qui dévie du template choisi. Alias `EXPECTED` conservé pour
   la compatibilité du profil Claude déjà qualifié et de
   `qualify_hq_postgrest.py`. Tests directs ajoutés dans
   `test_provider_policy.py` : profil Codex valide et strict indépendamment
   (chaque champ affaibli échoue sous Codex, pas seulement sous Claude),
   fournisseur inconnu refusé, et le cas de reproxy direct — un manifeste au
   contenu Claude (y compris son propre champ `provider` interne) ne peut
   jamais satisfaire un profil qui déclare `provider: "codex"`, et
   inversement. Suite complète : **168 tests passés, 27 ignorés
   (dépendants de Linux), 0 échec** (`python -m unittest discover`).

2. **`Oria.HQ/.../src/core/openhands-launch-contract.ts`** —
   `providerProfileSchema` passe d'un objet unique à `z.literal("claude")`
   vers une **union discriminée** de deux schémas explicites et stricts
   (`claudeProviderProfileSchema`, `codexProviderProfileSchema`), chacun
   verrouillé champ par champ, miroir exact du dictionnaire Python. Test
   direct ajouté : `src/core/openhands-launch-contract.test.mjs` (6 cas,
   tous verts) — variante par fournisseur, fournisseur inconnu refusé,
   champ affaibli refusé sous chaque variante indépendamment, compatibilité
   du chemin sans `providerProfile`. `npx tsc --noEmit` sur tout le dépôt :
   **0 erreur**. Aucun fichier `src/server/ai` touché ;
   `model-emission-launch-gate.ts` n'a pas eu besoin de changement (son
   `Record<string,string>` tolère déjà un `provider` élargi et refuse
   `codex` via `no_provider_binding` tant qu'il n'est pas explicitement
   câblé — hors périmètre, confirmé par lecture, pas modifié).

3. **`integrations/openhands-codex-runtime/`** — candidat minimal, calqué
   sur `../openhands-claude-runtime/` : `package.json`/`package-lock.json`
   verrouillés sur `@agentclientprotocol/codex-acp@2.1.1` (gitHead
   `68d7d2d5ddfc0ed5746f9f6130892dda685e65dd`) et son
   `@openai/codex@0.159.3` embarqué ; `Dockerfile` (même digest Node22
   figé, même doctrine « aucun secret/login dans le build ») ;
   `qualify_initialize.py` (sonde protocole ACP réelle — `initialize` +
   `session/new` — sans authentification ni appel modèle) ;
   `qualify_tools.py`/`qualify.sh` repris à l'identique. **Non construit,
   non qualifié dans cette session** : les images `oria-openhands-
   qualification:permissions1` / `oria-openhands-claude:qualification1`
   dont `PERMISSION_BASE` dépend n'existent pas sur ce Docker Desktop
   (vérifié par `docker images` avant d'écrire quoi que ce soit). État
   exact et prérequis pour qualifier ailleurs : `RESULTS.md`.

## Connexion officielle Codex — ce qui est vérifié, pas supposé

Lu directement dans le source officiel à la révision figée (`src/login.ts`,
`src/CodexAuthMethod.ts`) : `codex-acp` annonce trois méthodes
d'authentification ACP — `api-key` (exclue, c'est le repli payant),
`chat-gpt` (connexion abonnement ChatGPT, celle à utiliser) et `chat-gpt-
device-code` (même connexion abonnement, variante terminal distant). La
sous-commande `codex-acp login` démarre l'App Server Codex embarqué, lit le
compte, et si absent ouvre un navigateur vers une `authUrl` puis attend
l'événement `account/login/completed`. Ceci écrit dans le magasin
d'identifiants propre au binaire Codex embarqué — jamais le
`~/.codex/auth.json` de Hermes, aucune copie ni extraction de jeton. Ne
jamais positionner `CODEX_API_KEY`/`OPENAI_API_KEY` dans cet environnement :
cela basculerait silencieusement vers le repli payant. Aucune connexion
réelle n'a été tentée par ce lot.

## Ce qui n'a pas été fait (arrêt volontaire)

Authentification interactive/consentement de compte, déploiement VPS,
construction ou exécution de l'image candidate, modification de l'image
`agent-canvas` locale, lecture des répertoires d'identifiants Hermes,
élargissement du registre de policies déployé ou de
`model-emission-launch-gate.ts`, tout travail Gemini/Antigravity au-delà de
leur mention neutre (toujours « à qualifier », jamais annoncés compatibles
ni oubliés).

## Prochains prérequis

1. Reconstruire ou localiser `PERMISSION_BASE` et l'image de qualification
   Claude sur un hôte qui les a déjà, pour pouvoir construire et qualifier
   `openhands-codex-runtime` par le protocole seul (sans login).
2. Exécuter `codex-acp login` (abonnement ChatGPT) de façon indépendante
   dans cet environnement candidat, jamais via une lecture du conteneur
   Hermes.
3. Écrire et faire approuver (`validate_authorization`) une policy Codex
   réelle (`squid.conf`/`entrypoint.sh`/`relay.mjs` propres à sa surface
   réseau/env, pas copiés de Claude) dans le registre déployé, puis étendre
   `PROVIDER_PROFILE_TO_REGISTRY_PROVIDER_ID` côté HQ — décision et travail
   séparés, hors de ce lot.
4. Qualifier Gemini CLI séparément d'Antigravity, comme déjà cadré dans
   `docs/HQ-ABONNEMENTS-EXECUTANTS.md`.
