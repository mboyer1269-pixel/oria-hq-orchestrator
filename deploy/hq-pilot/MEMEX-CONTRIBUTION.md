# Contribution Memex depuis HQ : pilote qualifié

État du 30 septembre 2026 UTC (29 septembre au Québec). Succède au raccordement de lecture documenté dans MEMEX-CONNECTION.md.

## Résultat vérifié

Une proposition de règle de fonctionnement a été soumise depuis le navigateur propriétaire de HQ. Elle reste au statut `proposed`, sans approbation ni publication. Son reçu a été retrouvé après redémarrage du conteneur Memex et renouvellement du handle de contribution. Une lecture SQL readonly du mapping confirme exactement une requête conservée. Le bouton Nouvelle proposition libère le formulaire en conservant l'historique du reçu.

Le premier POST avait été refusé derrière le tunnel : l'origine publique différait de celle reconstruite par le serveur Next. La correction déclare explicitement `ORIA_HQ_PUBLIC_ORIGIN=http://localhost:3321`. Les en-têtes Host/Forwarded ne servent pas d'autorité. Adapter cette origine explicitement lors d'un futur changement d'adresse ; une autre origine reste refusée. Le reçu absent a permis une reprise explicite avec le même requestId. Aucun renvoi automatique.

## Configuration en service

- HQ v11 : sha256:960d2e0d8cdff83f4036098f7586384812e0a9ca9d5cc1035d2aab378444a7bd.
- Snapshot HQ : 842 fichiers, manifeste SHA256 80CF1DFE66C0F82DDC3FEA235E0F80531D08C47FC4283A8ABF8F8A60A90E0424.
- Memex idempotence : sha256:d430e55784aef543f984d17529edd52cbdb004566d3d7b1fb068e073dc26feca.
- Snapshot Memex : 37 fichiers, manifeste SHA256 8F8E5D567D6139E2A37A206862BE7C285A1F346223D619C1891BB47D52BC6160.
- TLS inchangé : sha256:7a81a565f75ee2758ffdf6b5c25f1d73fbbe222013cf48f13316986fbfee7ee1.

`memex.overlay.json` active explicitement `ORIA_ENABLE_MEMEX_PROPOSALS=1` et monte le répertoire dédié en lecture seule. Le handle de contribution est séparé du handle de lecture ; sujet stable `hq-contributor`, namespace unique `org:workspace:michael-hq`, expiration1h. `oria-hq-memex-proposal.timer` renouvelle toutes les20min. La clé de signature ne quitte pas Memex. Le service HQ ne reçoit aucun droit d'approbation ou de publication via son transport, limité à submit/status. Le gateway reste signé uniquement ; les outils filesystem distants demeurent interdits.

Les fichiers compose locaux HQ reflètent le déploiement. Conserver les deux compose et les variables de chemins CA/handle décrites dans MEMEX-CONNECTION.md. Les backups distants compose.before-contribution.json et memex.overlay.before-contribution.json permettent de revenir à la lecture seule v7 ; le nouveau mapping SQLite est additif. Ne pas supprimer les volumes pour revenir en arrière.

## Validation

- HQ : typecheck, lint (0 erreur, 5 avertissements préexistants), build et smoke Joris passent ; suite3919pass/0fail/2skip.
- Memex : doctor, gate0, gate1 et agentpack ;215tests passent.
- Inter-dépôts réel : HTTP signé, receipt après réouverture SQLite, mêmeID au retry, conflit payload, isolation sujet/workspace passent sur bases temporaires.
- Rotation contribution :3tests passent ; renouvellement réel avant/après redémarrage réussi.
- Image Memex Linux : publication/retry/HTTP signé/isolation/readonly/expiry/tamper/rawvault acceptance passe en environnement jetable.
- Navigateur propriétaire : receipt reçu, même receipt après redémarrage/rotation, nouveau cycle disponible. Supabase Auth/missions/ledger HTTP200.

## Suite nécessaire

L'historique de reçus dans le navigateur est limité à20 et à la session. Memex conserve les propositions durablement mais HQ ne dispose pas encore de leur liste persistante complète ni de leur contenu de revue. Prochaine tranche : lecture de proposition scoped pour l'opérateur, approbation humaine attribuée au payload/version, journal durable, publication unique puis lecture du résultat. Ne pas donner ces pouvoirs aux exécutants ordinaires. La mission native Paperclip/fournisseurs reste aussi à qualifier. Le certificat TLS90jours doit encore recevoir sa procédure de renouvellement automatisée. L'objectif global reste incomplet.
