# Recette réelle du formulaire — 1 octobre 2026

## Résultat et portée

Codex a effectué les interactions dans le navigateur intégré sur `http://localhost:3344/`. La fixture Next.js d'Antigravity importe le vrai `DevelopmentMissionForm` du snapshot Linux immuable `hq-validation-20261001.by6Fff`. React et le DOM sont réels. Seuls les retours HTTP et les erreurs de stockage sont simulés par les commandes visibles de la fixture.

Les cas ci-dessous passent. Cette recette ne prouve ni l'authentification propriétaire, ni RLS, ni une écriture en base depuis le navigateur, ni Hermes ou un appel modèle. La preuve PostgreSQL est distincte : [journal du banc réel](evidence/2026-10-01-intake-real-db.txt), revu par [Cursor](CURSOR-REVUE-INTAKE-REEL.md).

| Action exécutée | Observation dans le navigateur | Preuve locale |
| --- | --- | --- |
| Insérer un identifiant résiduel, remplir puis enregistrer | Aucun appel; choix explicite reprendre/nouvelle mission; saisie conservée | `browser-s1-residual.txt` |
| Choisir une nouvelle mission puis enregistrer | Un POST, nouvel identifiant, message « Aucun agent lancé » | `browser-s1-created.txt` |
| Refus 403 puis réessai explicite | Deux POST avec identifiant et JSON complets identiques; champs figés; reçu de confirmation | `browser-s4-b-retry-full-payload.txt` |
| Passer de A à B pendant un appel annulable | B vide, aucune charge de A réutilisée, création B distincte | `browser-s3-abort-a-to-b.txt`, `browser-s4-new-b.txt` |
| Recevoir A après passage à B, avec transport ignorant volontairement AbortSignal | La fixture livre HTTP 200 pour A; le formulaire B reste vide et sans reçu A | `browser-s3-late-ignored.txt` |
| Stockage corrompu puis indisponible | Alertes explicites, zéro requête, saisie conservée; restauration du stockage de test | `browser-s5-corrupt.txt`, `browser-s5-unavailable.txt` |
| Recharger puis vérifier le reçu du projet B | Un GET avec l'identifiant conservé, aucun POST; libellé de relecture et non de création | `browser-reload-get-only.txt` |

Ces fichiers sont conservés dans `Orchestrator/.validation/real-infra-20261001/`. Capture : `proofs/delegation/2026-10-01-recette-navigateur-reelle.png`.

## Traçabilité

- Composant testé : SHA256 `cc290783b6105a2895943694e7796a92e56e16b711d864324183e0c043869222`, comportement du candidat `2f08e96`.
- Fixture corrigée : `/home/michael_/.gemini/antigravity/scratch/browser-interactive-fixture`, `app/page.tsx` SHA256 `b50f17712518b7a8806fc6f6e0d3ab17270ea68e8a0cdc432b59f6b2784ac060`.
- Le commit Claude `dc0772f`, repris dans le candidat produit `e0d80e5`, modifie uniquement le paragraphe Paperclip → préparation/confirmation OpenHands. Diff relu et lint du seul fichier réussi. Les interactions ci-dessus portent sur le snapshot avant cette correction de texte, sans différence de logique ou de style.
- Les quatre validations globales déjà réussies sur `2f08e96` n'ont pas été répétées pour ce changement textuel.

## Corrections de méthode

Le premier livrable `browser_recette` utilisait un DOM JavaScript maison (`MockNode`). Codex l'a refusé comme preuve navigateur. Il reste un essai simulé, distinct de cette recette CUA. Antigravity a ensuite créé la fixture Next.js réelle, puis corrigé son indicateur de stockage, son journal JSON et son mode de réponse tardive à la demande de Codex.

Le badge `SIGNAL: ABORTÉ` peut aussi résulter du nettoyage `finally` après une réponse déjà terminée. Il ne prouve pas à lui seul une rupture de transport. Les réponses de cette fixture ne constituent pas un stockage idempotent; elles servent uniquement à vérifier le comportement du formulaire. L'unicité persistante vient du banc PostgreSQL séparé.

La nouvelle maquette reste indépendante et attend la validation visuelle de Michael. Aucun nouveau droit, secret, fournisseur, appel modèle, fusion principale ou déploiement n'a été ajouté.
