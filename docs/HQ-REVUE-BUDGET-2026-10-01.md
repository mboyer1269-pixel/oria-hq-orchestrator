# Revue indépendante du lot budget HQ

**État final :** les écarts ci-dessous sont corrigés dans le candidat `286a211`. Voir [l’acceptation technique et ses limites](HQ-BUDGET-ACCEPTATION-2026-10-01.md). Les sections suivantes conservent la chronologie des défauts, pas une liste de blocages encore ouverts.

## Revue initiale — état historique

Lot Cursor de la PR privée 9, branche `cursor/budget-reservation-transfer`, commit `8f59b6c`. Base produit `58712d0`, arbre livré `d93acb1b81912da5cbe8d655a9ce0f9780ed2e4c`. Patch SHA256 `5105873bc9d143c7a4ada14468cc29e09391b71e791e64fe89b02a3fec46ee92`, 82 610 octets. Application dans le candidat isolé contrôlée par égalité de l'arbre. Aucun merge principal, déploiement, seed de tarif, plafond utilisateur ou activation de `HQ_CALL_RESERVATION`.

Verdict intermédiaire : **non accepté**. Le code constitue un registre de réservations monétaires désactivé; il ne constitue pas encore une garantie sur la facture fournisseur ni une fonctionnalité branchée dans le chat.

## Vérifications Codex

- Node 22.14 sous Linux : 34 tests ciblés passent, zéro exclusion, 1,68 s. Transport et registre simulés dans cette suite.
- PostgreSQL 16.4 réel en conteneur jetable : le run `1790839683_75669` échoue à `prove-call-reservation-real-db.mjs:82`, résultat `refused` au lieu de `lost`. Le gagnant est non déterministe mais le script utilise ensuite `caller-a` comme gagnant fixe. Le test n'atteint donc pas le redémarrage.
- Le conteneur, réseau et volume de ce seul run ont été supprimés par le script; absence contrôlée ensuite.
- Les quatre validations globales sont différées jusqu'à correction du lot; ne pas confondre les succès du candidat précédent avec ceux de ce nouvel arbre.

Journaux locaux : `.validation/budget-targeted.log`, `.validation/budget-real-db.log`. Snapshot natif isolé : `hq-budget-review-20261001.tHgOIf`. Aucun appel fournisseur.

## Corrections demandées à Cursor

1. **État faux après perte de réponse RPC.** Dans `authorizeCallAttempt`, une réponse perdue après le commit de `markEmitted` conduit à appeler `release`, puis à retourner `released` sans lire son résultat. Or la base refuse la libération d'une ligne `emitted_unknown`. Conserver l'incertitude et le montant; n'annoncer une libération que sur confirmation. Prouver ce cas sans émission réseau fournisseur.
2. **Gagnant de concurrence supposé.** Réutiliser les identités calculées du gagnant et du perdant dans toutes les assertions et couvrir les deux ordres. L'échec ci-dessus reproduit ce défaut du banc, pas un défaut démontré du verrou SQL.
3. **Preuve de reprise trop faible.** La comparaison avant/après ne porte que sur des agrégats et un compte. Comparer les lignes complètes triées, y compris workspace, sujet, propriétaire, modèle, montants et états.
4. **Portée du devis insuffisante.** `covers_max_tokens` borne la sortie, pas les entrées réelles. Une ligne `reliable=true` par modèle sans contrat d'entrée/version/validité ne justifie pas une borne pour chaque requête. Définir ce contrat côté serveur et refuser les requêtes non couvertes; aucun tarif supposé.

Cursor reste seul propriétaire du correctif. Claude a reproduit séparément le défaut de délai HTTP, décrit dans [sa revue](CLAUDE-PROVIDER-DEADLINE-REVIEW.md). Le supplément de délai et la reprise du budget sont deux lots distincts; leurs preuves doivent l'être aussi.

## Supplément de délai vérifié

Transfert `4a3cae5`, correctif Cursor `669c1d3`, arbre produit `cb461c21c37457a6a384d33b6646dc885fb5eaf6`. Le patch de base est inchangé. Empreinte du supplément : `bea0c3093e250bbdc27b933f8f4ef5953eef8d8084b4b883be5889dd8356cb7a`.

Codex a revu le diff et rejoué les 27 tests des clients/délais sous Node 22.14 : tous passent, sans exclusion. Pour `timeoutMs=600`, les corps bloqués sont interrompus en 792 ms (Anthropic) et 601 ms (OpenAI); la suite garde la réservation `emitted_unknown`, 40 cents de fixture, zéro libération. Les réponses complètes réussissent; le transport injecté ignorant le signal reste explicitement hors couverture. Journal `.validation/deadline-targeted.log`. Le serveur est local; ce ne sont ni des temps de mission, ni des appels réels aux fournisseurs.

Le snapshot Linux de revue a ensuite reçu exactement les quatre fichiers du supplément. Les résultats PostgreSQL précédents concernent toujours le lot initial; aucune réussite de reprise budgétaire n'en est déduite.

## Limites maintenues

Le registre vise `generateStructuredJson`. Les appelants sans identité serveur sont bloqués lorsque le flag est actif; le flag reste éteint. OpenHands, abonnements, modèles locaux, authentification/RLS propriétaire et première mission avec un vrai modèle ne sont pas qualifiés par ces essais. AgentMemory reste une mémoire locale de développement.

## Réception du correctif des quatre écarts

Supplément `8ec2164`, transmis par `717e3b7`, patch SHA256 `4a3920e36783a44a51d8033a37deb6f8ca32fd8d1537dc9e5e4d8ab96c8eaca2`; arbre contrôlé `087a126fa1d063b4a29aa7dbb0cd272b281b93b2`. Les versions précédentes des patches restent intactes.

Codex confirme **63 tests ciblés, zéro exclusion**, en 8,00 s. Le run PostgreSQL réel `1790840244_77530` termine code 0 : deux ordres de concurrence, devis absent/invalide/hors borne refusé, émission inconnue non libérable, contenu des réservations et des droits d'émission identique après redémarrage. Le run conserve notamment le gagnant `caller-b` pour `mission-fwd` et `caller-a` pour `mission-rev`. Conteneur, réseau et volume du seul run supprimés; absence contrôlée après exécution.

Les requêtes du banc passent par `psql` avec un rôle privilégié. Cela prouve les transactions et le stockage, pas l'authentification HTTP ou les droits RLS d'un utilisateur.

Le devis possède désormais périmètre entrée/système/sortie, version et validité; les octets UTF-8 des textes et le maximum de sortie sont contrôlés. Il reste à fournir un devis serveur fiable pour un usage réel : ces champs seuls ne créent pas une source de tarifs.

La revue indépendante continue sur les exceptions de Promise du registre (reserve/mark/consume), distinctes des réponses RPC structurées. Le lot n'est pas encore déclaré prêt; les validations globales attendent la clôture de ce point.
