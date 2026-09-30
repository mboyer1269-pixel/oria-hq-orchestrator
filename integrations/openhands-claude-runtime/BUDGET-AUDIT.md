# Budgets du parcours Claude ACP — 30 septembre 2026

Inspection des sources installées dans `oria-openhands-claude:qualification1`,
sans credentials, réseau ni appel modèle. Ce document décrit les mécanismes
disponibles, pas un budget déjà imposé par notre exécutant.

| Limite HQ | État vérifié | Conséquence |
|---|---|---|
| maxIterations | La boucle OpenHands et les tours internes Claude sont distincts. | Transmettre aussi maxTurns à Claude. |
| maxCostCents | Claude maxBudgetUsd arrête après dépassement du coût estimé. | Ne pas promettre un plafond strict ni assimiler ce coût aux quotas du forfait. |
| maxTokens | taskBudget est une option alpha de budget communiquée au modèle. | Aucun plafond dur cumulatif démontré ; signaler hardTokenLimitEnforced=false. |
| timeoutSeconds | Le timeout ACP est un délai d'inactivité réinitialisé par les événements. | Ajouter une deadline externe absolue, puis arrêt du conteneur après grâce. |

## Écart à combler

Claude ACP accepte `_meta.claudeCode.options` avec maxTurns, maxBudgetUsd et
taskBudget. OpenHands 1.50.0 ne transmet actuellement que ses métadonnées de
modèle dans ce chemin. Un raccordement étroit et testé sur le protocole réel est
nécessaire avant de revendiquer la configuration de ces limites.

`usage_update.used` décrit le contexte courant, pas les tokens cumulés de mission.
Le coût final est estimé et rétrospectif. Les reprises ne doivent pas additionner
deux fois un cumul restauré. L'arrêt local ne garantit pas l'arrêt immédiat de
facturation d'une requête déjà engagée côté fournisseur.

## Références dans l'image inspectée

- OpenHands `sdk/agent/acp_agent.py` : 1767–1789 (timeouts), 2070–2120
  (usage), 3260–3264 (métadonnées de session).
- OpenHands `sdk/conversation/impl/local_conversation.py` : 2014–2035
  (contrôles entre étapes).
- Claude ACP `dist/acp-agent.js` : 334/336/358 (options acceptées),
  6490/6601 (propagation), 3955–3970 (coût), 4400–4425 (contexte).
- Claude Agent SDK `sdk.d.ts` : 1915–1936 (budgets), 5616 (coût cumulé).

## Prochaine intégration

Une session dédiée par mission, options explicites, deadline du superviseur,
rapport séparant limites configurées et limites effectivement imposées. Ne pas
introduire de repli API payant ni utiliser taskBudget comme preuve de plafond
dur. Vérifier l'authentification officielle avant toute inférence.
