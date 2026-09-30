# Terminer HQ en utilisant HQ

> Direction précisée après la comparaison OpenHands : construire d'abord le HQ constructeur, assistant de développement, puis l'utiliser pour ORIA HQ. Le plan de référence est désormais [PLAN-HQ-CONSTRUCTEUR.md](PLAN-HQ-CONSTRUCTEUR.md). Les choix de moteur ci-dessous restent historiques/provisoires ; ils ne doivent pas empêcher la qualification OpenHands ni imposer Paperclip par inertie.

Directive utilisateur du 29 septembre 2026, précisée pendant le lot de revue Memex : rendre d'abord le quartier général capable d'orchestrer une équipe de développement, puis confier à cette équipe l'amélioration de HQ lui-même. Ce document fixe la priorité actuelle ; les anciens plans de lots restent des historiques, pas un ordre immuable.

## Décision et critique

La mémoire fiable est un prérequis utile, mais elle ne prouve pas l'orchestration. Nous avons suffisamment avancé cette brique pour déplacer l'effort principal vers une mission réelle. Pas de nouveau moteur vectoriel, de catalogue massif de skills ou de refonte visuelle générale avant cette preuve. Le lot de revue humaine en cours est terminé et testé séparément ; son activation ne doit pas devenir une dépendance artificielle de la première mission de code.

L'objectif n'est pas une application qui modifie librement son propre serveur en cours d'exécution. HQ doit commander un travail sur une copie isolée de ses sources, produire un changement vérifiable, puis permettre sa livraison contrôlée. Le poste de pilotage reste utilisable si l'agent casse sa branche ou si le candidat échoue.

## Chemin critique et preuves

| Étape | Résultat utilisable | Preuve exigée |
|---|---|---|
| 1. Qualifier un exécutant | Un compte déjà disponible réalise une petite tâche dans un dépôt isolé | Changement réel, commande exécutée, statut final, consommation et durée disponibles ou explicitement inconnues |
| 2. Relier une mission HQ au moteur | Création, dispatch, suivi et arrêt d'une tâche réelle depuis HQ | Identité mission/issue persistée ; aucun double dispatch après réponse perdue ; arrêt constaté ou état arrêt demandé clairement distinct |
| 3. Ajouter la revue | Un second exécutant examine le changement du premier | Rapport sur le diff et résultats de tests ; acceptation ou correction motivée ; aucune auto-approbation du développeur |
| 4. Faire améliorer HQ par HQ | Une amélioration limitée de HQ passe tout le parcours | Branche isolée, résultat essayable, critères satisfaits, tests, décision de livraison, possibilité de retour arrière |
| 5. Étendre sur preuves | Missions suivantes, routage et autres comptes | Comparaison de missions terminées, coût total, reprises, qualité et limites réelles des intégrations |

Le premier candidat est Claude via l'adaptateur natif Paperclip et son runner SSH déjà préparé. Sa connexion et sa première tâche restent à vérifier. Le premier exécutant retenu sera celui qui réussit le test réel avec l'accès existant, pas celui que nous préférons théoriquement. Antigravity a déjà une preuve d'inférence, qui ne suffit pas à prouver un cycle de développement ; son raccord spécifique ne doit pas retarder le parcours natif. Cursor et les autres ne sont pas déclarés opérationnels sur la base d'une installation ou d'une authentification seule.

## Équipe et propriété

- Chef : clarifie le livrable, décompose seulement quand utile, fournit les dépendances et distribue les tâches. Les transitions ordinaires et la collecte d'état restent déterministes.
- Développeur : produit un changement dans un périmètre de fichiers attribué, avec tests adaptés et limites explicites.
- Réviseur : examine indépendamment le diff et les preuves ; peut demander une correction. Ce rôle n'impose pas un agent permanent supplémentaire.
- Opérateur : conserve la décision de livraison sur l'instance utilisée et les actions sensibles. Aucun agent de code ne reçoit les secrets de production ni l'accès Docker de l'hôte.

Un exécutant d'abord ; au plus deux tâches d'exécution simultanées pendant le pilote, uniquement si elles sont indépendantes. Aucune réunion multi-agent sans question concrète et décision attendue. Un blocage répété remonte au chef au lieu de relancer indéfiniment le même travail.

HQ conserve l'intention et l'expérience utilisateur. Paperclip conserve la file et les exécutions durables. Memex conserve les connaissances utiles ; le dossier de mission référence les sources et décisions. Pas de deux files concurrentes, ni de copie complète de chaque conversation dans tous les contextes.

## Économie et qualité

Chaque sous-tâche reçoit : objectif, critères d'acceptation, périmètre de fichiers, dépendances, références de contexte, commandes de validation, limites d'exécution et format de résultat. Les sorties attendues sont un diff, des preuves et les problèmes restants, pas un long compte rendu répété.

Les limites de durée, nombre de tentatives et appels sont imposées par le système. Un plafond de tokens n'est annoncé comme strict que si le fournisseur permet de l'imposer ; sinon l'estimation reste clairement identifiée. Les quotas et abonnements restent propres à chaque fournisseur. Aucun routage « gratuit » présumé, aucun basculement automatique vers une API facturée non autorisée.

Mesures : mission acceptée ou non, durée totale, tokens connus par fournisseur, consommation inconnue explicitement signalée, reprises, défauts découverts à la revue et après livraison. Les tests/scripts remplacent les appels modèle pour les opérations déterministes. Le modèle reçoit d'abord un résumé et des références, puis charge les détails nécessaires.

## Première mission candidate

Améliorer dans HQ l'affichage du statut réel d'une exécution : état lisible, dernière mise à jour, résultat ou blocage, et distinction entre « arrêt demandé » et « arrêté ». Le périmètre exact sera fixé sur les routes réellement disponibles une fois le connecteur qualifié. Cette mission utilise l'orchestration et améliore immédiatement le pilotage de la mission suivante.

Acceptation : accessible depuis la mission, aucune réussite simulée, erreur de connexion intelligible, aucune confusion entre état demandé et observé, vérification desktop/mobile et tests adaptés. Une seule branche candidate, sans modification du déploiement actif pendant le développement. La référence de départ et le diff doivent être traçables, y compris les changements locaux déjà présents.

## État au changement de priorité

### Avancement vérifié après cette décision

Le dossier de mission durable et interactif est livré dans HQ v13. Le lancement natif reste à qualifier : la mission créée ne vaut pas preuve d'exécution. Le challenge d'autorisation Board du CLI Paperclip a expiré sans approbation ; aucun accès n'a été accordé. Cette autorisation reste distincte de la connexion Claude.

Le socle de validation du futur travail des agents dispose maintenant d'un export de développement distinct de l'export de déploiement : sources, tests et fixtures synthétiques, sans mémoire opérationnelle ni dépendances locales. Sur le VPS, l'image candidate Node 22 exécute les contrôles sans réseau, sans volumes opérationnels et sans comptes de modèles. Résultat : 3 934 tests réussis, deux ignorés ; TypeScript, lint et smoke:joris passent. TypeScript nécessite un heap supérieur aux 512 Mio initialement essayés ; la limite retenue est 1 536 Mio dans un conteneur limité à 2 Gio. Les conteneurs de contrôle sont supprimés après chaque exécution.

L'arrêt du conteneur exclusif Claude a été vérifié avec un processus synthétique et son enfant détaché : aucun enfant repris après redémarrage. Cela qualifie une récupération opérateur, pas encore l'annulation native Paperclip. Le service HQ actif reste inchangé pendant ces essais.

La prochaine preuve reste une petite modification par le premier exécutant, suivie d'une validation isolée et d'une revue indépendante. Les connexions supplémentaires et la finition générale attendent ce parcours réel. Les informations historiques ci-dessous décrivent le point de départ.

La compilation de production passe également dans cette même image isolée, en 40 secondes. Les 1 072 fichiers exportés ont été vérifiés par leurs empreintes après transfert. Aucun de ces contrôles ne constitue encore une mission native exécutée par un modèle.

Le lot opérateur Memex est développé, testé et désactivé par défaut. La qualification isolée Linux de la nouvelle image passe ; cette image n'est pas encore celle du service actif. HQ a une suite complète de 3 926 tests réussis, deux ignorés ; typecheck, lint, build et smoke:joris passent. Les services existants restent actifs. L'orchestration native de la première mission n'est pas encore prouvée. L'accès board Paperclip et le raccordement effectif des exécutants restent à qualifier.

L'audit source confirme que le transfert HQ existant crée une issue backlog sans agent et annonce `executionRequested:false`. Ce n'est pas encore un lancement. Il faut ajouter affectation contrôlée (qui peut déjà réveiller l'agent, donc pas de double wakeup), liaison du run, réconciliation et arrêt observé. Le parcours de création de mission actuel est également à compléter pour une mission de développement durable. La connexion OAuth Claude n'est pas une autorisation board pour HQ.

Premier correctif du chemin critique effectué : le dispatcher reconnaît une origine publique explicitement configurée derrière le proxy, avec comparaison stricte et refus des en-têtes forgés. 12 tests ciblés et TypeScript passent ; lint, build et smoke:joris repassent après cette modification. Le correctif est local, pas encore déployé, et ne transforme pas un transfert backlog en lancement d'agent.
