# Livraison suivante — une directive, une mission, un résultat

Ce mandat courant remplace les anciennes attributions. Hermes est identifié et mis à jour; voir HQ-HERMES-MISE-A-JOUR-2026-10-01.md. Le gel de la maquette demeure. Il n'empêche pas le travail backend isolé autorisé par Michael.

Base produit publiée : `codex/hq-delivery-integration`, `f0e42a531c1a1e2d47726f870d15f0f905f367d8`, dépôt `mboyer1269-pixel/Oria.HQ.Michael.HQ-APP`. La base de code qualifiée est `cf4fc4a`; la tête suivante ne change que la documentation. Ne pas repartir d'un ancien patch isolé. Préserver tous les travaux et les previews existants.

## Propriétaires et sorties

| Agent | Écriture exclusive | Livrable |
| --- | --- | --- |
| Antigravity | Raccordement Hermes/HQ minimal en copie backend isolée, tests directs; fichiers annoncés dans sa remise initiale | Adaptateur utilisable, commande locale reproductible, limites et liste exacte des prérequis pour la mission réelle |
| Cursor | Tests indépendants et rapport de recette, jamais le code du constructeur | Scénarios adverses exécutables sur le contrat existant, puis verdict sur le commit du raccordement |
| Claude Code | `integrations/hermes-runtime-probe/` et rapport Hermes dans son worktree Orchestrator existant | Sonde qui reconnaît le véritable conditionnement Hostinger et distingue provenance, capacités déclarées et fonctionnement qualifié |
| Codex | Assemblage, vérifications globales, documentation et mémoire de développement | Candidat cohérent avec preuves et prérequis explicitement ouverts |

## Règles communes

Hermes propose et délègue; HQ reste autorité des identités, missions, confirmations et preuves; OpenHands exécute. Une réponse de chat ou une création de brouillon n'autorise pas un lancement. Aucun argument modèle ne peut choisir arbitrairement l'acteur, le workspace, une URL ou un exécuteur. Utiliser les contrats d'admission et de lancement existants, le routeur existant et les refus par défaut.

Pas de modification du VPS par les agents, compte/secret réel, appel modèle, fallback payant, nouvelle exposition publique, migration active, intégration UI, fusion principale ou déploiement dans ce lot. Le code peut être construit et testé localement. Les besoins d'activation sont rendus concrets, pas contournés.

Contexte : lire ce mandat, le constat Hermes et les fichiers réellement touchés; pas tout l'historique. Réutiliser les recherches et les bancs clos. Un seul constructeur et, au plus, un sous-agent de revue en lecture seule chez Antigravity. Pas de duplication d'audit. Utiliser les réglages de modèles/forfaits actuels sans les augmenter. Les tests ciblés appartiennent à l'auteur; les quatre contrôles globaux sont centralisés par Codex sur l'assemblage final. Les blocs se terminent par une remise compacte, puis attente de revue.

## Critère de livraison du raccordement

1. Cartographier les quelques fonctions existantes entre directive, admission, confirmation, lancement et retour. Identifier un seul chaînon manquant avant d'écrire.
2. Construire le plus petit raccordement compatible avec la version observée d'Hermes. Un mode local sans modèle fait traverser le véritable adaptateur et le véritable service HQ; toute doublure est nommée. Ne pas fabriquer une interface d'extension Hermes à partir du seul endpoint capabilities.
3. Tester refus sans autorisation, même requête simultanée, charge divergente, réponse perdue après effet, deadline sur le corps, refus inter-workspace et retour après reprise. Ne pas recopier les tests déjà qualifiés si le code ne change pas. Une issue inconnue reste inconnue; aucun relancement aveugle.
4. Produire un manifeste de remise : dépôt/base/commit/arbre, fichiers, commande exacte, sorties, exclusions, dépendances et limites. Séparer contrat simulé, infrastructure réelle et modèle réel.
5. Rendre la prochaine mission réelle exécutable par un opérateur autorisé : configuration attendue sans valeur sensible, profil et budget nécessaires, résultat attendu, commandes de lancement et retour arrière. Ne pas annoncer cette mission réussie avant son exécution.

Mesures utiles : durée de la commande de recette, requêtes sortantes observées, nombre d'exécutions pour une identité de mission, volume de contexte transmis si disponible. Aucun gain de tokens inventé; ni objectif arbitraire de nombre de tests.
