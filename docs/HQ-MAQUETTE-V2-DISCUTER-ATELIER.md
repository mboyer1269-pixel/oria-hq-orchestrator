# ORIA HQ — maquette V2 à présenter avant intégration

## Décision de Michael

Michael a examiné la première maquette et demande une révision, pas son intégration. Il veut une interface quotidienne simple, inspirée de l'organisation conversation/travail de ChatGPT, avec Hermes comme assistant permanent, choix des modèles et artefacts plutôt que longs paragraphes. La V1 d821773 reste une référence préservée. La construction de la V2 isolée est autorisée; son intégration au produit attend son accord explicite.

Nom proposé : **Atelier**, dans ORIA HQ. Les deux espaces principaux sont **Discuter** et **Atelier**. OpenHands apparaît comme moteur de réalisation dans les détails de mission, pas comme une deuxième application. Aujourd'hui devient un accueil/reprise léger dans la navigation, sans troisième cockpit concurrent.

## Parcours et design

**Priorité mobile confirmée par Michael :** le téléphone est son usage principal, pas une adaptation secondaire. Dossier vivant, cycle du livrable, composants et preuves sont regroupés derrière un bouton **Mission**, fermé par défaut. Seuls une décision requise ou un incident important peuvent faire apparaître un avis compact dans le fil. Ouvrir/fermer les détails ne change ni mission, ni défilement du fil, ni brouillon. Tester 360×800 et 390×844, zones tactiles confortables, safe areas, saisie avec clavier virtuel et réseau interrompu; distinguer simulation de viewport et essai sur appareil physique.

- Navigation compacte : nouveau fil, Discuter, Atelier, projets/récents, connexions. Sur mobile : tiroir et bascule claire entre les deux espaces; une surface de travail à la fois.
- Discussion : un fil lisible, une saisie persistante, réponses courtes lorsque possible. Les détails importants restent accessibles; aucun tronquage qui cache un risque ou un résultat.
- Barre Hermes : assistant stable; modèle et type d'accès visibles séparément. Changer le modèle n'efface ni fil ni mission. Pendant une exécution, le choix s'applique à la prochaine demande; pas de changement silencieux du travail lancé.
- Artefacts : plan éditable, aperçu, fichiers/diff, résultats de tests, décision attendue. Une carte compacte dans le fil ouvre une surface dédiée; panneau latéral sur ordinateur, plein écran réversible sur mobile. Fermer revient au même message, sans perdre le brouillon. Rien n'est simulé comme exécuté réellement.
- Atelier : une mission, son résultat attendu, son prochain geste et ses artefacts. La chronologie, les preuves et les explications pédagogiques s'ouvrent à la demande. Navigateur/terminal ne sont actifs que si la session existe; sinon raison claire.
- Direction visuelle : reprendre les composants et tokens ORIA utiles; hiérarchie typographique nette, surfaces calmes, un accent, peu de bordures/cartes imbriquées. Pas de grand tableau de KPI, de slogans, de jargon d'infrastructure ou de badges décoratifs. Le caractère distinctif vient de la continuité fil → artefact → mission. Composer et action principale visibles sur téléphone; clavier, focus et réduction des animations pris en compte.

## Modèles et accès — prototype honnête

Le sélecteur contient recherche, favoris et trois catégories : **Gratuits**, **Mes abonnements**, **API à l'usage**. Chaque entrée distingue modèle, fournisseur, capacités requises, disponibilité et tarif/limite connue ou inconnue. Aucun accès réel prétendu dans la maquette. Les connexions se simulent sans saisir ou conserver une vraie clé.

Politique proposée : privilégier les modèles gratuits compatibles avec la tâche, puis les abonnements effectivement connectés selon une préférence explicite. Une API payante reste exclue sans autorisation de dépense. Si aucun candidat ne convient, proposer une décision au lieu de dégrader silencieusement la tâche. Catalogue daté/rafraîchissable, pas de liste éternelle ni de promesse « tous les modèles gratuits ». Afficher modèle demandé et modèle réellement utilisé quand le backend le connaît. Un quota absent est inconnu, pas illimité. Un abonnement n'est pas un crédit API OpenRouter.

OpenRouter documente un catalogue de modèles et un routeur gratuit qui filtre les capacités puis choisit aléatoirement : ce n'est pas un classement qualitatif. Les modèles gratuits ont des limites et une disponibilité variable. Hermes documente OpenRouter et le fournisseur openai-codex par connexion officielle; la compatibilité exacte de la version installée et les accès du compte restent à vérifier. Le routeur HQ existant doit rester unique.

Sources consultées le 1 octobre 2026 :
- https://openrouter.ai/docs/quickstart
- https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/routers/free-router.mdx
- https://github.com/OpenRouterTeam/docs/blob/main/api_reference/limits.mdx
- https://hermes-agent.nousresearch.com/docs/integrations/providers

## Répartition complémentaire

**Antigravity :** conserver le backend isolé et créer un sous-agent constructeur UI V2 sur une branche distincte issue de la maquette existante. Réutiliser les composants; aucun fichier backend commun. Livrer une maquette locale interactive, captures mobile/ordinateur, actions et états documentés. La revue UI est distincte; ne pas intégrer.

**Claude Code :** sonde déjà livrée ac6378a, non encore acceptée par Codex. Mandat suivant documentaire ciblé : vérifier dans les sources officielles et la version Hermes épinglée le choix de modèle par session/demande, la connexion OpenRouter et abonnement Codex, les limites observables et les points de raccordement au routeur existant. Livrer un petit contrat données/états pour la maquette, sans toucher au runtime, secret ou code des autres.

**Cursor :** conserver la recette backend remise; revue complémentaire de la politique de choix des modèles et de ses états UI, sur le routeur existant. Identifier les écarts nécessaires, sans coder un second routeur. Fournir scénarios falsifiables : quota épuisé, gratuit indisponible, modèle sans outils, catalogue périmé, changement de modèle pendant mission, refus payant, retour d'artefact et reconnexion. Pas de promesse d'appel réel depuis la maquette.

**Codex :** vérifier les remises, éviter les écritures concurrentes et présenter la V2 essayable à Michael. Quatre scénarios de présentation : question simple; choix d'accès/modèle; directive transformée en mission; ouverture et annotation d'un artefact avec retour au fil. Ensuite seulement demander la validation d'intégration.

## Acceptation de la maquette

À 390×844 et sur ordinateur : aucune perte du fil/mission/brouillon lors des bascules; tous les boutons ont un effet démontré ou une indisponibilité expliquée; navigation clavier et retour mobile corrects; état démo évident; aucun secret stocké; aucune requête modèle ni facture. Rapport court, URL locale, commit et captures. Une maquette validée ne prouvera pas le branchement production.
