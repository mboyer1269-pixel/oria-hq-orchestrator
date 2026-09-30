# VPS — état vérifié le 29 septembre 2026

Inspection en lecture seule par SSH et API Hostinger. Aucun secret lu ou modifié ; aucun service existant arrêté.

## Capacité

Ubuntu 24.04, 4 vCPU, environ 16 Go RAM. À l'inspection : environ 14 Go disponibles et 166 Go disque libres. Charge faible à cet instant ; ce n'est pas une mesure de capacité sous charge multi-agents.

## Services observés

| Service | Constat | Conséquence |
|---|---|---|
| AgentMemory existant | Distribution npm @agentmemory/agentmemory, déploiement 1.0.0 ; Node 22.22.3 ; volumes propres | Distinct du dépôt Memex Core 0.8.0. Ne pas remplacer ses volumes ni lui appliquer nos migrations |
| Hermes | Version 0.15.2, Node 20.19.2 | Version Node insuffisante pour lancer directement HQ, qui demande Node 22 |
| Claude dans Hermes | CLI installé ; statut loggedIn=false | Connexion utilisateur nécessaire avant d'utiliser son abonnement ; aucun appel modèle exécuté |
| Codex dans Hermes/hôte | Non trouvé dans PATH lors de l'inspection | Adaptateur et authentification non prêts |
| Open WebUI | Conteneur sain, port hôte 3000 | Ne pas réutiliser ce port pour HQ |
| Traefik | Conteneur actif, écoute HTTP/HTTPS | Configuration des routes et protections à vérifier avant ajout de service |

## Accès et limites vérifiées

SSH fonctionne avec la clé existante et vérification stricte de l'hôte. UFW est inactif ; aucun groupe firewall Hostinger n'était indiqué. Des ports de services sont liés à toutes les interfaces. Cela ne prouve pas à lui seul l'accessibilité depuis Internet ni l'absence d'autres règles réseau. Les chemins / et /health et POST /mcp testés sur le service AgentMemory existant répondent 404 ; ce résultat ne valide ni sa santé fonctionnelle ni son authentification.

## Chemin retenu

1. Vérifier Memex Core dans un conteneur éphémère Node 22, sans port publié et avec données synthétiques seulement.
2. Conserver HQ dans son dépôt canonique C:/Users/micha/Dev/Oria.HQ et vérifier les contrats mémoire avant l'intégration distante.
3. Préparer un service Memex Core séparé, des données dédiées et une version de déploiement identifiable ; ne pas exposer AgentMemory local Windows.
4. Vérifier les routes, accès et restauration avant données réelles. N'annoncer aucune intégration d'abonnement tant qu'une authentification et une exécution contrôlée n'ont pas réussi.

Ce rapport décrit l'inventaire, pas un déploiement ni une certification de sécurité. La publication de Memex Core et les agents fournisseurs restent à valider.

## Essai local Hermes

Ollama écoute sur loopback et dispose de hermes3:8b (environ 4,66 Go sur disque). Un unique classement synthétique en JSON a produit la réponse attendue : rôle tester pour une demande de tests de régression. Temps total : 27,62 s, dont 0,90 s de génération pour 10 tokens ; le reste inclut notamment chargement et traitement du prompt. Le modèle a été déchargé après l'essai. Aucun compte payant ni donnée réelle utilisés.

Conclusion limitée : le modèle fonctionne pour ce cas élémentaire. Cet essai ne valide ni le coding autonome ni la fiabilité générale du classement. Le coût de démarrage favorise un usage différé ou regroupé ; un maintien en mémoire doit être évalué contre la RAM nécessaire aux builds et workers.
