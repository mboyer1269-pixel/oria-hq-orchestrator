# Maquette mobile HQ — recette et validation visuelle

Livraison Antigravity `d821773`, branche isolée `antigravity/hermes-discuter-atelier`. Prévisualisation locale sur le poste de développement : `http://localhost:3337/hq/hermes-cockpit`. Aucun branchement productif n'est démontré par cette maquette.

## Résultats contrôlés par Codex

- 33 tests ciblés : 33 succès, zéro exclusion, 0,66 s.
- Navigateur réel à 390 × 844 : largeur utile et largeur du document 375 px, aucun débordement horizontal.
- Aujourd'hui : champ entre 406 et 472 px; actions entre 486 et 566 px; prochaine action visible dans le viewport.
- Discuter : champ et bouton Envoyer entre 797 et 833 px.
- Une directive « Créer un filtre Montréal pour les prospects de démonstration » crée la mission de démonstration `mis_demo_mup836j2_edb0`.
- La même identité et le même objectif sont présents dans Atelier. Le brouillon saisi dans Discuter reste présent au retour depuis Atelier.
- La bascule de présentation par URL, qui faisait perdre la mission, est supprimée. La page possède une présentation responsive unique sans doubler le shell partagé.
- Les modèles sont explicitement non connectés; les résultats et étapes simulés sont identifiés. Une capture n'atteste aucun conteneur, abonnement ou coût réel.

Captures locales : `proofs/delegation/2026-10-01-hq-mobile-aujourdhui.png`, `2026-10-01-hq-mobile-discuter.png`, `2026-10-01-hq-desktop-discuter.png`.

## Validation encore requise

La proposition a été montrée à Michael, avec une demande de validation visuelle avant intégration. Aucune approbation n'a encore été reçue à cette rédaction. Antigravity a reçu l'instruction de geler ce lot sans ajouter de fonctionnalités.

Le clavier logiciel d'un appareil physique, la reprise après rechargement et les événements du backend réel ne sont pas qualifiés par cette recette. La continuité vérifiée ici concerne les vues de la session de démonstration. L'intégration doit conserver le registre canonique HQ et les permissions réelles, sans reprendre les données simulées comme des états de production.
