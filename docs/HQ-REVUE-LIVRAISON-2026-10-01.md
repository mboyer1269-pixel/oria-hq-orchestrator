# Revue indépendante de la livraison HQ — 1 octobre 2026

Ce relevé complète le contrat de livraison. Il distingue le code inspecté, les tests rejoués et les déclarations des agents. Il ne constitue ni une acceptation de production ni une preuve de mission avec un modèle.

## État courant de l'assemblage

Candidat isolé `codex/hq-delivery-integration`, commit `c4659f1`, base `e9ff840`. Il inclut les sept commits Cursor, l'admission Antigravity et les accès/reprise Claude; aucune maquette et aucune fusion dans le checkout canonique.

- Cursor : 61 tests ciblés passés; identifiants invalides et coût des tentatives corrigés.
- Admission : 18 tests de contrat passés; harnais réel `720d513` repris avec syntaxe vérifiée. Docker bloque toujours son exécution réelle.
- Claude : source `13930e1`; 107 tests ciblés et dépendants rejoués par Codex, réussis. TypeScript global passe. Lint global révèle deux causes d'erreur dans le formulaire (reset d'état dans l'effet et lecture d'une ref au rendu, neuf diagnostics). Correction minimale renvoyée à Claude; build et smoke finaux non exécutés après cet échec.
- Avant le lot Claude, les quatre contrôles globaux avaient passé. Cela ne qualifie pas le nouveau candidat.
- UI `87c00df` : deux directives successives vérifiées au navigateur, puis état après GO cohérent (zéro arbitrage, pas de nouveau GO). Historique distingué et budget explicitement démonstratif. Mobile 390 × 844, largeur client/scroll 375/375. Réactiver une carte historique crée une nouvelle mission démo; libellé à clarifier. Validation visuelle et allègement de l'en-tête soumis à Michael.

Les sections suivantes conservent la chronologie et les reproductions. L'état courant ci-dessus prime sur leurs anciens statuts.

## Backend Antigravity

Commit inspecté : `537545e`, branche `antigravity/hq-intake-bridge-handoff`, dépôt WSL `oria-hq-intake-bridge`.

Commande rejouée par Codex :

```sh
node --test src/scripts/development-mission.test.mjs src/server/missions/development-mission.test.mjs src/app/api/missions/development/handlers.test.mjs
```

Résultat : **18 tests réussis, 0 échec, 0 exclusion**. Ce sont des tests de contrat avec dépendances simulées. La classification des erreurs avant écriture a été améliorée. La preuve précédemment présentée comme complète est désormais étiquetée simulée.

La revue du harnais réel relève encore les points suivants, transmis au propriétaire avant exécution :

- `run-intake-real-db.sh` appelle `docker info` et `curl` sans délai maximal par appel. Une boucle bornée ne borne pas un appel bloqué.
- `prove-cli-real-db.mjs` hérite de tout `process.env` en n'effaçant que quatre variables. Ce n'est pas un environnement purgé; préférer une liste minimale explicite pour les processus de test.
- `process.exit(0)` dans la vérification après redémarrage empêche l'exécution du `finally` qui nettoie le répertoire temporaire.
- Après concurrence divergente, comparer uniquement le `missionId` ne vérifie pas que le contenu gagnant est intact. Vérifier le contenu avant et après redémarrage.
- Le cas de deux créations simultanées avec **le même** contenu doit être vérifié séparément du conflit entre contenus différents.

La configuration CLI reste une entrée privilégiée contrôlée par le lanceur. Un commentaire indiquant « fichier 0600 » n'est pas une preuve que le lanceur empêche le choix arbitraire de l'identité. Ce contrat de confiance doit être démontré avant exposition aux outils d'un agent.

## Maquette Antigravity

Dépôt WSL `oria-hq-construction`, état au début de la revue `c60b4ae`. Preview de développement lancée par Codex en loopback : `http://localhost:3337/hq/hermes-cockpit`.

Observations réalisées dans le navigateur :

- Aujourd'hui → Discuter → scénario question → scénario directive : les interactions modifient bien le contenu de démonstration. Cela ne prouve aucun appel au backend.
- À 390 × 844 pixels : `documentElement.clientWidth = 375`, `scrollWidth = 467`. Le débordement horizontal est reproduit.
- La navigation générale reste visible et les avertissements occupent l'essentiel de l'écran avant la discussion. Ce n'est pas encore une expérience mobile quotidienne satisfaisante.
- Le shell nomme Joris alors que le cockpit nomme Hermes. L'identité de l'interlocuteur doit être cohérente.
- `src/app/hq/hermes-cockpit/page.tsx` ignore `NODE_ENV` lors du repli `ORIA_ALLOW_DEV_USER_FALLBACK`. Un réglage de prévisualisation peut alors éviter la garde d'accès en production. Correction et test demandés dans ce fichier, sans chevaucher le lot `owner.ts` de Claude.
- Le modèle local apparaît configuré, Hermes actif et une exécution est dite garantie sans observation du runtime. Les explications pédagogiques affirment aussi des protections et reçus non qualifiés. Les exemples doivent être explicitement des scénarios, et les capacités réelles venir d'une observation.

Capture avant correction : `proofs/delegation/2026-10-01-maquette-mobile-avant.png`.

La maquette reste indépendante. Un terminal de démonstration en lecture seule ne clôt pas l'exigence utilisateur d'accès aux outils réels de la mission. La validation visuelle par Michael reste nécessaire avant intégration.

## Autres lots

- Claude Code `38383533` : correction accès/reprise en cours dans `claude-acces-reprise`. Les permissions ponctuelles d'inspection et de reproduction locale sont traitées; aucun verdict final à ce stade.
- Cursor : implémentation du routage en cours. Un test Ventures dépend directement de l'ancien repli implicite; permission donnée de corriger ce test et vérifier ses appelants, sans inventer un consentement payant ni élargir les fonctionnalités Ventures. Branche et PR demandées pour récupérer le résultat exact.

## Blocage d'infrastructure constaté

Docker Desktop est installé mais son démarrage échoue sur le socket Windows `dockerInference` avec une erreur AF_UNIX. La présence de processus Docker ne signifie pas que son moteur fonctionne. Aucune réinitialisation, suppression de volume ou modification des protections n'a été faite.

L'inspection SSH en lecture seule du VPS a été demandée à Michael après le refus automatique de la session Claude. Elle reste en attente; ne pas la contourner. La connexion Zapier n'est pas disponible et n'est pas nécessaire aux lots de code.

## Décision de revue

Conserver les trois propriétaires et terminer ces corrections. Rejouer les tests sur leurs commits livrés, puis assembler dans une copie isolée. Ne pas déclarer le HQ immédiatement utilisable : qualification de la base persistante, capacités Hermes réelles, mission avec modèle, accès aux outils et validation UI restent à obtenir.

## Revue complémentaire et assemblage isolé

### Cursor

Le patch produit de `cbc7d61473a5e77d524e2018f07cce287d4a3ec8` est transféré par la PR privée [Orchestrator #7](https://github.com/mboyer1269-pixel/oria-hq-orchestrator/pull/7). Cette PR contient des artefacts de transfert, pas une intégration du produit dans Orchestrator. Son SHA256 vérifié est `bd0392246e0a572b712eb41994aa87d06f6f6d6f6bf14ba838e06f45497033c2`.

Application réussie sur `e9ff840` dans `C:/Users/micha/Dev/Oria.HQ/.claude/worktrees/hq-acces-reprise`, branche `codex/hq-delivery-integration`. Arbre obtenu identique à celui livré : `58d354330c3687432fbe5fb5d4a301e7246d63b6`. Installation sous Node 22.14 WSL avec moteur npm respecté.

**57 tests ciblés réussis, 0 échec, 0 exclusion** : fournisseur JSON, routeur, exécution, brain, mission-draft-control et générateur Ventures. Aucun appel réel au modèle.

Deux défauts supplémentaires reproduits par Codex et confiés à Cursor :

1. Les clés `constructor`, `toString` et `__proto__` traversent l'objet d'allowlist et déclenchent le faux fetch OpenAI avec cet identifiant. La sortie annonce même un fournisseur de type fonction/objet. Exiger contrôle own-property ou Map et zéro requête pour ces valeurs.
2. Une réponse Anthropic 503 suivie d'un succès OpenAI autorisé ne conserve dans `cost` que l'usage du second essai. Conserver les tentatives et l'incertitude du coût total; la chaîne d'erreurs textuelle seule ne suffit pas à la comptabilité.

Reproduction locale : `.validation/cursor-routing/review-edge-cases.mjs`, exclusivement avec fonctions réseau injectées et valeurs synthétiques. Lot non accepté tant que corrigé et revérifié.

### Backend Antigravity

`e02339f` améliore délais readiness, environnement des enfants et concurrence de payload identique. Mais son harnais attend `objective` et `scope` dans un reçu qui ne les contient pas. Correction demandée : vérifier le contenu en base par mission et workspace, conserver le gagnant exact avant redémarrage, puis comparer après. Ne pas élargir le reçu pour adapter le code au test.

Les trois fichiers runtime/tests d'admission provenant de ce lot ont été appliqués sans conflit dans la copie d'intégration, distincte du produit canonique. **18 tests d'admission/service/handlers y passent aussi, sans exclusion**. Aucun résultat PostgreSQL réel n'en est déduit. Les rapports historiques et la maquette n'ont pas été importés.

Décision de consolidation pour cette copie : `feature-module` de mission existante, propriétaire équipe HQ, problème admission/récupération des brouillons par adaptateur de confiance, lien service canonique des missions, entretien sans nouvelle dépendance. Qualification réelle et vérification finale de l'ensemble restent exigées avant fusion.

### UI Antigravity

Sur `0857a11`, le débordement mesuré à 390 × 844 est corrigé : `clientWidth=375`, `scrollWidth=375`. Le repli de prévisualisation de la route est désormais limité à `NODE_ENV=development`.

Défaut fonctionnel reproduit : saisir « Ajouter une recherche de prospects par ville, avec un filtre Montréal. » dans Aujourd'hui, transformer en mission, puis ouvrir Atelier. Discuter montre la nouvelle directive; Atelier reste sur `mis_mon_8829`, la mission de monitoring snapshot initiale. La continuité promise entre vues est donc absente. Correction confiée aux sous-agents UI : un seul état partagé, preuves/logs réinitialisés pour toute nouvelle mission, vérification de deux directives successives. La maquette reste non approuvée.

### Correctif Cursor revérifié

Le patch actualisé contient le commit de correction `a8413508d48bd7776931f33292e4febc918f9b07` et sa documentation jusqu'à `79b0568bd9b8ae9a3d2b2d992330c94add2e7671`. SHA256 du patch : `24d9d5ca1e2fea6ba480e5fed7bf866f0599b8c970a9e3456e8233c4c02e7210`. Arbre reproduit après application : `558037ddc80cbcd58a001bb59c5244d79c98e8fa`.

Les trois identifiants invalides sont désormais refusés sans appel réseau; après une tentative possiblement facturée puis un succès, le coût global reste inconnu et les tentatives sont conservées. **61 tests ciblés réussissent chez Codex**, sans appel réel fournisseur. Ces deux observations de revue sont corrigées.

La copie comprenant routage et admission a passé TypeScript (avant le dernier correctif Cursor) et lint (après ce correctif) : zéro erreur, cinq avertissements dans des fichiers hors lot. Les validations globales finales restent à exécuter sur l'assemblage incluant Claude; ne pas généraliser ces résultats à une version future.

### Répartition des validations

Pour éviter les compilations redondantes des mêmes dépendances, chaque agent termine ses tests ciblés et remet un commit précis. Codex prend les quatre contrôles globaux sur le candidat assemblé. Cette coordination remplace la demande initiale de répéter ces quatre contrôles dans chaque copie. Aucune livraison finale ne sera déclarée avant ces contrôles.
