# Pilote HQ / Memex — deuxième lot

## Mise à jour : accès opérateur

Correction origine auth : le code upstream réécrit l'URL loopback avec le port interne 3100. Ajout de `BETTER_AUTH_TRUSTED_ORIGINS=http://localhost:3310` dans Compose. Test réel avec connexion synthétique inexistante : origine du tunnel acceptée puis identifiants refusés HTTP 401 ; origine étrangère refusée HTTP 403 INVALID_ORIGIN. Aucun compte de test créé. `onboard --yes` non exécuté : ce parcours quickstart n'est pas nécessaire pour la création du propriétaire de l'instance existante.

Le lancement direct de SSH dans une session gérée a réussi après la demande de poursuite de l'utilisateur. Santé HTTP 200 depuis Windows et formulaire de création de compte vérifié dans le navigateur Codex à `http://localhost:3310`. Aucun port VPS publié. Le tunnel dépend de cette session locale, pas d'un service persistant. Inscription temporairement autorisée sur ce pilote privé pour la création du propriétaire ; sa fermeture est à effectuer dès confirmation. L'utilisateur doit saisir son nouveau mot de passe lui-même conformément aux règles de l'outil navigateur. Aucun mot de passe propriétaire collecté par l'agent. Ce résultat remplace la limitation de tunnel mentionnée dans le compte rendu initial ci-dessous.

## Équipe et livraisons

Trois spécialistes ont travaillé dans des périmètres séparés, avec revue et intégration par l'agent principal. Les changements restent locaux, sans commit ni push.

- **Memex** : une publication incomplète reste invisible aux lectures ordinaires ; ouverture après succès du vault, reprise et correction SUPERSEDES testées. Les anciennes entités réutilisées restent visibles. 212 tests passent sous Windows et dans un conteneur Linux isolé sur le VPS ; quatre tests adversariaux supplémentaires passent sous Windows. Preuve Linux : `.validation/memex-20260929-151800/result.json` et journal associé.
- **HQ** : route de lecture Paperclip authentifiée, désactivée par défaut, rattachement workspace/company imposé côté serveur, délais et volume bornés. 49 tests ciblés/configuration, typecheck, lint, build et smoke booking réussis par le spécialiste ; cinq tests du nouveau raccord rejoués par l'agent principal. Cinq avertissements lint préexistants. Pas de flux réel ni de dispatch revendiqué.
- **VPS** : Paperclip officiel par digest, attestation GitHub validée et commit concordant ; PostgreSQL 17 dédié. Deux services démarrés, données séparées, processus nonroot, ressources bornées, aucun port publié, réseau Docker interne. Aucun service existant reconfiguré et aucun fournisseur appelé.

## Vérifications runtime

L'interface et la santé répondent HTTP 200 depuis le VPS via l'adresse privée du conteneur et le Host attendu. L'API companies sans session répond 403. Santé indique mode authenticated/private et bootstrap_pending. Application UID 1000, zéro redémarrage et aucun OOM lors du contrôle. Deux secrets dédiés générés uniquement sur cible, fichier mode 600 ; aucune valeur dans les rapports. Migrations initiales appliquées puis désactivées ; inscriptions fermées.

Docker n'a pas publié le port demandé sur ce réseau interne. Compose et la procédure ont été corrigés pour ne publier aucun port ; l'accès opérateur prévu utilise un tunnel SSH vers l'IP privée résolue à chaque ouverture. Le contrôle automatique a rejeté le lancement local du tunnel, sans raison détaillée. Aucun contournement tenté. Le navigateur opérateur n'est donc pas validé.

## Étapes restantes

1. Accès opérateur privé puis création du propriétaire Paperclip ; aucune inscription ouverte en attente.
2. Sauvegarde et restauration dans des volumes distincts avec vérification DB et clés/assets.
3. Société et mission synthétiques, jeton limité, rattachement HQ explicite, lecture réelle authentifiée.
4. Connexion interactive d'un fournisseur puis tâche bornée, preuve de résultat, arrêt/reprise/annulation avant ajout d'un autre exécutant.

Le pilote n'est pas une livraison publique. Memex runtime n'est pas déployé et AgentMemory local reste distinct. Claude, Codex, Cursor et Antigravity ne sont pas connectés à ce pilote. La suite verte ne garantit pas zéro défaut. La publication Memex n'est pas une transaction distribuée et les anciennes publications ne sont pas migrées automatiquement.
