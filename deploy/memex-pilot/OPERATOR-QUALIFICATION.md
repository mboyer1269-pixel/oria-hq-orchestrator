# Lot opérateur distant — qualification, activation différée

Le canal de revue est implémenté opt-in dans Memex et HQ ; les comptes agents MCP n'ont pas cette autorité. Deux POST exacts, snapshot et décision, sont relayés par le TLS proxy avec credential `opr1` distinct. Le reviewer vient d'une seule session Supabase propriétaire vérifiée, le principal technique de la configuration Memex. Aucun endpoint de publication.

## Preuves du lot

- Memex : gate1 218 tests réussis, check et agentpack terminés.
- HQ : 3 926 tests réussis, 2 ignorés, typecheck/lint/build/smoke:joris réussis ; 5 avertissements lint préexistants.
- Proxy : 9 tests réussis dont vrai TLS, refus croisé des credentials, chemins exacts, bornes et codes de conflit.
- Contrat réel HQ service → proxy → Memex sur données jetables : scopes, agent refusé, empreinte modifiée, replay durable, décision contraire, attribution humaine/technique ; aucune publication.
- Linux conteneur isolé sans réseau externe : operator-acceptance.mjs réussi ; autorité, scope, empreinte, retry après réouverture et absence de publication.
- Provisionnement credential : deux tests Linux réels des permissions/propriétaires, refus des chemins invalides et non-écrasement.

Snapshot Memex `.validation/memex-runtime-operator` : 39 fichiers, SHA256 manifeste `F8DDEB799AA761011C77C2B79D7AF403593E81246AEAF07140C4790AED938984`.
Image construite et qualifiée `sha256:88e783cab6e426453cd8753d5f6c2acb3c89a802744e1c72d9edbd84337344ce`, tag `oria-memex-pilot:operator`, source VPS `/opt/oria-memex-pilot/source-operator`.

Un défaut de packaging a été trouvé par le premier essai Linux : les sous-répertoires transférés par SCP étaient privés root, donc non lisibles par UID1000. Le Dockerfile normalise maintenant la lecture/traversée des seuls sources et fixtures. L'image corrigée ci-dessus passe l'essai ; la première image défectueuse n'a jamais remplacé le service actif.

## État volontairement distinct du déploiement

Le service actif Memex reste sur le lot governed-review précédent. HQ reste v11 ; le relais TLS actif n'a pas les nouvelles routes. Aucun credential opérateur réel n'a été provisionné, aucun snapshot réel approuvé, aucun changement d'autorité activé. Les scripts de provisionnement sont présents sur le VPS mais seuls leurs tests en répertoires temporaires ont été exécutés.

La priorité utilisateur est désormais le cycle HQ → agents → amélioration de HQ (STRATEGIE-HQ-PAR-HQ.md). Ne pas confondre cette pause de déploiement du lot avec une pause du goal : l'objectif général reste actif. L'activation opérateur est utile mais n'est pas nécessaire pour qualifier la première mission de code.

Pour activer ultérieurement : reprendre la source validée, vérifier les éventuels nouveaux changements, créer credential hors repo avec le script dédié, monter deux fichiers distincts dans Memex/HQ, configurer scope et flags, mettre à jour le proxy et qualifier depuis la session propriétaire réelle. Le script initial ne gère pas une rotation coordonnée. Le canal HTTP Memex conserve un graphe en lecture seule ; approbation et publication ne sont pas synonymes. Un worker activé ultérieurement pourrait publier une proposition approuvée : cela devra être explicitement qualifié.
