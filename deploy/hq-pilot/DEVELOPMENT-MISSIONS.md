# Missions de développement durables — livraison v13

Le parcours `/hq/missions` permet désormais de créer un brouillon de développement avec objectif, périmètre et critères d'acceptation. Owner Supabase vérifié une fois ; contexte workspace/mode serveur ; origine publique exacte ; requête bornée. Aucun lancement automatique.

Le requestId est conservé avant envoi pour cette session et ce projet ; UUIDv5 de mission dérivé du workspace et requestId. Insertion durable sans écrasement, hash de l'intention et récupération GET scoped. Un résultat ambigu ne déclenche pas de nouveau POST automatique. Seul l'identifiant reste dans le navigateur. Le store durable préexistant utilise Supabase ; aucun fallback RAM dans ce parcours.

Validation : suite entière avant correction de libellé 3 932 réussis, 2 ignorés ; correction finale Kanban 2 tests de rendu supplémentaires réussis et TypeScript. Lint/build/smoke repassés après correction. Cinq avertissements lint préexistants, aucune erreur. Logs `.validation/hq-development-*` et `hq-mission-card-*`.

V13 exécutée : `sha256:039c64a460dc42ee35f1aba543a89b618e4512722f954ea064da1fe1f5f87c6d` ; snapshot source `/opt/oria-hq-pilot/source-v13`, 856 fichiers ; manifeste SHA256 `8FB449163F9F2A905F4E3EBEAC8047DA1B8EBD7E4F2FA0027BFE6102DB07672E`. `MISSION_DURABLE_DRAFTS=true`, autres capacités conservées. L'overlay Memex reste obligatoire. Le canal de revue opérateur reste désactivé : seul son code client est inclus.

Preuve réelle depuis session propriétaire : première mission créée dans HQ, retrouvée après reload et lookup du même reçu, un dossier unique non attribué. Après remplacement du conteneur par v13, ce dossier reste visible. Carte corrigée « Approbation requise » et « Non attribué », pas d'exécuteur simulé. Le transfert Paperclip est toujours explicitement désactivé. Test responsive largeur390 : document contentWidth=clientWidth=375, aucun débordement global ; viewport remis à sa valeur initiale.

Preuve visuelle `.validation/hq-first-development-mission.png`. Aucun appel fournisseur déclenché. Une création de brouillon ne prouve pas une exécution.

Retour arrière : fichiers VPS `compose.before-mission-card.json` (v12, brouillons actifs) et `compose.before-development.json` (v11). Préserver les lignes Supabase ; rollback du serveur n'annule pas une mission enregistrée.

## Copie de travail du futur exécutant

Snapshot v13 placé uniquement dans le volume Claude `/workspace/hq-pilot`, sans anciens fichiers de connexion, `.env`, historique Git ou volumes applicatifs. Nouveau dépôt local `codex/hq-self-development`, baseline opérateur `2cbea807174ab58de9b5811a6e92898e537e7427`. Statut Git propre après initialisation. Ce commit contient la copie de sources, pas l'historique original ni un changement produit par Claude.

Le runner existant est UID1000, root readonly, sans Docker socket et conserve son isolation. Après `docker cp`, les fichiers étaient root-owned. Le chown dans le runner a été refusé par ses capacités retirées ; correction via helper ponctuel sans réseau, root readonly, seulement CAP_CHOWN, montage du seul workspace, puis suppression automatique du helper. Aucune capacité ajoutée au runner vivant.

Node du runner est24.21.0, Claude2.1.283. Les validations HQ de référence restent Node22 ; ne pas annoncer une suite HQ qualifiée dans le runner avant adaptation du runtime de test. L'environnement SSH Paperclip doit pointer `/workspace/hq-pilot`. Aucun agent natif ni environnement enregistré par ce lot.

## Accès restant

`auth whoami` réel retourne401. Le CLI officiel via `/app/cli/node_modules/.bin/tsx src/index.ts` a ouvert une nouvelle demande Board ; autorisation utilisateur explicitement demandée, non reçue à la rédaction. Ne pas considérer un challenge ou un onglet comme une autorisation. Ne pas consigner le token de challenge. Une approbation Board donne plus que le seul projet ; révocation temporaire prévue après qualification. Pas de nouvelle tentative aveugle tant que le processus de demande précédent reste actif.
