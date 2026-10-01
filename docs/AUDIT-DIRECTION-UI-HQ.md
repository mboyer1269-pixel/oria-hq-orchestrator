# ORIA HQ — audit des directions UI

30 septembre 2026. Recherche documentaire ciblée et inspection du code, pas audit exhaustif du marché ni test utilisateur des produits cités. Proposition à valider dans une maquette indépendante avant intégration.

## Références vérifiées
- Linear : objectifs/projets et niveaux de lecture ; https://linear.app/docs/initiatives et https://linear.app/docs/display-options . Retenir la hiérarchie et les vues alternatives, éviter de tout afficher ensemble.
- Lovable : sélection, annotations et commentaires attachés à l'aperçu ; https://docs.lovable.dev/features/preview-toolbar . Retenir pointer puis préciser, distinguer commenter de lancer une modification.
- Devin : exemple documenté de construction depuis une spécification et questions dans la revue liées au code ; https://docs.devin.ai/use-cases/gallery/implement-feature-from-spec . Retenir le lien demande/preuve/revue, sans prétendre avoir testé son interface.
- Google PAIR : explication proportionnée, contrôle et correction ; https://pair.withgoogle.com/guidebook-v2/chapter/explainability-trust/ et https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/ . Retenir une aide contextuelle et les limites explicites. Ne pas afficher de confiance chiffrée arbitraire.
- Documentation UI OpenHands non récupérée lors de cette recherche : aucune nouvelle comparaison visuelle vérifiée à en tirer.

## Directions comparées — jugement de conception
| Direction | Atout | Limite | Décision |
|---|---|---|---|
| Conversation centrale | Expression libre | Décisions et résultats se perdent dans le fil | Assistant contextuel, pas navigation principale |
| Tableau de tâches | Priorités et suivi | Faible compréhension du résultat final | Vue secondaire |
| Graphe permanent d'agents | Dépendances visibles | Bruit visuel, complexité mobile | À ouvrir seulement pour un blocage |
| IDE complet | Contrôle technique | Trop dense pour usage quotidien non expert | Détails avancés |
| Galerie d'aperçus | Résultat concret | Masque les preuves et incertitudes | Étape Essayer, avec preuve attachée |
| Accueil quotidien + dossier de mission | Reprise rapide et continuité | Exige une vraie source d'état | Direction principale |

## Structure retenue pour la maquette
Aujourd'hui : reprise, décisions en attente, idée rapide, changements depuis la dernière visite. Projet : objectif et missions. Mission : objectif, prochaine action, parcours, résultat. Un panneau contextuel commun contient Preuves, Comprendre, Équipe, Historique ; il conserve toujours la mission sélectionnée. Sur mobile, ouverture en panneau plein écran avec retour explicite.

Signature : une ligne de progression fondée sur les livrables et les preuves, avec bifurcation visible seulement lorsqu'une décision est nécessaire. Pas de pourcentage inventé, avatar qui prétend travailler ou animation qui simule une exécution.

Interaction pédagogique : pour chaque décision, présenter Ce qui est proposé / Pourquoi c'est utile / Ce que cela change / Ce qui reste incertain. Explications générales écrites sans modèle ; détails sur le projet tirés des preuves disponibles. Une demande d'explication approfondie est volontaire. Aucune prétention d'exposer le raisonnement interne.

## Correspondance avec le code inspecté
Le dépôt HQ contient déjà missions, activité, approbations, préparation, lancement et récupération. Leur présence ne prouve pas leur qualification opérationnelle.
- home-mission-overview.tsx : filtres, détails et activité, source indisponible distinguée du vide. Réutiliser cette distinction.
- openhands-launch.tsx : avertissement explicite que le démarrage hôte n'est pas raccordé à cet écran ; profil fournisseur interdit dans la confirmation actuelle. Ne pas dessiner Lancer comme une capacité opérationnelle acquise.
- Les routes mémoire, agents, compétences, workflows existent : présence de route seulement, pas preuve d'intégration ou besoin de les exposer au premier niveau.
- AgentMemory est mémoire de développement locale, pas source runtime à afficher aux utilisateurs de production.

## Évaluation de la maquette
Scénarios : reprendre après absence ; transformer une idée en mission ; comprendre une décision ; distinguer terminé de vérifié ; commenter un aperçu ; comprendre une erreur et la prochaine action. Mesurer sans assistance le temps, les erreurs et les hésitations. Cible de conception, non résultat mesuré : identifier prochaine action en dix secondes. Vérifier clavier, mobile, contraste, focus, mouvement réduit. Comparer deux compositions sur les mêmes scénarios, puis choisir avant intégration. Coût modèle nul pour la navigation et les aides statiques ; aucun appel modèle implicite au survol ou à l'ouverture d'un panneau.

## Limites et ordre
Cette recherche ne démontre pas une supériorité sur le marché. Prochaine preuve : prototype essayé par l'utilisateur. Ensuite seulement, raccordement des interactions supportées au backend. Les changements techniques Claude/Cursor continuent indépendamment. Ne pas élargir vers calendrier, CRM ou messagerie générale dans ce lot.
