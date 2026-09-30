# Memex Core et HQ — réalisation et preuves

29 septembre 2026. Premier ensemble de corrections et d'interface réalisé avec trois agents spécialisés et revue croisée. Le produit complet demandé n'est pas encore livré ni déployé.

## Livré dans le code

**Memex Core**, branche `codex/memex-memory-foundations` : scopes authentifiés par projet, attribution serveur, suppression de l'accès remote au vault non partitionné ; exclusion des faits remplacés/quarantinés/expirés ; protection Agent/Human et liens filesystem ; recherche Unicode ; chemin DB worker corrigé ; publication opérateur/worker commune avec journal de reprise, entrée approuvée immuable, collisions vérifiées et crédit unique. Pas d'appel modèle pour publier. Maintenance automatique risquée désactivée par défaut. Dépendances transitives corrigées.

**HQ**, dépôt canonique `C:/Users/micha/Dev/Oria.HQ`, branche `codex/hq-mission-dossier` : dossier de mission interactif dans la page existante, recherche/sélection/actualisation, noms lisibles des responsables, résultat attendu distinct du résultat déclaré, budget distinct de la consommation inconnue. Aucune seconde copie de la mission ni appel modèle ajouté par cette interface.

**Connexion HQ–Memex** : namespace compatible et mapping sans nettoyage destructif ; lecture structurée avec identifiants, source et dates réelles ; statut de confiance prudent system/untrusted ; données étrangères, prose sans preuve et réponses invalides exclues. Transport forcé read_only, délai de connexion borné, processus nettoyé en cas d'échec, erreurs MCP non injectées comme mémoire.

## Vérifications finales

| Vérification | Résultat | Limite |
|---|---|---|
| Memex Windows, gate1 | 209/209, syntaxe valide | Node local 25 ; Node 22 vérifié séparément sur Linux |
| Memex VPS Linux Node 22.22.3 | 209/209, syntaxe valide | Conteneur éphémère, aucune exposition réseau ni données réelles |
| Memex adversarial | 4/4 supplémentaires | Corpus synthétique |
| HQ Node 22.22.3, suite complète | 3 856 réussis, zéro échec, 1 ignoré | Test cross-repo optionnel ignoré dans cette commande |
| HQ cross-repo ciblé | 60/60 ensemble ciblé, dont vrais handlers Memex | Graphe en mémoire ; exécuté séparément avec checkout explicite, pas une connexion production |
| HQ typecheck, lint, build | Réussis après mises à jour | 5 avertissements lint préexistants ; clés Inngest absentes |
| HQ smoke Joris + preuve mémoire | Réussis sous Node 22 | Sans écriture Supabase ni appel fournisseur |
| Interface Chromium | Recherche, sélection, clavier et actualisation vérifiés ; pas de débordement à 320/1280 px | Banc de composant isolé, données fictives, authentification de production inchangée |
| Audits npm production | Zéro alerte connue sur les deux dépôts au contrôle final | Ni preuve de sécurité absolue ni couverture des futurs avis |

Le premier paquet Linux omettait les trois exemples de configuration MCP : échec reproductible corrigé dans le script d'empaquetage, puis suite complète verte. Les archives de validation excluent secrets, .env, données réelles et historique Git.

HQ passe à Next/eslint-config-next 16.3.7 et sharp 0.35.4 ; dépendances compatibles mises à jour dans le lockfile. Runtime Node 22 Windows récupéré depuis nodejs.org, archive vérifiée avec le SHA-256 publié ; il reste local à la validation.

## VPS utilisé et décision de moteur

SSH et capacité vérifiés ; ancien AgentMemory conservé, distinct de Memex Core. Hermes local a réussi un classement synthétique, avec environ 27,62 secondes au total dont 0,90 de génération : preuve élémentaire, pas benchmark de coding. Le modèle a été déchargé après usage.

Paperclip est retenu comme candidat au pilote durable après lecture de son code. Il doit posséder la file ; HQ projette les états. Voir `DECISION-MOTEUR-EXECUTION.md` pour limites de company, idempotence sept jours, Node 24 dédié et isolation nécessaire de l'adaptateur Hermes.

## Ce qui reste nécessaire pour le produit complet

1. Installer et valider le moteur isolé, son stockage, l'authentification et la reprise ; aucune file durable d'exécution n'a encore été reliée à HQ.
2. Connecter un compte fournisseur dans cet environnement. Claude est installé mais déconnecté sur le VPS ; Codex absent du PATH inspecté. Aucun abonnement n'a été déclaré fonctionnel par simple détection du CLI.
3. Valider migration des namespaces, identité runtime Memex dédiée et restauration avant données réelles. Ne pas exposer la mémoire AgentMemory locale.
4. Raccorder sous-tâches, discussion de groupe, décisions versionnées et preuves au dossier HQ. L'écran indique aujourd'hui les liens non encore disponibles.
5. Compléter la cohérence de publication : graphe/vault ne forment pas une transaction distribuée ; visibilité partielle possible, notes historiques non toutes invalidées par SUPERSEDES, anciens promoted non migrés. Un seul publisher par stockage jusqu'à une barrière plus forte.
6. Vérifier les correctifs Next annoncés pour le 30 septembre avant exposition publique. La version 16.3.7 disponible aujourd'hui ne contient pas ces futurs correctifs selon l'[annonce officielle](https://nextjs.org/blog/upcoming-nextjs-security-release-september-2026).

Aucun commit, push, migration de production ni remplacement de service existant. Le conteneur de test a été supprimé automatiquement ; seules des archives de code et preuves non secrètes restent dans le répertoire de validation dédié du VPS. Les captures HQ sont des preuves du banc isolé, pas de l'application déployée.

## Fichiers utiles

- Memex : `docs/AUDIT-2026-09-29.md`, `docs/MCP_PROJECT_SCOPES.md`, `docs/PUBLICATION-RECOVERY.md`.
- HQ : `docs/MEMEX_STRUCTURED_CONTEXT_COMPATIBILITY.md`, `src/features/missions/components/mission-dossier.tsx`.
- Orchestrator : `verify-memex-vps.ps1`, `VPS-ETAT-VERIFIE.md`, `DECISION-MOTEUR-EXECUTION.md`, `HQ-DOSSIER-MISSION.md`, `HQ-ACCEPTATION.md`.

Les 19 scénarios du dossier de conception ne sont pas tous réalisés : les résultats ci-dessus précisent les parcours effectivement testés.
