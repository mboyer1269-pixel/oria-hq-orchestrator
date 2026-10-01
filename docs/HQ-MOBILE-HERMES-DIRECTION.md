# HQ mobile — espace de travail agent

Recherche du 30 septembre 2026. Proposition de maquette, aucune intégration Hermes exécutée ou déployée.

## Ce que les sources établissent
La documentation actuelle de NousResearch/hermes-agent décrit un serveur API avec outils exécutés sur son hôte, des événements de progression, des conversations conservées côté serveur via Responses et une interface dashboard. Elle décrit aussi un sélecteur de modèles par fournisseurs configurés et des modèles auxiliaires distincts. Ces capacités sur main ne prouvent pas leur présence dans notre version VPS.

Sources :
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/api-server.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/configuring-models.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/web-dashboard.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/open-webui.md

Un outil terminal ou navigateur dans une API ne prouve pas l'existence d'un terminal interactif distant ou d'une vue navigateur contrôlable. Ces transports restent à qualifier. Pas de nouvelle affirmation sur Codex App Server dans cette recherche.

## Concept mobile
Une mission, un espace de travail persistant, plusieurs vues : Discussion, Résultat, Activité ; Outils ouvre navigateur, terminal et fichiers à la demande. Sur téléphone une seule vue occupe l'écran, jamais trois colonnes réduites. Sur grand écran, panneaux côte à côte. L'en-tête conserve mission, état de connexion et exécutant. Le retour à la conversation conserve sélection et position.

Exemple : depuis Aujourd'hui, ouvrir une mission, demander une correction, ouvrir son aperçu, pointer une zone et revenir au fil avec la référence attachée. Ouvrir le terminal montre la session de CETTE mission, pas le shell administrateur du VPS. Observer les sorties et saisir une commande sont deux capacités distinctes, avec périmètre et attribution explicites. Une commande humaine et un agent ne doivent pas écrire simultanément sans coordination.

Direction utilisateur confirmée depuis cette recherche : Hermes est l'interlocuteur quotidien et l'orchestrateur cible; OpenHands est son exécutant de développement délégué. HQ reste propriétaire des missions et autorisations. Ce positionnement ne prouve pas le raccordement de l'installation actuelle. Le sélecteur sépare exécutant, fournisseur et modèle ; modèles disponibles après vérification du compte seulement. Changement de modèle appliqué au prochain tour ou à une reprise sûre, avec confirmation de son effet ; aucune migration magique de processus ou de contexte entre moteurs.

## Persistance et limites
Fermer le téléphone ne doit pas commander l'arrêt de la mission. Après reconnexion, relire l'état canonique et reprendre les événements avec curseur/idempotence ; connexion perdue n'est pas mission échouée. Aperçu web et navigateur d'agent sont distincts. Authentification HQ côté serveur, connexions liées au workspace/mission, aucun secret fournisseur dans le client, aucune exposition brute du terminal ou de l'administration Hermes. Accès et écritures à qualifier séparément.

## Pédagogie et coût
Une action affiche ce qu'elle fait, son résultat et une explication facultative. Navigation, changement de panneau et aides statiques sans appel LLM. Modèles auxiliaires et gratuité non présumés : afficher usage connu, inconnus et limites réelles. Pas de répétition de toute la conversation à chaque clic.

## Validation avant construction
Prototype indépendant avec démonstrations étiquetées, pas connexion réelle. Scénarios : téléphone portrait, clavier virtuel, faible réseau/reconnexion, mission poursuivie hors écran, passage discussion/aperçu/terminal, modèle indisponible, conflit prise de contrôle. Ensuite inventaire version/capacités de notre Hermes et essai d'adaptateur isolé avant adoption. Ne pas ajouter un second orchestrateur ou remplacer la première mission OpenHands en cours.
