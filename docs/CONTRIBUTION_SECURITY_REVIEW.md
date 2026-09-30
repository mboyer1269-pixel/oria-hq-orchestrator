# Contribution durable — revue indépendante du 2026-09-29

Revue source uniquement, sans secrets, mutation de runtime ni déploiement. Les agents implémentent en parallèle ; les lignes ci-dessous repèrent le code inspecté, pas une version immuable. Ce document définit les invariants à vérifier, pas une déclaration de qualification du futur parcours.

## Constats vérifiés et frontière existante

- `C:/Users/micha/Documents/memex-core/src/db/intake.ts:38` contient une unicité historique `(namespace, content)`. `src/intake/index.ts` utilisait `INSERT OR IGNORE` puis recherchait par namespace/contenu : deux payloads ou auteurs différents pouvaient recevoir le même ID et un statut recalculé. Le nouveau wrapper requestId en cours doit soit isoler cette contrainte, soit refuser explicitement le doublon ; jamais l'interpréter comme succès idempotent sans vérifier l'identité et tout le payload.
- `src/mcp/unified-server.ts:85–94` contrôle accès et namespace authentifiés puis transmet `authenticatedSubject`. `src/mcp/tools.ts:186–187` impose ce sujet à proposedBy/sourceClient. Préserver ce chemin ; ne jamais utiliser le proposedBy ou workspace du navigateur comme autorité.
- Le lookup historique `src/mcp/tools.ts:58–71` filtre seulement proposalId et namespace. La récupération d'une contribution par requestId doit filtrer également le sujet authentifié, dans la requête SQL elle-même. Un ID absent et celui d'un autre sujet doivent produire le même résultat nul, sans exposer contenu ou métadonnées.
- `src/mcp/access.ts:26–34,64` distingue submit (read_write) et status (read_only). Un credential read_write autorise aussi des lectures : l'adaptateur contribution doit ajouter sa propre liste stricte submit/status. Le profil distant bloque déjà les outils raw vault dans `unified-server.ts:78–82`.
- `src/intake/publication.ts:179–201` n'admet que approved/publishing et gèle un journal de publication ; la barrière graph précède le statut promoted (`:237–245`). Submission réussie signifie seulement admission durable dans intake, jamais mémoire publiée. Une interruption peut laisser publishing ; ne pas convertir cet état en réussite finale ni échec destructif. La CAS SUPERSEDES dans `src/graph.ts:206–215` protège les corrections concurrentes, distinctement de l'idempotence de soumission.

## Contrat minimal

1. Clé stable et bornée `(authenticatedSubject, exact namespace, requestId)`. Réserver et insérer proposition/reçu dans une seule transaction SQLite. Même clé + même payload canonique → même proposition et statut actuel. Même clé + payload différent → conflit explicite, aucune nouvelle ligne ni écrasement.
2. Canonicaliser uniquement les champs acceptés et stables, avec sujet serveur imposé. JSON structures parsées, clés d'objets triées lexicalement sans dépendance locale ; ordre des tableaux préservé. Définir absence/null, valeurs finies et limites. Ni date générée, ni état de workflow dans la comparaison. Ne pas supprimer arbitrairement accents, espaces ou casse du contenu pour faire coïncider deux contributions.
3. RequestId est généré une fois pour une intention et conservé pendant timeout/retry. Si réponse perdue après commit, rechercher son statut puis rejouer au besoin le même payload avec le même ID. Une erreur réseau n'établit pas absence de commit. Une modification du brouillon après envoi ne doit pas silencieusement réutiliser l'ID.
4. Séparer credential, activation, binding et transport contribution du transport lecture. Namespace/tenant issus du workspace serveur ; sujet du handle. Rotation garde le même sujet logique pour retrouver les reçus. Pas de fallback lecture→écriture ou credential plus puissant. Jamais clé de signature dans HQ.
5. Lookup requestId n'est pas une API de listing. Réponse bornée aux identifiants, état, dates utiles ; pas de payload brut ni journal last_error. Pour le pilote mono-propriétaire, un sujet backend représente le service HQ, pas automatiquement l'identité individuelle Supabase : ne pas promettre une séparation entre utilisateurs avec ce seul sujet partagé.
6. Ni submit ni status ne donnent autorité d'approbation/publication. `status=verified`, `zone=human` ou provenance envoyés dans suggestedEntities ne prouvent pas une vérification humaine ; l'UI conserve le caractère proposé/advisory et distingue admission, validation et publication.

## Tests adversariaux recommandés

- Deux soumissions concurrentes même triple/payload : une ligne intake et un reçu ; deux mêmes triples/payloads différents : un succès, un conflit, jamais écrasement.
- Même requestId, namespace différent ou sujet différent : aucune récupération du reçu précédent. Faux proposedBy/sourceClient/tenant client : rejet ou identité serveur imposée.
- Même contenu mais provenance, confiance ou suggestedEntities différents : pas de déduplication silencieuse. Si la contrainte historique est conservée, conflit explicite documenté sans ID étranger.
- Réordonnancement des clés JSON imbriquées identique ; modification d'une valeur ou de l'ordre d'un tableau conflictuelle. Absence/null et chaînes JSON invalides traitées selon contrat explicite.
- Réponse perdue après commit puis retry ; redémarrage processus entre submit/status ; retry après approved, rejected, publishing et promoted : ID stable, état stocké réel.
- Read_only ne soumet jamais ; credential contribution ne sort pas de sa namespace et son adaptateur refuse tout outil hors submit/status. Expiré/tampered et statut d'un autre sujet refusés sans fuite.
- Contenu/suggested structures surdimensionnés, requestId invalide, payload incomplet : pas de reçu orphelin. Échec insertion proposition doit annuler la réservation.
- Arrêt durant publication : statut publishing visible sans promesse de publication ; pas d'auto-approbation. Les tests CAS de corrections doivent continuer à passer.

Le wrapper atomique commencé par memex_memory lors de cette revue reprend la bonne clé subject/namespace/requestId et refuse le doublon contenu historique ; son résultat final et ses tests doivent encore être relus après stabilisation. Aucune validation runtime du nouveau parcours n'est revendiquée ici.
