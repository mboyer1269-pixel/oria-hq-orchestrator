# Recette adversariale — raccordement Hermes/HQ

Base produit `f0e42a531c1a1e2d47726f870d15f0f905f367d8`, arbre `12f387bccc0687f92c28e6e1abf11f9cb4a4365e`. Aucun service, routeur, UI ni migration n'est modifié. Le lot RLS accepté n'est pas rejoué. Ceci n'est pas une session OAuth, un JWT, une infrastructure OpenHands, ni un modèle.

Hermes orchestre. HQ autorise et conserve la mission. OpenHands exécute. Un argument du modèle ne confirme pas.

## Commande

Depuis la racine produit :

`node --test --test-concurrency=1 proofs/hermes-hq-acceptance.mjs`

Le verdict honnête de cette commande, tant que `HERMES_HQ_ADAPTER` est absent, est :

`HERMES_HQ_RECETTE contrat_simule=ok adapter=bloque infrastructure=non_execute modele_reel=non_execute`

Ici : 5 tests, 0 échec, 5274 ms, exit 0. Exit 0 signifie que les effets HQ simulés tiennent et que l'adaptateur n'a pas tourné. Ce n'est pas un raccordement qualifié. L'injection est le chemin `HERMES_HQ_ADAPTER` vers un module qui exporte `runHermesHqJoin`. Fichier absent ou export absent : `blocked`. Cette recette ne l'appelle pas.

## Matrice

| Scénario | Appel réel | Effet attendu | Preuve |
| --- | --- | --- | --- |
| Identité du modèle contre le contexte de confiance | `POST /api/missions/development` avec `createdBy`, `workspaceId`, `actorId` ou `confirm` ; `POST /api/orchestration/openhands` `prepare` avec `actorId`, `workspaceId` ou `endpoint` | HTTP 400, zéro mission, le service de confirmation n'est pas appelé | `proofs/hermes-hq-acceptance.mjs`, handlers et services réels, session synthétique |
| Création distincte de la confirmation | POST développement valide, puis `prepare`, puis `confirm` avec un hash qui n'est pas celui préparé | Brouillon, `executionRequested` false, `createdBy` égal à l'id de session, zéro ledger ; préparation `externalEffectAllowed` false ; hash étranger HTTP 409 `dossier_changed`, toujours zéro ledger | même fichier |
| Réponse perdue après effet | l'écriture du brouillon réussit puis lève une erreur | HTTP 200, corps `outcome_unknown`, une ligne reste, GET retrouve le même id, le nouvel essai ne crée pas une seconde ligne, le secret n'apparaît pas | même fichier |
| Deux confirmations simultanées | deux `confirm` avec le hash préparé | une seule `reserved`, les deux `externalEffectAllowed` false, une ligne d'autorité liée à l'acteur et au workspace de session, rejeu `already_reserved`, aucune clé de lancement | même fichier |
| Workspace, destination ou exécuteur imposés | champs en trop ; configuration serveur `executorVersion` `9.9.9` | HTTP 400 avant le service ; lancement configuré `unavailable`, magasin non touché, la version absente du résultat | même fichier |
| Deadline sur le corps | corps OpenHands qui ne se termine pas | HTTP 400 `invalid_request` entre 4,5 s et 8 s, service et lancement non appelés | même fichier, durée observée 5023 ms |
| Secret dans l'erreur | la configuration lève une erreur contenant un secret synthétique, ou un JSON invalide le contient | `unavailable` ou `reconciliation_required`, `externalEffectAllowed` false, secret absent, zéro lecture du magasin | même fichier |
| Coût hors autorisation | dossier réservé à 100 cents, configuration serveur à 40 cents, confirmation avec le hash de la prévisualisation concordante | prévisualisation concordante `prepared` sans écriture ; écart `ineligible_mission`, `externalEffectAllowed` false, zéro écriture | même fichier |
| Adaptateur Hermes | variable absente, chemin absent | `blocked`. Un fichier factice qui exporte la fonction est seulement détecté, pas exécuté comme raccordement | même fichier |
| Infrastructure et modèle | aucun | `fetch` n'est pas appelé | même fichier, `networkCalls` 0 |

Les tests déjà qualifiés des handlers injectés, de la frontière propriétaire et des services de confirmation ou de lancement ne sont pas recopiés ici.

## Hors de cette recette

Pas de VPS, pas de compte réel, pas de modèle payant, pas de nouveau secret, pas de port public, pas de déploiement. L'image Hermes `sha256:374874de079dc821db4cf9e67df8c8eee8064deb51c5b64524d3b130967045c1` et les capacités annoncées ne sont pas rejouées. Le verdict sur le commit du constructeur attend ce commit.
