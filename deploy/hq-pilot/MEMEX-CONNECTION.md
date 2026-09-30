# HQ → Memex : pilote privé qualifié

État vérifié le 29 septembre 2026. HQ v7 lit Memex via HTTPS sur un réseau Docker privé. Aucun port Memex/TLS n'est publié. Le navigateur passe par le serveur HQ authentifié ; il ne reçoit aucun handle.

## Déploiement

Toujours combiner `compose.json` et `memex.overlay.json` pour conserver cette connexion. Définir `MEMEX_TLS_CA_FILE=/opt/oria-memex-tls/certificates/ca.crt` et `MEMEX_HQ_HANDLE_DIRECTORY=/opt/oria-hq-pilot/memex-read`, puis utiliser `docker compose -f compose.json -f memex.overlay.json up -d --no-build hq` depuis `/opt/oria-hq-pilot`. Le fichier runtime.env reste exclusivement sur le VPS.

Le namespace est fixé côté serveur à `org:workspace:michael-hq`. Le handle est read_only, expire après une heure et se renouvelle via `oria-hq-memex-read.timer` toutes les vingt minutes. La rotation remplace atomiquement le fichier ; HQ le relit à chaque requête. Le timer est activé ; deux renouvellements ont réussi, et une lecture navigateur après rotation et redémarrage TLS a réussi sans redémarrer HQ.

Le certificat serveur expire après 90 jours. Son renouvellement reste une opération à mettre en place avant expiration ; ne pas prétendre à une exploitation autonome indéfinie. Ne jamais désactiver la validation TLS. La clé CA reste sur l'hôte et n'est pas montée dans HQ ou le proxy. Une rotation de CA impose de redémarrer HQ pour recharger sa confiance.

## Versions qualifiées

- HQ : sha256:179a6bfbee374da8449a6ede6684efbe24d50154a3db9f60435cdf6a01572039.
- Memex : sha256:5a396d872abad03b938855f43cdc848d351d983df1edb1b5027eaaad2074ed65.
- Relais TLS : sha256:7a81a565f75ee2758ffdf6b5c25f1d73fbbe222013cf48f13316986fbfee7ee1.
- Snapshot HQ : 833 fichiers, manifeste SHA256 369D348B94C98BD9A93E9542CC90DB61A0C91BEACAD24B572CCC00A2B8076FEE.

Ces trois services utilisent `restart: unless-stopped`. Leurs configurations précédentes restent sauvegardées sur le VPS. Les fichiers compose Memex/TLS du dépôt sont des recettes de construction ; les images distantes sont figées aux identifiants ci-dessus.

## Preuves et limites

HQ : 3904 tests passent, 2 ignorés, zéro échec ; typecheck, lint, build et smoke Joris passent. Memex : gate1 215 tests passent. TLS : 6 tests passent. Rotation : 3 tests passent. Build Linux et acceptation Memex passent. Sonde TLS réelle : canary positif, accès interprojets/écriture/tamper refusés, CA inconnue et SAN incorrect refusés. Supabase Auth et lectures de schéma missions/ledger : HTTP200.

Le navigateur propriétaire confirme une lecture réussie mais vide du namespace HQ. Ce résultat ne prouve pas la pertinence de recherche sur un corpus réel. Le panneau consulte au maximum 50 entrées et filtre cet échantillon ; il ne constitue pas une recherche exhaustive, vectorielle ou sémantique. Il ne déclenche aucune inférence.

Memex expose désormais `agentmemory_proposal_status`, reçu scoped minimal avec statut. Un identifiant absent ou étranger renvoie null. Le parcours complet de contribution/validation/publication dans HQ reste à réaliser. L'orchestration native Paperclip et les fournisseurs restent à qualifier séparément.

Petite incohérence rédactionnelle restante : l'avertissement de l'ancien corpus parle de « cette page » alors que le nouveau panneau vérifie désormais Memex. Le limiter au « corpus local historique » au prochain lot UI.
