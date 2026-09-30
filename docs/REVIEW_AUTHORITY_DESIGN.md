# Autorité de revue humaine distante — conception minimale

> Mise à jour après implémentation : les outils non classés sont désormais refusés pour tous les niveaux d'accès. Le socle local `src/intake/review.ts` et le contrôle commun de publication décrits ci-dessous sont implémentés et testés. Le canal opérateur distant reste à créer ; les observations de code initiales suivantes expliquent les défauts corrigés.

Revue source du 2026-09-29, aucune nouvelle permission créée, aucun secret ni service modifié. Le socle de revue locale audité est développé séparément ; ce document décrit les conditions préalables à une future exposition HQ.

## Frontières actuelles observées

- `C:/Users/micha/Documents/memex-core/src/mcp/handles.ts:73,119` refuse admin à la création et vérification des handles. Les handles courants ne distinguent que read_only/read_write/none et namespace ; ils ne prouvent aucune autorité humaine de revue.
- `src/mcp/access.ts:64` classe tout outil hors READ_TOOLS comme read_write. Ajouter simplement un outil review à ce catalogue lui donnerait donc la même autorité qu'à un agent contributeur. Ce serait un élargissement dangereux, même si HQ masque le bouton.
- `src/intake/promotion.ts:23–48` approuve/rejette par ID seul ; aucun reviewer ou hash du contenu n'est requis. `promoteApprovedProposal` appelle le publisher commun. `src/intake/publication.ts:183` admet approved/publishing ; `src/ai/worker.ts:138` appelle directement cette fonction. Un contrôle limité au nouveau wrapper de revue serait contourné par ces voies historiques.
- `C:/Users/micha/Dev/Oria.HQ/src/server/auth/owner.ts:108` vérifie une session propriétaire ; `getAuthenticatedActorId:72` fournit l'identité Supabase réelle. L'identité configurée du workspace peut être différente. La revue doit utiliser un même résultat d'authentification validé pour l'autorisation et l'attribution, sans accepter reviewer fourni par navigateur.

## Minimum sûr à exposer ultérieurement

La version minimale garde review/publish hors MCP agents. Une route opérateur distincte ne devient disponible qu'après conception et qualification explicites de son authentification : credential dédié à audience revue, séparation de clé/autorité avec les handles agents, namespace exact et aucun fallback vers read_write/admin legacy. L'appartenance au réseau privé ou TLS seul ne constitue pas cette autorité. Ne pas élargir le handle actuel pour obtenir un résultat rapide.

HQ valide le propriétaire, l'origine de la requête et le workspace serveur. Il transmet une décision liée à un snapshot précis : version de canonisation, namespace, proposalId, hash cryptographique du payload revu, reviewer authentifié, décision approve/reject, identifiant de décision stable. Memex ne fait confiance au reviewer relayé que parce que l'appelant est le backend HQ opérateur authentifié par le canal distinct ; cette assertion n'est pas une preuve humaine indépendante. Conserver séparément actor humain déclaré et principal technique authentifié dans l'audit. Aucun de ces champs ne vient directement d'un texte agent.

Le GET de revue renvoie le payload exact et son hash/version. Le POST refuse si le hash actuel diffère, si l'état a changé ou si le namespace n'est pas celui autorisé. La décision et le changement d'état sont atomiques. Même identifiant/même décision → reçu identique ; décision contradictoire ou hash différent → conflit. Pas de dernière écriture gagnante. Horodatage serveur, aucune modification rétroactive de l'événement de revue ; un changement de contenu nécessite une nouvelle proposition ou version et une nouvelle revue.

L'interface montre le contenu réellement approuvé, y compris les champs ayant un effet de publication. Une approbation content-only ne peut pas valider silencieusement suggestedEntities, relations SUPERSEDES, provenance ou niveau de confiance cachés. Pour le pilote, restreindre les propositions affichées/approvables au schéma effectivement présenté est préférable à une validation partielle.

## Invariant au dernier point de publication

Le publisher commun vérifie lui-même que toute proposition soumise à revue auditée possède une décision approve persistée, portant le bon namespace et le hash du payload effectivement publié. Les fonctions historiques approve/reject doivent refuser ces propositions ou déléguer au contrat audité complet. Un statut SQL approved isolé ne suffit pas. Le worker et la reprise d'un journal passent par le même contrôle ; un journal ne doit pas publier un payload différent de celui approuvé.

La distinction legacy/audité ne doit pas être un champ falsifiable fourni par l'agent. Elle découle d'une provenance/contrainte persistée par le serveur lors de l'admission. L'absence accidentelle de la ligne d'audit doit provoquer un refus pour les contributions qui l'exigent ; elle ne doit pas faire retomber automatiquement en mode legacy. Ceci protège les chemins applicatifs, pas contre un administrateur ayant accès direct à SQLite et aux clés.

La reprise alreadyComplete peut vérifier et rendre un reçu de publication existante, mais ne doit pas réouvrir une visibilité ou réconcilier une projection différente sans l'invariant d'approbation. Après publication, révoquer une décision n'est pas équivalent à retirer la mémoire : ce serait une opération distincte avec journal et impact graphe/vault, hors de ce lot.

## Contre-exemples et tests obligatoires

1. Handle agent read_write appelle review/publish : refus, même avec JSON reviewer=owner et namespace valide. Idem handle read_only et token legacy généraliste.
2. Propriétaire voit payload H1 ; contenu devient H2 avant clic : conflit, aucune approbation H2.
3. Deux décisions opposées concurrentes sur le même état/hash : une décision acceptée, l'autre conflit explicite ; audit sans ambiguïté.
4. Fonction legacy approveProposal appelée sur proposition auditée sans review : refus. Statut approved injecté en fixture sans décision : publisher et worker refusent.
5. Journal gelé avec payload différent du hash approuvé, reprise publishing ou réconciliation alreadyComplete : aucun effet de publication non autorisé.
6. Auth email autorise une identité différente du owner ID configuré : reviewer enregistré est l'identité authentifiée. Paramètre reviewer navigateur rejeté ; absence d'acteur authentifié refusée.
7. Namespace foreign, proposalId foreign, replay de décision d'un autre projet : refus indistinguable d'un ID absent avant divulgation du payload.
8. Réponse perdue après commit : retry du même decisionId retourne le reçu ; aucune nouvelle décision ni republication.
9. Admission agent contenant status=verified/zone=human : ne donne aucun droit de revue ni validation humaine automatique.

La revue locale auditée peut être qualifiée avant ce protocole distant. Ne pas annoncer « revue depuis HQ disponible » tant que le canal d'autorité distinct et les tests bout en bout propriétaire→audit→publication ne sont pas réalisés.
