# Socle de revue gouvernée déployé

Qualification du 30 septembre 2026 UTC. Memex image `sha256:04c47d5b4572fed80ea1a04a93bf6a525f8dcfa2567897e80bc0eae108ffd367`, source-review38fichiers, manifeste SHA256 `8F86DC4AD3A85B19D3AC69A380C2864130F682035688AA062B3891F507D9C799`. HQ reste v11 sans nouveau bouton de revue.

## Invariants

Les contributions avec requestId reçoivent un marqueur serveur durable review_required. La migration le rétroapplique aux mappings existants. Les fonctions legacy approve/reject refusent ces lignes, y compris dans leur predicate UPDATE. Une décision locale impose namespace, identifiant de proposition, empreinte canonique version1, reviewer déclaré, décision et identifiant de décision stable. Audit et transition d'état sont atomiques ; même décision rejouée retrouve le même reçu.

Le publisher commun vérifie la décision et le contenu, le journal gelé et son chemin déterministe avant publication ou reprise, y compris alreadyComplete. Un contenu changé, une revue absente ou une décision de rejet ne doivent pas publier. Les outils non classés sont refusés même pour read_write/admin. Aucune capacité MCP de revue/publish n'a été ajoutée.

La fonction locale attribue une décision à l'identité déclarée par l'opérateur ; elle n'authentifie pas à elle seule une personne. Le futur backend HQ doit authentifier le propriétaire et relayer son identité via un canal opérateur distinct, selon docs/REVIEW_AUTHORITY_DESIGN.md. Ne pas exposer directement la fonction aux agents.

## Preuves

- Memex gate0 puis gate1 :217tests passent ; agentpack généré, diffcheck propre.
- `hq-contribution-contract.mjs ... --review` : HTTP signé réel HQ→Memex, pending absent de la lecture, refus d'empreinte périmée/projet étranger, revue locale sur fixture, retry de décision après réouverture, approved toujours absent de la lecture, publication deux fois, une seule mémoire retournée par le handler HQ après réouverture, un journal complete.
- `review-acceptance.mjs` dans un conteneur Linux sans réseau, /runtime tmpfs : revue durable, bypass legacy refusé, stale hash refusé, retry publication unique, mutation post-revue refusée. Acceptance Linux existante passe également.
- VPS après migration : une contribution HQ existante, status proposed et reviewRequired1 ; les deux services de renouvellement de handles réussissent. Le navigateur propriétaire retrouve son reçu en attente. Aucune décision humaine réelle ni publication runtime effectuée pendant cette qualification.

## Migration et rollback

La nouvelle table d'audit et la colonne sont additives. Les contributions historiques avec requestId deviennent soumises à revue ; celles déjà approuvées sans audit peuvent nécessiter une réconciliation opérateur explicite avant publication. Ne pas inventer une approbation rétroactive. Le pilote vérifié ne contient qu'une contribution HQ proposée.

Le compose distant est figé à l'image ci-dessus ; compose.before-review.json conserve l'image précédente. Revenir à cette image enlèverait l'application des nouvelles protections : un rollback opérationnel doit désactiver la contribution et la publication avant d'être envisagé. Ne pas supprimer les volumes ou le marqueur de revue.

Prochaine étape : lecture persistante des propositions et revue dans HQ avec identité propriétaire réelle, autorité distincte des handles agents et preuve de publication. L'orchestration native complète reste à qualifier séparément. Aucun commit/push dans ce lot.
