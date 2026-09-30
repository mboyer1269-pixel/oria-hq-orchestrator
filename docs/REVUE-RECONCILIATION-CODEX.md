# Revue indépendante : corrections avant activation

Les 157 tests Linux ont été rejoués par Codex : tous passent. Cela ne couvre pas les défauts suivants, identifiés dans le code livré.

## P1 — identité observée non liée à l'identité canonique

Reproduction directe de decide : claim state=container_created et containerId=A, mission state=created et containerId=B, evidence started=absent : retourne record_cancelled. observe_mission contrôle nom, labels et image, mais pas l'identité du claim. apply_decision envoie ensuite A, ce qui satisfait le contrat HQ malgré l'observation de B. Un conteneur de remplacement portant les mêmes labels ne doit pas justifier la clôture. Vérifier cette liaison avant toute transition et avant nettoyage, y compris pour un claim déjà terminal. Ajouter un test de non-effet démontrant ce cas.

## P1 — contrôle des chemins après effets

main appelle reconcile avant de vérifier root.name et review.parent.name contre launchId. reconcile peut déjà écrire une transition canonique et supprimer une passerelle. Déplacer le contrôle de liaison avant toute transition ou suppression, avec test vérifiant zéro effet pour une configuration pointant un autre lancement.

## P1 — nettoyage permis malgré observation incertaine

Pour un claim terminal, decide retourne already_final avant les vérifications d'identité. reconcile n'exclut du nettoyage que ACTIVE ; unknown et identity_mismatch peuvent donc passer à release_gateway. Le contrat de cette fonction exige pourtant que l'agent soit observé incapable d'agir. Utiliser une liste explicite d'états admissibles et une identité concordante ; les observations incertaines doivent conserver les ressources et expliquer le refus.

## Concurrence à éprouver

La CAS sur l'état ne suffit pas à lier une observation Docker à un start déjà autorisé mais pas encore effectué. Vérifier le cas start_requested, Docker absent à l'observation, création/démarrage concurrent ou conteneur remplacé avant clôture. Ne pas affirmer qu'une enum empêche un hôte de soumettre une observation périmée. Démontrer le mécanisme existant de sérialisation, ou corriger la coordination nécessaire sans relance aveugle. Corriger aussi les affirmations trop fortes du rapport.

## Autonomie et résultat

L'objectif autonome initial reste inchangé. Choisir la correction minimale cohérente, traiter ces invariants sur le vrai chemin et produire les preuves négatives correspondantes. Rejouer la suite Linux et les parcours connectés affectés. Ne pas élargir aux comptes, à la production ou à de nouveaux systèmes. Conserver le travail et les preuves. Mettre à jour le rapport avec les limites réelles ; aucune activation avant revue indépendante.
