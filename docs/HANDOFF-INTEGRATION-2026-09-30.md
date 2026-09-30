# Handoff — qualification intégrée Cursor + Antigravity

30 septembre 2026. Consigné dans le dépôt parce qu'AgentMemory n'était pas
joignable par MCP pendant cette session (serveur retiré de la configuration en
cours de route). À reporter en mémoire partagée quand le serveur répond.

## Faits durables

- Les deux lots revus s'assemblent sans conflit : Cursor `0d2f8a9` plus le patch
  Antigravity figé. Branche `codex/integrated-qualification`.
- Incompatibilité réelle trouvée et corrigée : `operator_status` exigeait un champ
  `id` dans `policy.json`, que `provider_policy` interdit. L'inspection refusait
  donc un connecteur réellement configuré. La correction fait appeler le vrai
  validateur au lieu de redéfinir le format ; `provider_policy.py` est intact.
- `checkedFile` de l'export de développement lit désormais par descripteur
  `O_NOFOLLOW`. Le dernier composant ne peut plus être échangé entre vérification
  et lecture ; les composants répertoires restent vérifiés par chemin, faute
  d'`openat` par composant dans l'API synchrone de Node.
- Suite hôte : 184 tests, zéro exclusion en root sur le VPS. Instantané 5,
  contrats Antigravity 21, inspection opérateur 19.
- Chaîne connectée qualifiée dans un dossier jetable du VPS : nominal,
  interruption puis récupération du résultat terminé avec le code de sortie
  observé, répétition sans nouvelle exécution, persistance après redémarrage de la
  base. Identités de conteneur comparées, pas comptées.
- Authentification fournisseur vérifiée absente : `loggedIn: false`,
  `authMethod: none` dans `oria-openhands-claude-login`.
  `/etc/oria-hq/provider-policies` n'existe pas.
- Docker local indisponible : Docker Desktop arrêté et intégration WSL inactive.
  La qualification connectée passe donc par le VPS isolé.

## Prochaine action unique

Connecter le compte fournisseur officiel dans `oria-openhands-claude-login`, puis
reconstater `loggedIn: true`. Autorisation utilisateur requise.

## À ne pas confondre

Une qualification synthétique reste synthétique. Aucun modèle n'a été appelé,
aucun accès accordé, rien fusionné dans `main`, rien poussé.
