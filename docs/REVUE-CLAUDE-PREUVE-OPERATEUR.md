# Revue indépendante — preuve opérateur

Codex a rejoué sur Linux les 139 tests (aucune exclusion), puis les qualifications connectées nominale et interruption. Les deux qualifications passent, sans compte fournisseur ni appel modèle. Six fichiers critiques correspondent par SHA-256 aux sources locales. Le nominal atteint execution_finished ; independentValidationPassed reste false, correctement.

## Corrections demandées avant acceptation de la preuve

1. Dans qualify_hq_postgrest.py, vérifier explicitement le code de sortie du consommateur réinvoqué. Une sortie vide accompagnée d'un échec ne démontre pas une réinvocation correcte. Conserver stderr dans le diagnostic d'échec, sans secrets.
2. Capturer les identités exactes du conteneur mission et de la passerelle avant/après réinvocation, puis vérifier leur égalité. Un compte égal à un ne prouve pas l'absence de remplacement. Conserver et comparer l'identité canonique après redémarrage de la base dans qualify_hq_postgrest.mjs ; supprimer toute affirmation non appuyée par une assertion.
3. Renommer honnêtement le scénario actuel : il tue le consommateur dès la création du conteneur. Il prouve une interruption au démarrage et un refus de relance, pas une récupération d'un résultat terminé après perte de réponse.
4. Ajouter une qualification distincte de réponse perdue après exécution terminée : utiliser le vrai parcours existant avec agent synthétique, supprimer uniquement la réception de la réponse dans le dispositif de test, réinvoquer la même demande, vérifier les identités, l'état durable et l'absence de nouvelle exécution. Si le résultat ne peut pas être récupéré, produire un état explicite nécessitant réconciliation ; ne jamais déclarer une validation indépendante ou un succès métier non observés.

## Périmètre du retour à Claude

Corriger ces preuves et leurs diagnostics avec le minimum de code. Réutiliser les mécanismes existants ; aucune nouvelle architecture. Ajouter une assertion négative ciblée montrant qu'un remplacement d'identité ou un échec du consommateur serait détecté. Rejouer les tests Linux pertinents et les qualifications modifiées, puis rendre un rapport factuel avec commandes, résultats et limites.

Les restrictions du mandat précédent restent applicables : qualification isolée uniquement, aucun appel modèle, aucun transfert d'identifiants, aucune modification des services ou bases actifs, aucun commit/push. Ne pas créer d'autres agents. Ne pas transformer cette qualification en promesse de mission autonome réelle. Arrêter au livrable vérifié ou au blocage précisément documenté.
