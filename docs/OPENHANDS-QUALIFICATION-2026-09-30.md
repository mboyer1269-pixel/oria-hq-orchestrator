# Qualification OpenHands — état vérifié

30 septembre 2026. SDK OpenHands 1.50.0 installé et exécuté dans un conteneur de qualification isolé sur le VPS. Les échanges ACP synthétiques et la relecture des événements persistés passent. Aucun modèle ni fournisseur connecté, aucune mission de développement autonome validée. Voir `../integrations/openhands-qualification/RESULTS.md` pour les limites des preuves.

## Direction produit

Le choix utilisateur est un HQ personnalisé autour du moteur OpenHands, accessible dans ORIA HQ. Un fork ciblé de l'interface est acceptable; préserver un lien avec upstream et limiter les modifications du moteur. Paperclip reste un témoin déjà installé, pas une obligation d'empiler un deuxième ordonnanceur. Memex reste la mémoire par projet.

## Versions et frontières

- SDK release 1.50.0, commit `dcf401af7a9a302ef92cb7d092e1df9bb659daa5`, Python >=3.12. ACP Python >=0.12.1,<0.13.0.
- Adaptateur Claude ACP 0.84.0, commit `bdb50ad984336e62dde1d41339f04071f6617085`, Node >=22. Son SDK Anthropic 0.3.284 ne prouve pas la compatibilité du CLI déjà installé.
- Dans la release SDK, `_OpenHandsACPBridge.request_permission` choisit automatiquement une option. Le mode Claude par défaut est `bypassPermissions`. Choisir `acp_session_mode="default"` ne supprime pas l'approbation automatique du bridge.
- Aucun callback public de permission raccordé à la politique de confirmation trouvé dans le fichier ACP examiné. Une UI HQ de confirmation ne contrôle pas implicitement les outils internes.

Sources : [SDK épinglé](https://github.com/OpenHands/software-agent-sdk/blob/dcf401af7a9a302ef92cb7d092e1df9bb659daa5/openhands-sdk/openhands/sdk/agent/acp_agent.py), [adaptateur Claude épinglé](https://github.com/agentclientprotocol/claude-agent-acp/blob/bdb50ad984336e62dde1d41339f04071f6617085/src/acp-agent.ts).

## État réel du VPS

Les conteneurs HQ, Memex, Paperclip et Claude répondent présents et sains dans Docker. Cela ne prouve pas une mission exécutée.

Le home Claude isolé est volontairement vide de connexion permanente. Le contrôle direct `claude auth status` sous UID1000 retourne non connecté. Ce résultat est compatible avec la conception existante : Paperclip matérialise la connexion gérée uniquement pour son exécution native. Il ne prouve pas que la connexion Paperclip est perdue. Référence locale : `deploy/providers/runner/CLAUDE.md`.

Le navigateur Paperclip est connecté et affiche encore la tâche d'onboarding en Todo. L'ancienne demande d'autorisation CLI est expirée. Ne pas confondre session web, autorisation CLI, connexion fournisseur et exécution d'une mission.

## Décision et preuves restantes

1. Installation réalisée depuis les packages officiels dans un environnement distinct, sans secrets ni montages opérationnels. Les packs de connaissance restent en lecture seule et ne sont pas exécutés.
2. Événements, résultat synthétique, échange de permissions et relecture du stockage qualifiés avec le vrai SDK. Interruption et reprise après panne restent à qualifier. Un résultat simulé ne compte pas comme mission modèle réussie.
3. Adapter le bridge pour refuser par défaut et transmettre une décision explicite, avec tests du refus et de l'expiration; sinon ne qualifier qu'une exécution autonome confinée, sans prétendre au contrôle humain des outils.
4. Pour un essai Claude indépendant, effectuer une connexion officielle dédiée. Ne pas extraire ni copier les secrets gérés de Paperclip. Ne pas activer une API facturée comme repli automatique.
5. Une modification réelle sur une copie isolée, validation externe sans credentials fournisseur, puis interruption et reprise avec conservation du diff. Garder coûts, événements et interventions observés.

L'intégration finale et l'objectif général ne sont pas achevés. Les optimisations UI/Memex validées constituent une base utile, mais pas une preuve d'orchestration autonome.
