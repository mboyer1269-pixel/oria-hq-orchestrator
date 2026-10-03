# Suite de livraison : qualification réelle — résultat

3 octobre 2026. Mandat : `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, avec sa
« Clarification du responsable » et son complément « livre patch HQ séparé
testable ». Périmètre : runner/runtime/qualification (`integrations/`,
Orchestrator) + un patch additif séparé pour le worktree Oria.HQ
`hq-acces-reprise` — jamais `src/server/ai/*` (Cursor), jamais le chantier
en cours non commité détecté là (voir § « Pas de modifications
concurrentes » ci-dessous).

## 1. Correction : pas de « connexion fournisseur vérifiée »

`auth status --json` sous `--network none` (mandat précédent) lit
UNIQUEMENT l'état de session déjà persisté localement — jamais contacté un
serveur distant. Corrigé dans :
- `integrations/openhands-claude-runtime/RESULTS.md` (deux sections,
  l'ancienne en réseau `bridge` incluse — aucune preuve qu'un appel réseau
  réel ait eu lieu là non plus).
- `docs/CLAUDE-BUILD-CANDIDAT-CONNEXION-RESULTAT-2026-10-02.md`.
- `docs/CLAUDE-REPRISE-OPENHANDS-OPERATIONNELLE-RESULTAT-2026-10-02.md`.

Ce qui est réellement prouvé : ce CLI plus récent lit le même fichier de
credentials sans erreur (compatibilité de FORMAT). Ce qui ne l'est pas :
que le fournisseur distant accepte encore ce jeton aujourd'hui.

## 2. Raccordement accountId — inspection, puis patch testé livré séparément

**Inspection** (`hq-acces-reprise`, lecture seule) : un chantier substantiel,
non commité, était déjà en cours au moment de ce lot — `accountId`/
`catalogRevision` raccordés dans `model-emission-gate.ts`/
`model-emission-launch-gate.ts`, jamais depuis `orgId` ni `providerProfile.id`
(corrigé par une revue indépendante antérieure, caught before activation).
113/113 tests, `npx tsc --noEmit` propre. **Non touché** (« pas de
modifications concurrentes ») — vérifié seulement, jamais dupliqué ni
patché par-dessus.

Constat : `accountId` reste structurellement absent pour `claude-code-cli`
aujourd'hui, car aucun champ per-UTILISATEUR (pas par-organisation) sûr
n'existe dans `claude auth status --json` — `email` était délibérément
jamais lu (hash d'un identifiant personnel = réversible par dictionnaire).

**Clarification utilisateur reçue en cours de lot** : l'interdiction porte
sur l'INVENTION d'identité, pas sur l'usage d'un identifiant officiel en
soi. Une liaison OPAQUE côté serveur (jamais un hash) reste possible.

**Patch livré, testé, séparé, non appliqué** :
`patches/hq-account-identity-binding/` (diff unifié + README). Deux
fichiers NEUFS uniquement — `account-identity-binding.ts` (accountId =
UUID aléatoire, jamais dérivé de l'email ; table d'indirection email→id
injectée, jamais lue/journalisée au-delà) et son test (9 cas). Testé
directement dans `hq-acces-reprise` (additif pur, zéro conflit avec le
chantier en cours), `tsc` propre, puis extrait et le worktree remis dans son
état `??` d'origine. Revue ciblée bornée (un sous-agent lecture seule,
contexte limité au diff + critères) lancée sur ce patch spécifiquement —
voir verdict à la fin de ce document.

Détail complet, prérequis (accord de Michael pour un nouveau stockage de
données personnelles, décision sur la rotation d'email, attendre que le
chantier en cours soit commité) :
`docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RACCORDEMENT-COMPTE-PROPOSITION-2026-10-03.md`.

## 3+4. Recette mission triviale — prête, testée, blocage exact reproductible

`integrations/openhands-claude-runtime/qualify_trivial_mission.py` (nouveau) :
recette complète pour « créer un fichier texte, vérifier son contenu » via
la VRAIE entrée ACP (`initialize`/`session/new`/`session/prompt` réels,
jamais le script de diagnostic). Réutilise le handshake déjà qualifié de
`qualify_initialize.py` et `provider_policy.validate_authorization`
(`../openhands-runner`) — jamais un second mécanisme d'autorisation inventé.

Gate réel avant tout envoi de prompt, deux artefacts exigés, ni l'un ni
l'autre fabriqué par ce lot :
- `ORIA_TRIVIAL_MISSION_AUTHORIZATION_FILE` — objet `AUTHORIZATION` réel
  (`profileId`/`policySha256`/`policyRoot`/`gatewayRoot`), validé par la
  MÊME fonction que le vrai runner.
- `ORIA_TRIVIAL_MISSION_BUDGET_FILE` — `maxCostCents`/`maxTokens`/
  `maxIterations`/`timeoutSeconds`, entiers positifs stricts,
  `maxIterations` doit être exactement 1 (ce script n'envoie jamais plus
  d'un `session/prompt`, par construction).

Honnêteté documentée sur ce qui est réellement forcé : `timeoutSeconds` et
`maxIterations=1` le sont réellement (code). `maxCostCents`/`maxTokens` ne
le sont PAS au niveau transport — recherché dans le binaire
`claude-agent-acp` réellement bundlé dans ce candidat : aucun passthrough
`maxTurns`/`maxBudgetUsd`/`meta` (mécanisme utilisé par
`integrations/openhands-permission-extension/budget_agent.py`, mais qui
n'existe qu'au niveau SDK OpenHands, jamais atteint par de l'ACP stdio
brut). Documenté, pas caché.

**Exécution réelle, sans aucune variable d'environnement (état honnête
actuel)** :
```
$ python qualify_trivial_mission.py
{"ok": false, "blocker": "ORIA_TRIVIAL_MISSION_AUTHORIZATION_FILE is not set"}
exit=10
```
Reproductible, exact, sans secret. 14 tests fixtures
(`test_qualify_trivial_mission.py`) prouvent chaque branche du gate
(fichier manquant, JSON invalide, forme invalide, champ manquant/en trop,
valeur non-positive, booléen déguisé en entier, `maxIterations`>1) —
**14/14 passés**.

**Aucune authorization/budget fabriquée pour aller plus loin** — ce serait
exactement le faux jeton d'approbation interdit par le mandat. Ce qui
bloque réellement un lancement aujourd'hui, nommé précisément :

1. `provider_policy.py` exige `os.name=='posix'` (hôte Linux) pour
   `protected_bytes()` — aucun hôte runner Linux déployé, ce laptop Windows
   ne peut structurellement pas porter ce mécanisme.
2. Un objet `AUTHORIZATION` réel doit être écrit par l'opérateur dans une
   configuration root-only sur CET hôte — n'existe nulle part aujourd'hui.
3. `RUNNER_EXECUTOR_PROBE_APPROVAL` (`runner-executor-connection-probe.ts`,
   HQ) vaut `{status:"not_approved"}` par construction, sans hôte SSH ni
   fichier d'identité configurés — aucun défaut n'existe à activer.
4. Le relai réseau restreint (`integrations/openhands-runner/PROVIDER-RELAY.md`)
   est qualifié avec un pair de test SYNTHÉTIQUE uniquement — « non activé »
   pour une mission Claude réellement authentifiée.

Aucun de ces quatre points n'est une case à cocher que ce lot peut remplir
seul — chacun est soit une décision opérateur (écrire une vraie
autorisation, choisir un mécanisme d'identité de compte), soit un
déploiement d'infrastructure réelle (hôte runner, relais réseau activé).
**Ne pas assimiler cette absence de coût observé à un coût nul** : aucune
mission n'a été lancée, donc aucun usage n'a été consommé — ce n'est pas la
preuve que le coût aurait été nul si elle l'avait été.

## Nettoyage et provenance

Aucune ressource Docker temporaire créée par ce lot (seul le gate Python a
tourné, sur l'hôte, jamais dans le candidat image cette fois — le
handshake réel ACP n'a jamais été atteint). `__pycache__` nettoyé. Aucun
fichier de credentials touché. Aucune mission modèle réelle lancée, aucun
déploiement, catalogue Cursor non touché, qualification Antigravity du
lanceur non touchée.

## Revue ciblée (au plus une, comme demandé)

Un sous-agent natif en lecture seule (`Explore`), contexte limité au diff
du patch `account-identity-binding.ts`/`.test.mjs` + critères de revue
(fuite d'email par dérivation/journalisation, stabilité/absence de race,
tests probants) a été lancé sur ce patch spécifiquement.

**Verdict** : deux défauts réels trouvés, aucune fuite. (1) Le test « pas un
hash » ne prouvait qu'une seule dérivation déterministe écartée (sha256),
pas l'aléa réel — corrigé par un test résolvant le même email contre deux
stores indépendants frais, prouvant que deux résultats différents. (2)
Aucune normalisation de l'email avant usage comme clé de recherche — un
même compte réel renvoyant son email avec une casse ou un espace différent
entre deux sondes aurait silencieusement créé deux `accountId` distincts
pour un seul compte, cassant la garantie de stabilité que ce module existe
pour fournir — corrigé : `email.trim().toLowerCase()` avant toute
recherche/écriture, forme normalisée aussi persistée. Les deux corrigés par
moi-même (jamais délégués), tests ajoutés nommément pour chaque défaut,
**12/12** après correction, `tsc` toujours propre. Patch regénéré avec les
corrections, répertoire HQ revérifié intact (toujours `??`, aucun autre
fichier touché, y compris les nouveaux fichiers additionnels du chantier en
cours apparus entre-temps).

## Fichiers modifiés / ajoutés (Orchestrator, ce worktree)

```
M integrations/openhands-claude-runtime/RESULTS.md
M docs/CLAUDE-BUILD-CANDIDAT-CONNEXION-RESULTAT-2026-10-02.md
M docs/CLAUDE-REPRISE-OPENHANDS-OPERATIONNELLE-RESULTAT-2026-10-02.md
A docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RACCORDEMENT-COMPTE-PROPOSITION-2026-10-03.md
A docs/CLAUDE-SUITE-QUALIFICATION-REELLE-RESULTAT-2026-10-03.md
A patches/hq-account-identity-binding/account-identity-binding.patch
A patches/hq-account-identity-binding/README.md
A integrations/openhands-claude-runtime/qualify_trivial_mission.py
A integrations/openhands-claude-runtime/test_qualify_trivial_mission.py
```

Côté Oria.HQ (`hq-acces-reprise`) : deux fichiers neufs, additifs, laissés
`??` non suivis, non commités (jamais entré ce worktree via l'outil dédié) —
`src/server/agents/models/account-identity-binding.ts` et son `.test.mjs`.
Aucun autre fichier de ce worktree touché, y compris le chantier en cours.

## Prochaine action concrète unique

Décision de Michael sur les quatre blocages nommés en § 3+4 (au minimum :
veut-il qu'on déploie un hôte runner Linux minimal pour lever le blocage 1,
et quel mécanisme d'identité de compte approuve-t-il pour le blocage 3/le
patch § 2) — pas une approbation abstraite, ces quatre décisions précises.
