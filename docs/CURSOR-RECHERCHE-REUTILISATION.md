# Contre-expertise de réutilisation — ORIA HQ

30 septembre 2026. Recherche documentaire seulement. Aucune dépendance ajoutée, aucun secret lu, aucun service activé, aucune modification d'interface ou de backend.

Le correctif snapshot reste dans sa pull request distincte, non fusionnée. Ce document ne rejoue pas ces tests.

## Architecture imposée

- Hermes est l'interlocuteur quotidien et l'orchestrateur.
- HQ reste l'autorité des missions et des permissions.
- OpenHands est l'exécutant logiciel.
- Memex local est une mémoire de développement, pas un runtime de production.

Cette répartition est une contrainte de décision, pas un constat que le binaire VPS ou un adaptateur l'implémente déjà.

## Critères de décision

1. Une option qui crée une seconde autorité de mission ou de permission à côté de HQ est rejetée.
2. Une licence qui interdit de présenter le logiciel comme visage ORIA est un rejet du visage, même si le logiciel reste utilisable sans retirer sa marque.
3. Un client qui renvoie tout l'historique à chaque tour coûte des tokens. Une session serveur ne le fait pas automatiquement disparaître : il faut le mode de continuation réellement utilisé.
4. Une version publiée ne prouve pas la version installée.
5. Le coût retenu est le plus bas qui respecte les quatre rôles : pas de second produit de chat, pas de nouvelle base, pas de nouveau port.
6. Aucune source consultée ne décrit une application mobile ORIA. Un bot de messagerie ou un navigateur sur un tunnel n'est pas cette application.

## Phase 1 — Faits du dépôt et hypothèses

### Faits vérifiés dans ce dépôt

- `README.md` attribue à HQ les missions et les états visibles, à l'OpenHands SDK l'exécution d'un dossier borné, à Memex le contexte projet, et à AgentMemory la mémoire locale de développement. Il dit aussi qu'une mission réelle authentifiée reste à prouver.
- `VPS-ETAT-VERIFIE.md` (29 septembre 2026, lecture seule) : Ubuntu 24.04, 4 vCPU, environ 16 Go RAM. Le service nommé Hermes est en version 0.15.2 sur Node 20.19.2, insuffisant pour lancer HQ qui demande Node 22. Claude dans ce Hermes : CLI installé, `loggedIn=false`. Codex absent du PATH inspecté. Open WebUI : conteneur sain, port hôte 3000, à ne pas réutiliser pour HQ. Traefik actif.
- Le même rapport distingue un essai Ollama `hermes3:8b` : un classement JSON synthétique, 27,62 s au total dont 0,90 s de génération, modèle déchargé. Ce n'est pas un benchmark de coding et ce n'est pas le service Node Hermes.
- `LIVRAISON-2026-09-29.md` reprend cette limite et renvoie à `DECISION-MOTEUR-EXECUTION.md`.
- `DECISION-MOTEUR-EXECUTION.md` est une revue de code Paperclip au commit `29c8fb0`, pas une exécution. HQ garde l'identité d'espace et les intentions. Paperclip possède issues et files. La clé d'idempotence de ce code est retenue sept jours. L'adaptateur Hermes de ce checkout ajoute `--yolo`. Node exigé `>=24.11`, distinct de Node 22. Les chemins cités (`packages/db/src/schema`, `server/src/services/issues.ts`, `packages/adapters/hermes/src/server/execute.ts`) sont dans ce checkout Paperclip, pas dans ce dépôt.
- `docs/OPENHANDS-QUALIFICATION-2026-09-30.md` et `integrations/openhands-qualification/RESULTS.md` : SDK 1.50.0, commit `dcf401af7a9a302ef92cb7d092e1df9bb659daa5`, exécuté dans un conteneur isolé. `packages-observed.txt` est un inventaire observé, pas un lock cryptographique. Le bridge ACP examiné choisit une option de permission ; le mode Claude par défaut est `bypassPermissions`. Aucune mission modèle.
- `integrations/openhands-qualification/README.md` : pas de reprise de session distante. L'arrêt brutal et la reprise fournisseur ne sont pas qualifiés par le scénario d'annulation synthétique.
- `integrations/openhands-runner/README.md` : le contrat SDK vérifié avant construction de l'agent est 1.50.0. `prepare_job.py` écrit `durableLaunchReserved: false` et `budgetsEnforced: false`.
- `deploy/hq-pilot/PROJECT-MEMORY-FOUNDATION.md` est une proposition Memex non approuvée et non publiée. Elle distingue AgentMemory local et la mémoire de projet Memex.

### Hypothèses non démontrées ici

- Le service VPS « Hermes 0.15.2 » n'est pas identifié comme le dépôt Nous `hermes-agent`. Les quinze derniers tags consultés sont datés (`v2026.9.24` à `v2026.7.20`) et ne contiennent pas `0.15.2`.
- Aucun adaptateur Hermes vers HQ n'est dans `integrations/`. Le contrat figé attendu (deux créations simultanées, même identité et payload différent, perte de réponse puis lookup, espace et acteur protégés, création distincte de l'exécution) n'est pas dans ce dépôt. Il n'est pas fabriqué ici.
- La doc amont Hermes lue le 30 septembre n'est pas prouvée identique au binaire 0.15.2, ni byte à byte au tag `v2026.9.24`.
- PyPI `openhands-sdk` 1.50.1 ne prouve pas le contenu du conteneur qualifié en 1.50.0.
- Le texte du `README` sur Memex comme contexte projet n'a pas été réécrit. La contrainte de ce mandat est plus étroite : Memex local ne devient pas un runtime de production.

## Phase 2 — Sources officielles

Consultation le 30 septembre 2026. Les pages de documentation en ligne ne portent pas un identifiant de commit. Les licences et notes de version ci-dessous viennent des tags ou de l'API GitHub/PyPI.

### Versions et licences

| Composant | Version consultée | Licence exacte lue |
|---|---|---|
| Nous `hermes-agent` | Tag `v2026.9.24`, publié 2026-09-24, notes « Hermes Agent v0.21.5 », commit `f97608f178d1ffeca59860195ab7da295f7c8e5f` | MIT, copyright 2025 Nous Research. API GitHub : SPDX `MIT`, fichier `LICENSE`, sha `75410e73319c72cd3e991a501c5455eb78f38375` |
| Open WebUI | Tag `v0.11.4`, publié 2026-09-21 | Fichier `LICENSE` du tag : « Open WebUI License », 2819 caractères. API GitHub : SPDX `NOASSERTION`, nom `Other`. Ce n'est pas la MIT |
| LibreChat | Dernier tag `v0.8.8-rc4`, publié 2026-09-23, `prerelease=true`. Tag `v0.8.7` publié 2026-06-24, également `prerelease=true` dans les 20 dernières releases API | MIT au tag `v0.8.7`, copyright 2026 LibreChat, fichier 1066 octets. API GitHub : SPDX `MIT` |
| OpenHands SDK | Qualifié ici : `v1.50.0`. Publié ensuite : `v1.50.1` le 2026-09-30T19:31:33Z. PyPI `openhands-sdk` 1.50.1, champ licence vide | MIT aux tags `v1.50.0` et `v1.50.1`, copyright 2026 OpenHands contributors. API GitHub : SPDX `MIT` |
| OpenHands Agent Canvas | Release `v1.24.0`, publiée 2026-09-25. README de ce tag : « Agent Canvas », badge status beta, paquet npm `@openhands/agent-canvas` | MIT, copyright 2025 OpenHands contributors. API GitHub : SPDX `MIT` |

Liens : [Hermes v2026.9.24](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.24), [Open WebUI v0.11.4](https://github.com/open-webui/open-webui/releases/tag/v0.11.4), [LibreChat releases](https://github.com/LibreChat-AI/LibreChat/releases), [SDK v1.50.1](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.50.1), [SDK v1.50.0](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.50.0), [OpenHands v1.24.0](https://github.com/OpenHands/OpenHands/releases/tag/v1.24.0), [PyPI openhands-sdk](https://pypi.org/pypi/openhands-sdk/json).

### Hermes API

Source : site [API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), [Sessions](https://hermes-agent.nousresearch.com/docs/user-guide/sessions), [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp), [Open WebUI](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui), [messagerie](https://hermes-agent.nousresearch.com/docs/user-guide/messaging), index [llms.txt](https://hermes-agent.nousresearch.com/llms.txt). Le mot `mobile` n'apparaît pas dans cet index. Android est documenté comme [Termux](https://hermes-agent.nousresearch.com/docs/getting-started/termux). Desktop et Windows natif existent. Telegram, WhatsApp, Signal et d'autres passerelles sont des bots, pas une application ORIA.

- `POST /v1/chat/completions` est décrit comme stateless : la conversation complète est dans le tableau `messages`. L'objet `usage` rapporte `prompt_tokens`, `completion_tokens`, `total_tokens`.
- L'historique serveur est un autre chemin : `X-Hermes-Session-Id`, `POST /api/sessions/{id}/chat`, ou Runs qui chargent l'historique de session. Un Chat Completions sans cet en-tête, une chaîne Responses, ou un Run avec historique fourni par l'appelant n'utilisent pas la livraison détachée. Dériver un identifiant depuis le contenu ne suffit pas.
- La page Sessions dit que l'historique sert à reprendre, mais que Hermes ne renvoie pas chaque octet déjà traité. Chaque tour voit le prompt système choisi, la fenêtre courante, et le contenu injecté explicitement.
- Open WebUI, selon la page d'intégration Hermes, envoie quand même l'historique complet à chaque requête, y compris en mode Responses, au lieu de `previous_response_id`. Les outils s'exécutent sur l'hôte du serveur API. Un Hermes distant signifie des outils distants.
- Le chaînage `previous_response_id` stocke l'historique cumulé, sorties d'outils comprises. Ce n'est pas gratuit en tokens.
- Streaming SSE, keepalive toutes les 10 s sans événement, événement `hermes.tool.progress`. Écoute par défaut `http://127.0.0.1:8642`, modèle `hermes-agent`, `API_SERVER_ENABLED` et `API_SERVER_KEY`.
- Runs : en-tête `Idempotency-Key` (1 à 255 caractères ASCII visibles), réservé avant le travail. Retry identique : même `run_id`, HTTP 202, `Idempotency-Replayed: true`, y compris après redémarrage et après fin, échec ou annulation. Même clé et payload JSON différent : HTTP 409 `idempotency_key_conflict`. Clés isolées par profil API authentifié, retenues 24 heures après la dernière mise à jour de statut. Sans l'en-tête, chaque requête crée un run.
- La section CORS dit séparément que `Idempotency-Key` est un en-tête autorisé et que les réponses sont mises en cache 5 minutes par clé. Cette phrase n'est pas reconciliée ici avec la rétention de 24 heures des Runs. Les deux restent des phrases de la doc courante, pas un contrat HQ.
- `GET /v1/runs/{id}` sert à relire l'état sans garder le flux SSE. La reconnexion décrite pour le contrôleur navigateur exige le même principal, profil, session, `controller_id`, profil navigateur et transport. Un autre `controller_id` ne reprend pas le même contrôleur. Ce n'est pas une preuve de reconnexion du chat ORIA.
- Sessions SQLite `~/.hermes/state.db`. MCP stdio et HTTP sont documentés.
- Le gateway TUI documente qu'une reprise attache un abonné de plus sans couper les autres. Ce protocole n'est pas l'API HTTP utilisée par Open WebUI.

### Open WebUI

La clause 3 interdit d'utiliser le nom du titulaire pour promouvoir un produit dérivé sans permission écrite. La clause 4 interdit de modifier, retirer, masquer ou remplacer la marque Open WebUI, y compris le nom, le logo et les identifiants visuels, sauf si (i) le nombre d'utilisateurs finaux ne dépasse pas 50 sur 30 jours glissants, (ii) une permission écrite préalable, ou (iii) une licence entreprise. `LICENSE_HISTORY` et le CLA sont mentionnés. Texte lu au tag `v0.11.4`.

Conséquence : Open WebUI peut rester un conteneur déjà présent si la marque reste visible et si l'exception des 50 utilisateurs s'applique. Il ne peut pas devenir le visage rebrandé ORIA sans permission ou licence entreprise.

### LibreChat

Sources : [MCP](https://www.librechat.ai/docs/features/mcp), fichiers `main` du dépôt de doc `LibreChat-AI/librechat.ai` (`mcp.mdx`, `resumable_streams.mdx`, `memory.mdx`, `local/docker.mdx`). Ce `main` n'est pas épinglé au tag applicatif `v0.8.7`.

- MCP : STDIO, SSE (déconseillé en production dans cette page), Streamable HTTP recommandé pour le multi-utilisateur. Message STDIO limité à 10 Mo par le SDK embarqué.
- Streams résumables : reprise après coupure, synchro d'onglets, poursuite sur un autre appareil. Mode une instance : état en mémoire. Mode plusieurs instances : Redis. Ce n'est pas une clé d'idempotence de création de mission HQ.
- Mémoire utilisateur : paires clé/valeur, désactivée tant que `librechat.yaml` ne l'active pas. Ce n'est pas l'historique de conversation, et ce n'est pas Memex.
- Installation Docker Compose documentée avec MongoDB. L'interface locale citée est `http://localhost:3080`.
- Aucune page consultée ne décrit une application mobile native. La reprise de stream mentionne un téléphone comme second client du même chat web.
- Les 20 dernières releases GitHub, y compris `v0.8.7`, sont marquées `prerelease=true`. On ne les traite pas comme une version stable prouvée.

### OpenHands SDK et Agent Canvas

Sources SDK : [persistance](https://docs.openhands.dev/sdk/guides/convo-persistence.md), [streaming](https://docs.openhands.dev/sdk/guides/llm-streaming.md), [MCP](https://docs.openhands.dev/sdk/guides/mcp.md). Sources Canvas : [vue d'ensemble](https://docs.openhands.dev/openhands/usage/agent-canvas/overview.md), [architecture](https://docs.openhands.dev/openhands/usage/agent-canvas/architecture.md), [conversations](https://docs.openhands.dev/openhands/usage/agent-canvas/conversations.md), [réglages](https://docs.openhands.dev/openhands/usage/agent-canvas/customize-and-settings.md), [mobile](https://docs.openhands.dev/openhands/usage/agent-canvas/mobile-access.md), [ACP](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents.md).

- Le SDK persiste une conversation sur disque (`persistence_dir`, `conversation_id`) et peut la rouvrir. La doc décrit l'état agent, les outils et les serveurs MCP. Elle ne décrit pas une clé d'idempotence HQ.
- Le streaming SDK est un callback de tokens (`stream=True`). Ce n'est pas le SSE Hermes.
- MCP SDK : serveurs locaux et URL OAuth. Le flux OAuth navigateur n'est pas adapté à un worker sans opérateur, sauf jeton statique fourni par le serveur MCP.
- Notes `v1.50.1` : timeout des flux async bloqués, restauration des outils lors d'un attachement distant, pont vers des backends applicatifs authentifiés, HTTP 429 si trop de conversations. Aucune de ces notes n'a été rejouée dans le conteneur 1.50.0.
- Agent Canvas est le client navigateur. L'architecture officielle le sépare de l'Agent Server (dépôt SDK) et d'un Automation Server distinct. Canvas présente l'état et envoie des requêtes. Il ne remplace pas HQ.
- Reconnexion documentée : une bulle « Failed to send » pendant une reconnexion, puis effacement si le serveur a bien reçu le message. Le compteur de contexte et le compactage manuel existent. Brancher une conversation est limité aux backends locaux qui supportent les forks.
- Mobile : Tailscale vers `http://<ip>:8000/`, ou ngrok avec `agent-canvas --public` et une clé. Ce n'est pas une application ORIA, et l'exposition publique sans clé est refusée par la doc elle-même.
- Les réglages, skills et serveurs MCP sont par backend. Les activer dans Canvas ne les active pas dans le runner HQ.

## Phase 3 — Quatre options

### 1. Garder la répartition et ne réutiliser que le SDK déjà qualifié

Recommandation : garder.

HQ reste l'autorité. Le runner `integrations/openhands-runner` reste l'exécutant, épinglé à la preuve 1.50.0 jusqu'à une relecture du conteneur. Hermes n'est branché comme interlocuteur qu'après avoir identifié le binaire VPS. Open WebUI, LibreChat et Agent Canvas ne deviennent ni le visage ni un second orchestrateur. Memex local et AgentMemory ne sont pas promus en runtime de production.

Coût : nul en nouveau service. Le coût réel est une lecture de version, pas une installation.

Limite : tant que le binaire 0.15.2 n'est pas rattaché à Nous `hermes-agent`, la doc 0.21.5 n'autorise aucun code d'adaptateur.

### 2. Réutiliser Open WebUI tel quel, marque conservée

Recommandation : rejeter comme visage ORIA. Ne pas étendre le conteneur existant.

Le port 3000 est déjà pris (`VPS-ETAT-VERIFIE.md`). La page Hermes dit qu'Open WebUI renvoie l'historique complet. Les outils tourneraient sur l'hôte Hermes, pas dans le dossier HQ. Retirer la marque au-delà de l'exception des 50 utilisateurs, ou sans écrit, rompt la licence `v0.11.4`.

Coût si on le gardait comme console d'admin : suivre les releases Open WebUI et la compatibilité de l'API Hermes, plus le risque de marque. Ce coût n'achète pas les vues Discuter et Atelier.

### 3. Adopter LibreChat comme visage

Recommandation : rejeter.

LibreChat est MIT et sait reprendre un flux, parler MCP et mémoriser des paires clé/valeur. En faire le visage ajoute MongoDB, une mémoire parallèle, et un produit dont les releases récentes sont marquées prerelease. Rien de consulté n'en fait l'autorité des missions HQ. Deux historiques de conversation apparaîtraient.

Coût : une pile de plus à qualifier, mettre à jour et sécuriser, sans retirer le travail déjà fait dans le runner OpenHands.

### 4. Adopter Agent Canvas comme atelier

Recommandation : rejeter l'application. Garder le SDK.

Canvas v1.24.0 est un centre de contrôle beta : conversations, automations, backends, secrets. L'adopter créerait une seconde identité de travail à côté du dossier HQ. Le mobile documenté est un navigateur sur Tailscale ou ngrok. Le SDK 1.50.0 déjà qualifié reste le seul exécutant à réutiliser, sans installer 1.50.1 dans ce lot.

Coût de Canvas en plus de HQ : deux interfaces, un Automation Server, et des réglages qui ne sont pas la politique de permission HQ. Le bridge qualifié approuve encore tout seul.

## Recommandation

Garder l'option 1.

Réutiliser le SDK OpenHands déjà qualifié dans `integrations/openhands-runner` et `integrations/openhands-qualification`. Ne pas le mettre à jour vers 1.50.1 tant que le conteneur n'a pas été relu et les permissions requalifiées.

Réutiliser Hermes seulement comme interlocuteur devant HQ, et seulement après preuve que le service 0.15.2 est Nous `hermes-agent` à une version dont l'API a été lue. Le client devra alors continuer une session serveur (`X-Hermes-Session-Id` ou `/api/sessions/{id}/chat`), pas renvoyer le tableau `messages` complet à la façon d'Open WebUI. L'idempotence des Runs (24 heures, 409 si le payload change) ne remplace pas le contrat HQ manquant. Ne pas activer `API_SERVER_ENABLED` dans ce lot.

Rejeter Open WebUI comme coquille ORIA, LibreChat comme second chat, et Agent Canvas comme second atelier. Paperclip reste le témoin déjà décrit, avec `--yolo` et une idempotence de sept jours : ne pas l'empiler.

## Actions concrètes

1. Lire, sans l'activer, l'identité du processus VPS qui annonce Hermes 0.15.2 : binaire, dépôt, version Node. La consigner à côté de `VPS-ETAT-VERIFIE.md`. Si ce n'est pas Nous `hermes-agent`, ignorer la doc 0.21.5 pour ce service.
2. Dans le conteneur de qualification, relire la version importée d'`openhands-sdk` et la comparer à `integrations/openhands-qualification/RESULTS.md`. Ne pas traiter PyPI 1.50.1 comme cette version.
3. Ne pas donner le port 3000 à HQ. Ne pas retirer la marque Open WebUI.
4. Ne pas coder un second adaptateur Hermes. Le contrat figé reste la dépendance : deux créations simultanées, même identité avec payload différent, réponse perdue puis lookup, configuration protégée de l'espace et de l'acteur, création distincte de l'exécution.
5. Ne pas interpréter `prepare_job.py` (`durableLaunchReserved` et `budgetsEnforced` à false) comme une réservation durable déjà tenue.
6. Plus tard, hors de ce fichier, aligner la phrase Memex du `README.md` avec la contrainte de runtime. `deploy/hq-pilot/PROJECT-MEMORY-FOUNDATION.md` n'est toujours pas une publication.

## Hypothèse qui invaliderait la recommandation

Si le service VPS 0.15.2 est bien Nous `hermes-agent` et si une lecture de son code montre qu'il n'a ni `X-Hermes-Session-Id` ni `Idempotency-Key`, alors la doc du 30 septembre ne s'applique pas et l'option « interlocuteur Hermes » doit attendre une version qualifiée, pas un branchement sur la doc courante.

Si le conteneur qualifié contient déjà le SDK 1.50.1, `RESULTS.md` est en retard. Cela ne renverse pas le rejet de Canvas. Cela renverse seulement la phrase « rester sur 1.50.0 » et exige de réécrire la preuve, pas d'installer à l'aveugle.

Si un usage futur d'Open WebUI reste sous le seuil de 50 utilisateurs, marque intacte, comme console d'administration séparée d'ORIA, le rejet vise le visage produit, pas l'existence du conteneur déjà sain.

## Limites de cette recherche

- Le site Hermes et `docs.openhands.dev` ont été lus en ligne le 30 septembre 2026, sans commit de doc épinglé.
- La doc LibreChat vient du dépôt `librechat.ai` branche `main`, pas du tag `v0.8.7`.
- Aucun binaire VPS n'a été relu dans cette session. L'inventaire du 29 septembre n'a pas été refait.
- Les tests snapshot déjà acquis n'ont pas été rejoués.
- Aucune page consultée ne prouve la reconnexion d'une mission HQ ni l'idempotence d'une création de mission ORIA.
