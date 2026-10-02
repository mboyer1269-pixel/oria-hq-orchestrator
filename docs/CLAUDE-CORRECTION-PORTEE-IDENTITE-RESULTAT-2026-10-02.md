# Correction prioritaire identité et fraîcheur — résultat

2 octobre 2026. Mandat : `docs/CLAUDE-CORRECTION-PORTEE-IDENTITE.md`. Revue
bloquante de `05a2100`. Périmètre : sonde/missions/runtime uniquement.
Cursor corrige le catalogue tarifs dans `src/server/ai` (non touché ici) ;
Antigravity travaille la qualité de preuve des tests (non touché ici).

## 1. Correction de portée identité — annulée, pas renommée

**Le bug exact** : `local-runtime-probe.ts` (lignes ~636-643 au moment de
la revue) hashait `orgId` et appelait ça `accountId`. `orgId` identifie
l'ORGANISATION du compte Claude, pas l'utilisateur spécifique connecté.
Deux utilisateurs différents dans la même organisation partagent le même
`orgId` — hasher cette valeur produit le même hash pour les deux,
conflatant deux identités différentes en une seule. Un hash ne change
jamais la portée de ce qu'il hache.

**Correction appliquée, pas un contournement** : conformément à l'instruction
explicite « ne remplace pas identité compte par organisation pour obtenir
vert », la dérivation a été **annulée**, pas renommée ni redéfinie :

- `src/server/agents/runtimes/local-runtime-probe.ts` —
  `classifyClaudeCodeProbe` ne lit plus jamais `orgId` pour en dériver
  `accountId`. Le champ `accountId` reste absent pour `claude-code-cli`
  dans toutes les circonstances aujourd'hui — même absence honnête que
  pour `codex-acp-cli`, pour la même raison de fond : aucun champ
  officiellement documenté, par UTILISATEUR (pas par organisation,
  pas un booléen `loggedIn`, pas un jeton), n'existe dans la sortie de
  `claude auth status --json`. La fonction `hashAccountIdentity` et
  l'import `node:crypto` associés, devenus sans appelant légitime, ont été
  supprimés plutôt que laissés en infrastructure spéculative non utilisée.
- `src/server/agents/models/runner-executor-connection-probe.ts` —
  aucune logique changée (le pont transmettait déjà `accountId` tel quel,
  quel qu'il soit) ; doctrine d'en-tête et commentaires corrigés pour ne
  plus affirmer que Claude attache une identité aujourd'hui.
- `model-emission-launch-gate.ts` — toujours aucun changement nécessaire :
  son contrat (refus explicite `account_identity_unverifiable` sur absence,
  jamais de repli vers profil/organisation/provider) était déjà correct ;
  il retombe maintenant simplement sur le même refus honnête pour les deux
  fournisseurs, comme avant la dérivation erronée.

**Champ email examiné et explicitement écarté** : la seule donnée
réellement par-utilisateur dans cette sortie JSON est `email` — jamais lue
pour cet usage, pas seulement parce que c'est un identifiant personnel brut,
mais aussi parce qu'un hash d'email n'est PAS de façon fiable à sens
unique : un email est un identifiant à faible entropie, contrairement à un
UUID, et peut être retrouvé par dictionnaire/table arc-en-ciel à partir de
son hash. Ce serait substituer un problème de portée par un problème
cryptographique, pas une correction.

### Tests obligatoires — exécutés aux deux niveaux demandés

Aucune fixture ne traite `orgId` seul comme preuve suffisante — exigence
explicite du mandat, vérifiée ligne par ligne dans les tests ci-dessous.

**`local-runtime-probe.test.mjs` (22/22)** :
- « CORRECTION... orgId... jamais attesté comme accountId » — remplace
  l'ancien test qui affirmait le contraire.
- **Deux utilisateurs, même organisation** : deux réponses JSON avec le
  même `orgId` mais des `email` différents (Alice, Bob) — ni l'une ni
  l'autre n'attache `accountId` ; rien à conflater.
- **Changement d'utilisateur sous le même profil/organisation** : deux
  lectures successives, même `orgId`, utilisateur différent — les deux
  restent `"ready"` (connexion) mais sans `accountId`, donc rien qu'un
  appelant pourrait confondre avec « même compte qu'avant ».
- Absence sur `orgId` manquant/vide/non-JSON/non connecté ; effacement sur
  déclassification (fixture forgée).

**`runner-executor-connection-probe.test.mjs` (18/18)** :
- Test corrigé : connexion avec un `orgId` réaliste n'attache plus
  `accountId` (l'ancienne assertion affirmait le contraire — bug
  reproduit puis corrigé au même endroit que la revue l'a trouvé).
- **Deux utilisateurs, même organisation**, au niveau du pont de connexion
  cette fois (même `orgId`/`orgName`, `email` différent) : les deux se
  connectent, aucun des deux n'attache `accountId`.

**`model-emission-launch-gate.test.mjs` (41/41)** :
- « FIXTURE PROOF... CORRECTED » : la chaîne réelle de production
  (sonde → classificateur → gate → commit), nourrie d'une réponse SSH
  fixture entièrement réaliste avec `orgId`, refuse maintenant
  explicitement (`account_identity_unverifiable`) au lieu d'autoriser —
  c'est la preuve directe, de bout en bout, que la correction tient.
- **FIXTURE PROOF : deux utilisateurs, même organisation**, de bout en
  bout cette fois : ni Alice ni Bob n'est autorisé via l'identité
  d'organisation partagée.
- Les tests `attestedAccountStillMatches` (changement de compte,
  révocation, concurrence) restent inchangés et verts : ils testent la
  logique de RE-VÉRIFICATION du gate avec une identité DÉJÀ fournie —
  logique correcte et indépendante de la question « d'où vient cette
  identité », qui est ce que cette correction répare.

`npx tsc --noEmit` sur tout le dépôt : **0 erreur**, avant et après cette
correction (narrowing Cursor toujours corrigé par Codex, confirmé stable).
Combiné (`missions/*` + `ai/*` + `agents/models/*` + `agents/runtimes/*` +
`openhands-launch-contract`) : **zéro échec** hors des deux lacunes
intentionnelles déjà trackées (`*-gap.test.mjs`), non liées à ce mandat.

## 2. Fraîcheur — inférence retirée, pas remplacée par une autre

L'affirmation précédente (« ~1,95 s cohérent avec un aller-retour réseau »)
est **retirée**, pas affaiblie ni reformulée en une autre inférence : une
durée d'exécution ne prouve ni qu'une requête serveur a eu lieu, ni la
fraîcheur de quoi que ce soit. Détail et texte exact retiré :
`docs/CLAUDE-QUALIFICATION-COMPTE-REEL-RESULTAT-2026-10-02.md` (section
Fraîcheur, édité en place avec historique visible dans ce dépôt).

Ce qui reste, honnêtement : l'observation elle-même est horodatée
(2 octobre 2026, cette machine, `claude auth status --json` ≈ 1,95 s) sans
aucune conclusion de fraîcheur serveur tirée de cette mesure. Cette session
ne sait pas, et ne prétend pas savoir, si cette commande consulte un cache
local ou revérifie le serveur à chaque appel — documenté comme inconnu,
jamais reclassé « frais » par horodatage.

Le contrôle de péremption réel reste au même niveau que documenté au lot
précédent et inchangé par cette correction : `model-emission-gate.test.mjs`,
« a stale INDIVIDUAL provider entry is blocked... », la seule couche où une
donnée de capacité indépendante du `now()` du gate appelant peut
effectivement être représentée comme périmée et testée comme telle.

## 3. Contexte opérationnel — inventaire avant conclusion

**Correction du constat antérieur** : plusieurs documents de ce fil
(dont `CLAUDE-QUALIFICATION-COMPTE-REEL-RESULTAT-2026-10-02.md`) affirmaient
« aucun hôte runner réel n'existe » / « aucun hôte runner n'est déployé ».
C'était une généralisation excessive, corrigée ici après inventaire
read-only (aucun login, démarrage, déploiement ni appel modèle) :

```
docker images   → ghcr.io/openhands/agent-canvas:1.0.0-rc.11 présent (5.98 GB, créée 2026-06-12)
docker ps -a     → openhands-agent-canvas          Exited (255) il y a 2 mois
                   openhands-agent-canvas-old       Exited (137) il y a 2 mois
                   openhands-agent-canvas-backup    Exited (137) il y a 2 mois
docker inspect openhands-agent-canvas →
  StartedAt  2026-07-09T20:46:46Z
  FinishedAt 2026-07-30T23:44:48Z   (a réellement tourné ~3 semaines)
  Mounts (réels, confirmés, contenu jamais lu) :
    C:\Users\micha\.openhands                        -> /home/openhands/.openhands
    C:\Users\micha\Dev\openhands-projects             -> /projects
    C:\Users\micha\Dev\openhands-credentials\claude   -> /home/openhands/.claude
    C:\Users\micha\Dev\openhands-credentials\codex    -> /home/openhands/.codex
    C:\Users\micha\Dev\openhands-credentials\gcloud-adc -> /home/openhands/.config/gcloud
    C:\Users\micha\Dev\openhands-credentials\gemini   -> /home/openhands/.gemini
  Port bindings: 127.0.0.1:8000->8000/tcp
```

**Distinction correcte, maintenue** : ceci est une installation Docker
**ancienne, arrêtée, non qualifiée** pour ce gate — pas un « runner
QUALIFIÉ et approuvé » au sens où `model-emission-launch-gate.ts` l'exige
(policy vérifiée, compte attesté, approbation liée). L'énoncé juste n'est
pas « aucun runner n'existe », mais : *une installation non qualifiée
existe ; aucun runner qualifié n'est câblé à ce gate aujourd'hui.* Les deux
affirmations précédentes qui disaient le premier ont été corrigées dans
leurs documents respectifs.

**Cible concrète de qualification et blocage exact** : pour vérifier si les
credentials déjà montés dans `openhands-agent-canvas` produiraient une
preuve d'identité différente de celle testée sur cette machine, il
faudrait exécuter `claude auth status --json`/`codex doctor --json`
**à l'intérieur** de ce conteneur (le redémarrer, ou en lancer un nouveau
avec les mêmes montages en lecture). **C'est précisément l'action
suivante, et son blocage exact est aussi précis : démarrer un conteneur est
explicitement hors du périmètre « lecture seule » de ce mandat** (« pas
login/démarrage/déploiement/modèle »). Cette action nécessite une
approbation écrite explicite et séparée de Michael avant exécution — non
donnée ici, non supposée. Rien d'autre ne bloque cette prochaine étape :
l'image existe, le conteneur existe, les montages existent, les commandes à
exécuter sont déjà les mêmes commandes déjà qualifiées en lecture seule sur
cette machine.

## Limites dites explicitement

1. Ni Claude ni Codex n'ont d'identité par-utilisateur officiellement
   documentée et stable aujourd'hui. Le gate refuse honnêtement pour les
   deux (`account_identity_unverifiable`), aucune activation n'est
   possible sans une correction en amont (nouveau champ officiel côté
   Codex ; champ par-utilisateur encore à découvrir ou à faire exposer
   côté Claude si `email` reste exclu, ce qui est délibéré ici).
2. L'inventaire Docker ci-dessus est un CONSTAT, pas une qualification :
   le conteneur reste arrêté, ses credentials montés n'ont jamais été lus
   ni leur contenu inspecté par ce lot.
3. Aucune mesure de latence n'est présentée comme preuve de fraîcheur
   serveur dans ce document ou les précédents après cette correction.
4. Portée inchangée : aucun nouveau fournisseur, aucune nouvelle couche,
   aucun audit général entrepris.

## Prochaine action réalisable

Obtenir l'approbation écrite explicite de Michael pour démarrer
`openhands-agent-canvas` (ou un conteneur jetable équivalent avec les
mêmes montages en lecture) et y exécuter les deux mêmes commandes déjà
qualifiées ici (`claude auth status --json`, `codex doctor --json`),
toujours en ne rapportant que noms de champs/longueurs/motifs — jamais de
valeur brute — pour déterminer si l'environnement réellement monté change
la conclusion ci-dessus. Sans cette approbation, l'état reste : refus
honnête des deux fournisseurs, correctement câblé, rien de plus à faire
dans ce périmètre.
