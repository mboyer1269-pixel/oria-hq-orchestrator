# Suite exécutant opérationnel — résultat

Exécution de `docs/CLAUDE-EXECUTANT-OPERATIONNEL-SUITE.md`. Étape 1 terminée et
livrée (code + test). Étapes 2 et 3 préparées avec commandes exactes mais
**non exécutées sur le VPS**, sur décision explicite de l'utilisateur après
refus du classificateur auto-mode (détail en fin de document) — le parent
intègre le code et traite ce blocage opérateur.

## Étape 1 — fixture sans identifiants (fait)

Testé l'image candidate réelle `oria-openhands-claude:qualification1` contre
un volume Docker jetable (Linux natif, pas un chemin Windows — les sémantiques
uid/mode exactes comptent ici) jouant le rôle du vrai volume : HOME
`uid=10001 mode=755`, `.claude` vide `uid=10001 mode=755`. Aucun identifiant
réel, aucun secret cloné — répertoire jamais logué.

Commandes exécutées (fixture jetable uniquement) : `claude-agent-acp --cli
--version` puis `--cli auth status --json`, avec un instantané complet de
l'arborescence avant/après.

**Constat empirique décisif** : même ces deux commandes de diagnostic créent
`~/.claude.json` (mode 600) et `~/.claude.json.lock` (mode 755) **directement
sous HOME**, pas sous `.claude`. La correction précédemment proposée (chown de
HOME vers root) aurait donc cassé le CLI dès la première invocation — le
risque déjà signalé la dernière fois est confirmé réel, pas hypothétique.

**Correction minimale validée** : resserrer uniquement `.claude` à `0700` ;
HOME reste `10001:10001 mode 755`, intact. Revérifié sur une fixture fraîche :
avec ce resserrement seul, `--version` (exit 0) et `auth status --json`
(exit 1, `loggedIn:false` attendu sur une fixture vide) réussissent de façon
identique à l'état non resserré — aucune erreur de permission.

Ce resserrement seul ne suffit pas côté code : `inspect_auth_directory`
exigeait que **chaque** parent de `.claude` soit root — or le vrai parent
(`_data` = HOME) est et doit rester `uid=10001`. Corrigé dans
`provider_policy.py` :
- **Avant** : tout parent non-root est refusé, quel que soit son mode.
- **Après** : un parent est accepté s'il est root **ou** appartient au MÊME
  uid que la feuille elle-même (jamais un tiers), et n'a aucun bit d'écriture
  groupe/autre. Un tiers reste refusé explicitement. La fermeture TOCTOU
  reste intacte : chaque appelant (`container_job.create_job`,
  `permission_worker`) relit ce même `(dev, inode)` juste avant montage.

Fichiers modifiés (worktree `.claude/worktrees/executant-operationnel`,
branche `worktree-executant-operationnel`) :
- `integrations/openhands-runner/provider_policy.py`
- `integrations/openhands-runner/test_auth_context.py` (+1 test :
  `test_parent_may_be_the_leafs_own_owner_but_never_a_third_uid`, qui vérifie
  aussi qu'un tiers reste refusé et qu'un bit d'écriture groupe/autre sur ce
  même parent reste refusé)

Tests exécutés (ciblés, Linux réel via conteneur root, pas la suite complète
déjà rejouée par le parent) : `test_provider_policy`, `test_auth_context`,
`test_container_job`, `test_permission_worker`, `test_run_host_job`,
`test_reconcile_launch` → **53/53 verts**, aucune régression.

Note de rigueur : la fixture locale utilise l'image locale
`oria-openhands-claude:qualification1` (ID `9e23766db51e`, build
2026-10-02). L'image réellement déployée sur le VPS porte le même tag mais un
ID différent (`0c894a12d134`, build 2026-09-30) — pas de rebuild entre les
deux dans ce lot. Le comportement observé (`.claude.json`/`.claude.json.lock`
sous HOME) vient du CLI `@anthropic-ai/claude-agent-sdk` embarqué, pas d'un
script propre à ce dépôt, donc peu probable qu'il diffère — mais non vérifié
bit-à-bit sur l'image VPS exacte dans ce lot.

## Étape 2 — resserrement réel sur le VPS (préparée, NON exécutée)

Métadonnées de départ capturées (lecture seule, VPS réel) :
```
/var/lib/docker/volumes/oria-openhands-claude-auth/_data          uid=10001 gid=10001 mode=755
/var/lib/docker/volumes/oria-openhands-claude-auth/_data/.claude  uid=10001 gid=10001 mode=755
```
Connexion confirmée avant toute modification (champs sûrs seulement, jamais
l'email/orgId) : `loggedIn:true`, `authMethod:"claude.ai"`,
`apiProvider:"firstParty"`, `subscriptionType:"pro"`, exit 0.

Commande exacte proposée — un seul chmod, rien sur HOME :
```sh
chmod 700 /var/lib/docker/volumes/oria-openhands-claude-auth/_data/.claude
```
Vérification à exécuter immédiatement après (champs sûrs seulement) :
```sh
docker exec oria-openhands-claude-login claude-agent-acp --cli auth status --json
```
Attendu : identique à l'état « avant » (`loggedIn:true`,
`authMethod:"claude.ai"`, `apiProvider:"firstParty"`), exit 0.

Retour arrière exact si le CLI casse ou si la vérification diffère :
```sh
chmod 755 /var/lib/docker/volumes/oria-openhands-claude-auth/_data/.claude
```

## Étape 3 — qualification du candidat dans un conteneur distinct (préparée, NON exécutée)

But : lancer `oria-openhands-runner:auth-context1` (image locale, digest
`sha256:f09e1b71c2b7...`) dans un conteneur **séparé** sur le VPS (ne
remplace jamais `oria-openhands-claude-login` ni aucun service actif),
monter le volume `oria-openhands-claude-auth` en lecture seule exactement
comme le prévoit authContext, et vérifier que `claude-agent-acp --cli auth
status --json` réussit dans ce nouveau conteneur — sans jamais envoyer de
prompt ni déclencher de génération.

À exécuter seulement après l'étape 2 confirmée bonne :
```sh
# 1. Transférer l'image locale vers le VPS (ne remplace rien)
docker save oria-openhands-runner:auth-context1 | gzip \
  | ssh -i ~/.ssh/codex_vps root@2.24.118.156 'gunzip | docker load'

# 2. Lancer un conteneur DISTINCT, réseau none, montage lecture seule
ssh -i ~/.ssh/codex_vps root@2.24.118.156 '
docker run -d --name oria-openhands-runner-qualify-authcontext1 \
  --network none --read-only \
  --mount type=volume,src=oria-openhands-claude-auth,dst=/home/runner/.claude,readonly \
  oria-openhands-runner:auth-context1 sleep 300
'

# 3. Vérifier la connexion officielle SANS appel de génération (champs sûrs seulement)
ssh -i ~/.ssh/codex_vps root@2.24.118.156 '
docker exec oria-openhands-runner-qualify-authcontext1 claude-agent-acp --cli auth status --json
'

# 4. Nettoyer le conteneur jetable (ne touche à rien d'autre)
ssh -i ~/.ssh/codex_vps root@2.24.118.156 'docker rm -f oria-openhands-runner-qualify-authcontext1'
```
Attendu : `loggedIn:true`, `authMethod:"claude.ai"`, `apiProvider:"firstParty"`,
exit 0, dans ce conteneur neuf — preuve que le candidat `auth-context1` peut
réellement lire la connexion existante une fois le stockage resserré, sans
avoir touché à aucun service actif.

## Pourquoi étapes 2 et 3 ne sont pas exécutées

J'ai tenté le chmod de l'étape 2 sur le VPS réel ; **le classificateur
auto-mode de Claude Code l'a refusé** (« Blocked by classifier »). Ce n'est
pas une limite imposée par ce mandat ni par le code — c'est le garde-fou
intégré à l'outil pour une commande qui modifie une infrastructure réelle.
Interrogé, l'utilisateur a choisi explicitement : livrer le correctif, les
tests et les commandes exactes maintenant ; ne pas modifier les règles de
permission ; ne pas contourner le refus par une autre voie ; laisser les
étapes VPS non exécutées pour que le parent les traite comme blocage
opérateur. L'étape 3 dépend de l'étape 2 et n'a donc pas été tentée non plus.

## Ce qui fonctionne réellement aujourd'hui

- authContext + `resolveOpaqueAccountId` (lot précédent) : 77 tests, rejoués
  par le parent, verts.
- Correction d'`inspect_auth_directory` (ce lot) : 53 tests ciblés verts,
  aucune régression, validée empiriquement contre le comportement réel du
  CLI (pas une hypothèse).
- Le stockage VPS réel reste, à ce stade, **non resserré** (`.claude` toujours
  en mode 755) : authContext refuserait encore de monter ce volume tel quel.

## Blocage restant

Les deux commandes mutantes ci-dessus (étapes 2 et 3) restent à exécuter par
l'opérateur. Rien d'autre n'est bloquant dans ce lot : commandes, vérification
et retour arrière sont prêts à copier-coller tels quels.
