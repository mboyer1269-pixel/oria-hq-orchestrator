# Reprise opérationnelle OpenHands — résultat

2 octobre 2026. Mandat : `docs/CLAUDE-REPRISE-OPENHANDS-OPERATIONNELLE.md`.
Périmètre : runner/runtime/qualification uniquement (`integrations/`,
Orchestrator) — pas `src/server/ai`, pas UI. Détail technique complet,
sonde exacte et recette : `integrations/openhands-claude-runtime/RESULTS.md`
(section « Reprise opérationnelle », ajoutée à l'historique existant de ce
candidat). Ce document résume les quatre étapes du mandat et le constat
global.

## 1. Inventaire des conteneurs arrêtés — fait, sans afficher de secret

Trois conteneurs arrêtés (`openhands-agent-canvas`, `-old`, `-backup`),
tous `ghcr.io/openhands/agent-canvas:1.0.0-rc.11`, inspectés via
`docker inspect` (métadonnées seules). Montages identiques sur les trois :
`~/.openhands` (état session/automation), `openhands-projects`,
`openhands-credentials/{claude,codex,gcloud-adc,gemini}`. Entrypoint réel
extrait SANS exécution (`docker create`+`docker cp`+`docker rm`, jamais
démarré) : démarre sans condition un agent-server, un serveur d'automation
(base SQLite persistante) et un frontend. **Risque identifié avant tout
démarrage** : si l'état `~/.openhands` est monté et que ces services
démarrent, le serveur d'automation peut reprendre un travail planifié de
façon autonome, sans intervention de l'opérateur.

## 2. Sonde isolée et temporaire — exécutée, nettoyée

Conteneur `--rm`, entrypoint entièrement remplacé (jamais le vrai
`tini -- entrypoint.sh`), seul montage réel : `openhands-credentials/claude`
en **lecture seule**. Mitigation du risque du point 1 : `.openhands`,
`openhands-projects` et le socket Docker ne sont jamais montés — aucun des
trois services ne démarre, donc aucune reprise n'est possible par
construction. Aucun modèle, aucune API facturée, aucune production/VPS
touchée. Preuve de nettoyage : conteneur supprimé après l'unique exécution,
aucune image/volume résiduel (vérifié par `docker images`/`docker ps -a`
filtrés sur le label de cette sonde).

## 3. Identité réellement disponible — reconnaissance locale, sans confondre loggedIn et autorisation

**Correction (`docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`)** : ce conteneur
tournait en réseau `bridge` (atteignable), mais aucune preuve n'a été
recueillie qu'un appel réseau réel de validation a eu lieu (ni capture, ni
log réseau conservé) — ne pas lire ce qui suit comme une validation
distante confirmée.

`claude-agent-acp --cli auth status --json` (commande officielle déjà
installée dans l'image) : `loggedIn=true`, `authMethod="claude.ai"`
(abonnement), `apiProvider="firstParty"`, `subscriptionType="pro"` —
**session d'abonnement reconnue localement**, jamais confondue avec une
autorisation HQ ni une identité de compte (email/orgId/orgName absents de
toute façon ; conforme à la correction du lot précédent, aucune identité
par-utilisateur fabriquée). Codex : aucune sous-commande
login/doctor/auth n'existe dans le binaire `codex-acp` de cette image —
constaté via `--help`, rien tenté. Aucun login interactif n'a été
nécessaire : la session existait déjà.

## 4. Comparaison et recette — livrées, rien exécuté

Delta minimal et recette de qualification complets dans
`integrations/openhands-claude-runtime/RESULTS.md`. Résumé : l'image
ancienne a une session Claude abonnement fonctionnelle mais un adaptateur/
CLI plus anciens (0.30.0/2.1.114) que ce candidat (0.84.0/2.1.284) ;
compatibilité des jetons OAuth entre versions plausible mais **non
vérifiée pour ce candidat**. Aucune vraie mission modèle lancée ; aucun
contrôle HQ désactivé ou remplacé.

## Anomalie d'environnement observée (hors mandat)

Après ces commandes, trois conteneurs aux noms Docker auto-générés
existaient, réutilisant cette même image avec des volumes anonymes (jamais
mes montages) et des commandes `git --version`/`python3 --version` —
signature d'un mécanisme de vérification interne de l'environnement
d'exécution, pas de ce lot. Non touchés (hors périmètre et compréhension
de cet outillage) ; signalé pour transparence, pas pour action.

## Fichiers modifiés / ajoutés (Orchestrator, ce worktree)

```
M integrations/openhands-claude-runtime/RESULTS.md
? integrations/openhands-claude-runtime/qualify_existing_image_account.sh
? integrations/openhands-claude-runtime/qualify_existing_image_account_probe.sh
```

Aucun fichier Oria.HQ touché par ce lot (périmètre runner/runtime/
qualification uniquement, confirmé). Aucun test automatisé nouveau — ce
lot est une sonde opérationnelle documentée et reproductible, pas un
changement de logique de gate ; `integrations/openhands-runner/` (Python,
provider_policy.py) et les tests HQ des lots précédents restent inchangés
et verts.

## Prochaine action concrète unique

Construire réellement ce candidat (`integrations/openhands-claude-runtime/`)
sur cette machine ou retrouver le manifest déjà construit sur VPS, puis
monter `openhands-credentials/claude` en lecture seule dans l'image
construite et rejouer exactement la même sonde `--cli auth status --json`
pour vérifier la compatibilité de la session existante avec l'adaptateur/
CLI plus récents — avant toute mission réelle, toujours sans engager de
budget ni d'approbation.
