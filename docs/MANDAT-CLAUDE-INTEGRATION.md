# Mandat Claude Code — rendre le parcours réel exécutable

## Recentrage : une livraison, un responsable, une preuve

Priorité : terminer le raccordement opérateur vers le worker OpenHands existant,
sans ajouter de moteur d'orchestration. Claude réalise le changement ; Codex
contrôle le diff et les preuves ; l'utilisateur autorise les nouveaux accès.
La mission autonome depuis HQ demeure le jalon produit, distinct de ce lot.

Périmètre initial précis : `consume_pending.py`, `prepare_host_job.py`,
`run_host_job.py`, leurs contrats de configuration et tests associés. Avant
modification, tracer le chemin réel depuis la découverte d'une mission jusqu'à
`run_permission_job`. Identifier le refus actuel et le passage de paramètres
manquant. Le code du worker/proxy déjà qualifié doit être réutilisé.

Livraison attendue : un chemin opérateur explicitement configuré peut transmettre
la politique fournisseur approuvée au worker sans changer le comportement par
défaut. Un profil absent, altéré, incohérent ou non autorisé reste refusé avant
effet. Aucun réseau ou compte réel n'est activé pour obtenir un test vert.
Si les contrats existants ne permettent pas ce changement sans nouvel accord,
indiquer exactement la condition manquante et arrêter ce lot.

Validation utile : configuration par défaut inchangée, profil explicitement
autorisé transmis correctement, profil modifié refusé, budget commun conservé,
erreur incertaine sans relance aveugle. Puis suite existante adaptée au changement.
Ne pas réécrire les tests de toutes les autres briques ni fabriquer une preuve
d'authentification avec un adaptateur simulé.

Les 124 tests hôte ont déjà passé sur le VPS Linux sans exclusion. Recréer un
miroir Docker complet pour refaire cette preuve n'est pas la priorité. Docker
ne reproduit pas à lui seul le noyau, le réseau, les droits ou les comptes du VPS.
Les portes d'authentification ne sont pas déclarées vulnérables sans constat.
Paperclip reste hors de ce lot : aucun service de réconciliation supplémentaire
sans démontrer qu'il appartient au parcours effectivement retenu.

La première mission réelle utilisera ensuite le chemin qualifié, les accès
explicitement accordés et un dossier Memex confirmé. Sa sortie sera un diff,
des tests, une revue indépendante et un résultat essayable. Les coûts inconnus
restent inconnus ; aucun engagement de zéro bug ou de perfection mathématique.

## Résultat attendu

Faire progresser le chemin critique qui transforme une mission confirmée dans
HQ en travail OpenHands réel, puis en changement testé et révisable. Livrer un
changement concret de raccordement, pas un nouveau catalogue ni une nouvelle
architecture. Ne jamais présenter « sans faille » comme une propriété démontrée.

## Contexte vérifié au départ

- Ce dépôt contient le runner, les scripts et les preuves d'intégration ; le
  produit HQ reste dans `C:/Users/micha/Dev/Oria.HQ` et Memex dans
  `C:/Users/micha/Documents/memex-core`.
- Claude Code local est connecté. Cela ne prouve pas la connexion du conteneur
  Claude dédié sur le VPS, dont le dernier statut était déconnecté.
- La chaîne synthétique et les 124 tests du runner sous Linux passent ; aucune
  mission authentifiée complète avec revue indépendante n'est encore prouvée.
- Le worker possède un chemin opt-in vers le proxy contrôlé ; l'entrée opérateur
  n'active pas encore ce chemin. Le conteneur de mission n'a pas d'accès compte.
- Le consentement OAuth VPS et la publication gouvernée du cadre Memex restent
  en attente. La présente délégation n'accorde pas ces autorisations.

## Première livraison autonome

1. Lire le plan, TASKS.md, les derniers handoffs AgentMemory si disponibles,
   PROVIDER-INTEGRATION-GAPS.md, PROVIDER-POLICY.md et le code réel du runner.
2. Identifier le plus court chemin manquant entre l'entrée opérateur et le
   worker déjà qualifié. Vérifier les invariants : politique approuvée identique,
   identité de mission/projet, durée commune, permissions explicites, échec
   visible et absence de relance automatique d'une action incertaine.
3. Choisir et expliquer brièvement un seul changement qui lève un obstacle réel.
   L'implémenter localement dans ce dépôt avec une configuration inactive par
   défaut. Si ce changement nécessite une décision sur les identifiants non
   vérifiable sans consentement, ne pas inventer le mécanisme : livrer le constat
   exact et les points de branchement plutôt qu'une fausse intégration.
4. Exécuter les tests concernés, puis les tests du runner si le contrat change.
   Distinguer tests simulés, tests Linux et exécution réelle. Une nouvelle suite
   n'est justifiée que par un défaut ou un invariant précis.
5. Produire `docs/CLAUDE-INTEGRATION-RESULTAT.md` : problème, solution retenue,
   fichiers modifiés, commandes et résultats, limites, prochain blocage concret.

## Périmètre et coordination

Écriture autorisée dans ce dépôt uniquement. HQ et Memex peuvent être consultés
en lecture pour comprendre les contrats ; ne pas modifier leurs branches.
Préserver les changements d'autrui. Ne pas committer, pousser ou déployer dans
cette mission : Codex fera la revue indépendante du diff avant publication.
Ne pas lancer d'autres agents ni d'autres modèles depuis cette session.

Ne pas lire, copier, imprimer ou enregistrer des secrets. Ne pas transférer le
compte local, ouvrir de port public, activer le consumer, accorder de permission
outil automatiquement, publier de mémoire opérationnelle ou modifier le VPS.
Conserver les garde-fous existants. Les fichiers de compte et sessions restent
hors des dépôts, du dossier de mission et de la mémoire partagée.

## Efficacité et sortie

Une passe ciblée ; réutiliser le code et les preuves existants. Aucun nouveau
framework. Pas de refonte UI. Pas de recherche générale sur le marché.
Séparer clairement fait établi, hypothèse et travail non effectué. Arrêter après
une livraison cohérente ou un blocage précis nécessitant une autorisation ; ne
pas remplacer le résultat demandé par des travaux périphériques.

Le succès de ce mandat n'est pas la finalisation globale de HQ : c'est un
obstacle réel retiré et revu sur le chemin vers la première mission utilisable.
