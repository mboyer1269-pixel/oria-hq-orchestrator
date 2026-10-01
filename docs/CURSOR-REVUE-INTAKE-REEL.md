# Revue — preuve PostgreSQL d'admission, 1 octobre 2026

Lecture seule du candidat `mboyer1269-pixel/Oria.HQ.Michael.HQ-APP`, branche `codex/hq-delivery-integration`, tête `b0752d3c9ce7a4d37c1b333118cf6671c7b4194d`, et de `docs/evidence/2026-10-01-intake-real-db.txt` sur `codex/cursor-recovery-handoff` à `7e13e70`. Le lot routage n'est pas repris. Aucun Docker, aucun test produit, aucun appel modèle.

## Verdict

Le run `1790836047_67270`, code 0, tient pour ce qu'il mesure : le CLI `src/scripts/development-mission.mjs` appelle `createDevelopmentService`, PostgreSQL `16.4-alpine` et PostgREST `v12.2.0` reçoivent vraiment les écritures, et le journal publié correspond au script du candidat.

Aucun des quatre constats n'invalide ce run. La concurrence divergente (un `saved`, un `conflict`), la déduplication du payload identique, la réponse client perdue après un 201 déjà reçu par le proxy, et la relecture après `docker stop` / `docker start` sont cohérentes avec le code et avec le journal. Cela ne qualifie pas l'authentification propriétaire, les politiques RLS, le formulaire, Hermes, ni un modèle.

Contrôles de cette lecture, sans relancer le banc :

- Hors `docs/` et `proofs/`, `2f08e96` et `b0752d3` n'ont aucun diff. Le correctif de banc est `ad549d7` ; `b0752d3` n'ajoute que la note d'intégration.
- Empreinte du script `proofs/run-intake-real-db.sh` : `7bb134906e1532630b3f1b59f6e4dff92e7c69fe4f2bd09f4506dfeac1c12f6a`.
- Empreinte du journal : `b1c5bc3a24bba43b0285c1b141510daddc6b6908e54584571f28521c2186238a`.
- Les deux empreintes sont celles citées dans `docs/HQ-INTEGRATION-2026-10-01.md` du candidat. Les condensats d'images cités là ne sont pas revus ici : ce poste n'a pas interrogé Docker.

## Constats

1. **N'invalide pas. Preuve 3 n'est pas une preuve RLS.** `db/migrations/0001_missions.sql:26` active RLS sans politique. Les politiques restrictives sont dans `db/migrations/0005_missions_rls.sql`, que le banc n'applique pas : `proofs/run-intake-real-db.sh:86-92` ne charge que `0001`, puis crée `qualification_service` `NOLOGIN BYPASSRLS`. PostgREST utilise ce rôle (`:100`). Le proxy retire `authorization` et `apikey` avant l'envoi (`proofs/prove-cli-real-db.mjs:88-89`). Le refus du workspace falsifié est le contrôle du CLI (`src/scripts/development-mission.mjs:76-78`) ; le `not_found` de l'autre workspace suit l'identifiant dérivé du workspace, pas une politique. Le journal peut se lire « étanchéité garantie » ; la phrase juste est : filtre applicatif sur rôle qui contourne RLS. Reproduction statique : le script n'a pas d'autre fichier de migration.

2. **N'invalide pas ce run. L'assertion shell du titre exact n'est pas celle qui a tranché.** `proofs/prove-cli-real-db.mjs:242-251` compare le gagnant enregistré (id, titre, objectif, périmètre, critères, hash) puis `:285-290` efface `WINNER_STATE_FILE`. Le shell ne s'exécute qu'après ce processus (`proofs/run-intake-real-db.sh:194`). Le fichier est donc absent, et `:218-223` accepte l'un ou l'autre des deux titres concurrents, y compris celui du perdant. La ligne `:226` dit « contenu exact du gagnant ». Le journal montre pourtant la ligne de succès Node, imprimée seulement après les asserts `:242-251`, puis le code 0. Le verdict exact est celui du script Node. Le repli shell ne le renforce pas. Les champs hors de ces asserts (horodatages, `expected_output`) ne sont pas comparés un à un.

3. **N'invalide pas. La coupure est locale au proxy, après le corps HTTP.** `proofs/prove-cli-real-db.mjs:101-109` lit toute la réponse PostgREST, puis détruit le socket client si le statut est 201 ou 200. Ce n'est pas une panne entre PostgREST et PostgreSQL, ni une coupure au milieu de la transaction. Le service transforme l'échec de lecture en `outcome_unknown` (`src/server/missions/development-mission.ts:42`). Le journal et le SQL du banc exigent ensuite une seule ligne pour `33333333-3333-4333-8333-333333333333` (`run-intake-real-db.sh:152-156`). L'assertion « réponse perdue après commit, sans doublon » tient pour ce mécanisme. Elle ne tient pas pour un crash du moteur pendant l'écriture.

4. **N'invalide pas ce run. Un appel Docker après redémarrage ne ferme pas stdin.** Le blocage initial `docker exec -i … psql -c` n'est plus dans le script qualifié : les `psql -c` n'ont pas `-i` et redirigent `< /dev/null`, avec `timeout -k 2`. Après redémarrage, `proofs/run-intake-real-db.sh:184` lance `docker port` sans `< /dev/null`, contrairement à `:109`. `timeout -k 2 5` borne cet appel. Le journal va jusqu'au succès, donc cet appel n'a pas bloqué le run `1790836047_67270`. Résidu seulement.

Le `docker stop` / `docker start` conserve le volume nommé du run. C'est un redémarrage de conteneur, pas une coupure d'alimentation. Le document d'intégration le dit déjà.

## Prochaine intégration

Ne pas exposer le CLI à Hermes et ne pas lui inventer d'outil, de compte ou d'API. Aucun fichier `src/server/ventures` ni `src/server/orchestration` n'importe ce CLI. Le seul service déjà capable de relire une ligne écrite par ce banc est le dépôt existant `public.missions`.

Le raccord nécessaire, déjà dans le code, est la frontière propriétaire HTTP, pas le fichier `0600` du banc :

- `POST /api/missions/development` (`src/app/api/missions/development/route.ts`) authentifie `getCurrentAuthUser` / `isOwnerUser`, prend le workspace du contexte HQ, et appelle le même `createDevelopmentService`. Le flag `MISSION_DURABLE_DRAFTS` reste faux par défaut (`src/server/missions/mission-persistence-flag.ts:22-28`). Le run ne l'a allumé que dans le processus CLI.
- La suite d'exécution existante est `POST /api/orchestration/openhands`. Elle exige le même propriétaire, `ORIA_ENABLE_OPENHANDS_CONFIRMATION=1`, et charge la mission par `createOpenHandsReservationStore` sur `public.missions`. `buildOpenHandsSubmission` garde `executionRequested: false` et `commitVerification: "not_verified"`. L'admission CLI ne lance rien.

Tant que les capacités et le compte Hermes ne sont pas observés, on s'arrête à cette frontière. Le formulaire reste à Claude. La recette navigateur et le banc restent à Antigravity.
