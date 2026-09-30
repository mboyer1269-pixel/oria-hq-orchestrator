# Claude — livrer une preuve du parcours opérateur

## Objectif concret

Faire passer une mission de qualification par le vrai consommateur et l'entrée
opérateur jusqu'au worker OpenHands, avec politique explicitement autorisée,
état durable et reprise refusant un second lancement. Réutiliser le harnais et
l'adaptateur synthétique existants : aucune requête modèle ni accès de compte.
Cette livraison prouve un raccordement ; elle ne sera pas appelée mission
autonome réelle. Le prochain jalon produit reste la modification de code avec
compte autorisé, tests, revue et aperçu.

## Revue indépendante déjà effectuée

Ton lot précédent contient 137 tests au total. Sous Windows : 114 réussis et
23 ignorés. Codex a copié le lot dans un dossier distinct et exécuté sur le VPS
Linux `python3 -m unittest discover -p "test_*.py"` : 137 réussis, zéro ignoré,
sortie 0. Les exclusions de plateforme sont donc levées pour cette version.
Ne pas répéter une exploration générale ni réimplémenter le proxy.

La revue du code identifie les points restants :

1. `permission_worker.run_permission_job` accepte encore `gateway_root` sans
   `authorization`. Rendre l'autorisation obligatoire pour tout parcours
   fournisseur, qualification comprise. Vérifier aussi que le chemin effectif
   est celui de l'autorisation et refuser les combinaisons incohérentes. Aucun
   effet Docker, socket ou transition avant ces vérifications.
2. `prepare_host_job` valide la forme de l'autorisation, mais pas le dossier
   `gatewayRoot` ni sa séparation avant de créer le travail. La voie de
   préparation CLI peut donc laisser un dossier partiel qui sera ensuite refusé
   par `load_configuration`. Valider les prérequis hôte avant ces créations ;
   réutiliser les contrôles existants, sans multiplier les implémentations.
3. `qualify_hq_postgrest.py --synthetic-provider` appelle directement le worker.
   Ce test ne prouve pas le raccordement opérateur que tu viens d'ajouter.
   Ajouter un mode ciblé passant par le consommateur/préparation/entrée réels.
   Fournir une autorisation protégée explicite au harnais ; aucune exemption de
   validation parce que c'est un test, aucun mock de la fonction de passage.

## Critères de livraison

### Défi supplémentaire demandé par l'utilisateur : prouver la résistance

La livraison doit montrer trois scénarios observables, pas seulement du code :
un lancement nominal ; une politique altérée refusée avant effet ; une réponse
de lancement perdue suivie d'une nouvelle demande identique. Dans ce dernier
cas, vérifier l'effet déjà produit avant toute reprise et prouver qu'aucun second
conteneur n'est créé pour la même mission. Si l'état ne peut être établi,
le résultat correct est une demande de réconciliation explicite, pas une relance.

La panne doit être injectée uniquement dans le harnais de qualification, sans
modifier la production. Rapporter les observations avant/après : nombre de
conteneurs créés pour cette mission, transitions persistées, appels répétés et
sortie obtenue. Ne pas déduire ces observations d'un simple test vert.

Contrainte d'ingéniosité : résoudre avec le minimum de mécanismes nouveaux.
Réutiliser les contrôles existants et expliquer toute nouvelle abstraction.
La qualité du résultat sera jugée sur la chaîne réellement parcourue, la
compréhension de l'échec et la possibilité de reprendre, pas sur le volume
de code, le nombre de tests ajoutés ou une garantie fictive de zéro défaut.

- Configuration absente : comportement par défaut conservé.
- Profil, empreinte ou chemin incompatibles : refus avant effet.
- Configuration complète de qualification : un seul lancement observable via
  le consommateur réel, entrée opérateur, worker, conteneur et état HQ durable.
- Après nouvelle invocation / réponse incertaine : pas de deuxième conteneur
  pour la même mission ; conserver les preuves, exiger réconciliation si doute.
- Le budget partagé et les demandes d'autorisation outil restent inchangés.
- Suite Linux sans exclusions et preuve connectée ciblée, avec commandes,
  version des sources et limites dans un rapport court.

## Travail et limites

Éditer uniquement ce dépôt. Consulter HQ/Memex en lecture si nécessaire.
Tests Linux autorisés par SSH avec la connexion VPS existante, exclusivement
dans un NOUVEAU sous-dossier de `/opt/oria-openhands-qualification`.
Les ressources Docker doivent être nommées/étiquetées pour la qualification,
temporaires, sans port publié ni volumes opérationnels. Réutiliser les images
épinglées existantes ; ne pas installer les fichiers dans le runtime actif.
Ne pas modifier le proxy ou les services en production, ni la base HQ existante.
Ne pas lire/transférer des identifiants, publier de mémoire projet, changer le
consentement OAuth ou appeler un modèle supplémentaire.

Ne pas committer/pousser. Ne pas créer de nouveaux agents. Arrêter après la
preuve ciblée ou un blocage concret. Codex fera la revue et la publication.
Pas de perfection prétendue, pas de benchmark inventé, pas de chantier Paperclip.

## Rapport attendu

Créer `docs/CLAUDE-PREUVE-OPERATEUR-RESULTAT.md` : invariant corrigé, fichiers,
résultats exacts, passage réellement exécuté, ressources nettoyées, limites et
prochaine action indispensable. Joindre les sorties utiles sans secrets.

L'accès Linux ne doit pas être une raison de conserver des exclusions Windows.
En revanche, un test passant reste une preuve bornée : il ne rend pas le produit
« mathématiquement prêt », ne démontre pas l'authentification et ne suffit pas
à déclarer une mission réelle réussie.
