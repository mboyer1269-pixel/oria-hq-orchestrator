# Claude Code — reconnaître l'installation réelle, sans refaire l'audit

Reprendre la session et le worktree `claude-hermes-runtime-probe`. Lire HQ-HERMES-MISE-A-JOUR-2026-10-01.md et HQ-COORDINATION-HERMES-2026-10-01.md depuis le checkout principal Orchestrator. Le VPS a été mis à jour par Codex : 0.21.5, provenance amont vérifiée, santé et protections contrôlées. Tu ne dois effectuer aucune opération VPS ni aucun appel modèle.

Objectif autonome : corriger ta sonde pour que le véritable Hermes Hostinger soit reconnu sans accorder de capacités non démontrées. Périmètre d'écriture exclusif : `integrations/hermes-runtime-probe/`, `docs/CLAUDE-HERMES-UPGRADE-REVIEW-2026-10-01.md` et un court rapport de remise. Aucun fichier produit HQ, backend Antigravity ou banc Cursor.

1. Corriger catalog/observation/classification à partir des faits observés. Séparer image réellement exécutée Hostinger, provenance amont embarquée, version du paquet et exposition via proxy. Absence de ports Docker publiés ne signifie pas absence d'accès web. Ne pas accepter n'importe quel nom ou label comme preuve d'identité.
2. Fournir une observation expurgée attribuée explicitement à Codex et des fixtures de contradiction, provenance absente, capacités seulement déclarées et refus d'authentification. Reconnaître le moteur ne doit jamais signifier « mission qualifiée » ou « approvals prouvées ». Garder la compatibilité des observations précédentes ou documenter la migration.
3. Corriger les affirmations trop absolues de ta revue : un pull ne supprime pas nécessairement l'ancienne image (elle a été archivée ici), un bind mount peut conserver les données, Config.User ne suffit pas à identifier l'utilisateur effectif de l'agent, une issue ouverte ne prouve pas à elle seule qu'une version est affectée.
4. Exécuter les tests ciblés et la sonde sur ces observations, sans réseau ni secrets. Remettre un commit isolé, commandes/résultats, limites et une seule prochaine action utile. Ne pas fusionner ni publier sans coordination; ne pas modifier le contexte/runtime de production.

Réutiliser tes travaux; pas de nouvel audit général, pas de sous-agent supplémentaire, rapport final court. S'il manque une propriété, la nommer « inconnue » et poursuivre les autres validations. Le but est d'enlever le faux blocage d'identité tout en maintenant la frontière entre observation et preuve fonctionnelle.
