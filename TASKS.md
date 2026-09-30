# Tâches ORIA HQ constructeur

État au 30 septembre 2026. Référence : [plan constructeur](PLAN-HQ-CONSTRUCTEUR.md). Une case cochée désigne le livrable précis, pas l'achèvement du produit.

## Implémenté ou qualifié dans un périmètre borné

- [x] Documenter le choix OpenHands SDK, les frontières HQ/Memex et le contrat de mission.
- [x] Préparer et vérifier les dossiers et les identités de source avant lancement.
- [x] Implémenter consommateur hôte, réservation durable et refus des doublons.
- [x] Implémenter supervision, deadline partagée, transport de permissions et refus par défaut.
- [x] Implémenter passerelle/relai fournisseur et rapports de réconciliation sans relance aveugle.
- [x] Qualifier des parcours synthétiques et scénarios de panne ; conserver leurs limites dans les rapports.
- [x] Fournir un paquet hôte reproductible avec manifeste et exclusions.
- [x] Fournir scripts et qualifications du contexte Memex et de la contribution gouvernée.
- [x] Fournir adaptateur Antigravity expérimental et tests de contrat.
- [x] Documenter le candidat staging, distinct de l'application active.
- [x] Fournir une inspection opérateur sans effet depuis un checkout Linux (`operator_status.py`). Elle ne prouve ni l'authentification fournisseur, ni Docker, ni une mission réelle.

## À terminer avant de déclarer l'atelier utilisable

- [ ] Finaliser l'authentification fournisseur officielle et prouver son usage depuis le runner autorisé.
- [ ] Reconstruire un ensemble cohérent HQ/bridge/runner avec les derniers correctifs, config et montages protégés.
- [ ] Vérifier depuis HQ authentifié préparation, confirmation, lancement durable et état visible d'une mission réelle.
- [ ] Obtenir une modification utile en copie isolée, tests pertinents et aperçu essayable ; rattacher les preuves à la version exacte.
- [ ] Réaliser une revue indépendante du changement et tester le parcours réel de décision des permissions.
- [ ] Qualifier interruption, déconnexion, panne hôte/redémarrage et réconciliation des effets avant reprise réelle.
- [ ] Raccorder Antigravity à une mission complète avec contexte, résultat et annulation observés.
- [ ] Confier une amélioration d'ORIA HQ à l'atelier, puis livrer après revue avec retour arrière vérifiable.
- [ ] Mesurer durée, consommation disponible, interventions et reprises sur des missions comparables ; conserver les coûts inconnus comme inconnus.

## Publication et exploitation

- [x] Séparer ce dépôt d'intégrations des dépôts produit HQ et Memex Core.
- [x] Exclure clés, environnements, caches et artefacts runtime de la publication.
- [ ] Qualifier une installation durable de la version publiée ; la publication GitHub ne déploie aucun service.
