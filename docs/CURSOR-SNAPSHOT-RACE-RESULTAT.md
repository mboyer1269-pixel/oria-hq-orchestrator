# Course des répertoires du snapshot — résultat

30 septembre 2026. Base `origin/codex/integrated-qualification` à `d7f563d4a6c510a28ef3576e985f47ea10fc8a66`. Branche `cursor/snapshot-parent-race`. Le lot `cursor/operator-inspect` n'est pas modifié. Aucun fichier fournisseur, aucune UI, aucune mémoire, aucun déploiement, aucune fusion.

## Ce qui était ouvert

`checkedFile` ouvrait le fichier final avec `O_NOFOLLOW`, mais chaque répertoire parent était encore jugé par `lstat` sur le chemin. Remplacer ce répertoire par un lien, entre ce contrôle et la lecture, faisait suivre le lien. Le descripteur final ne voyait alors qu'un fichier régulier hors de la racine.

Reproduction déterministe, avant correctif, sur le même module : le second `lstat` de `src/nested` renvoie encore le répertoire réel, puis le répertoire est renommé et remplacé par un lien vers un arbre extérieur. `exportDevelopmentSnapshot` réussit.

```
{"exportResult":{"files":9,"excluded":0},
 "exportedBytes":"OUTSIDE-SENTINEL\n",
 "nestedIsSymlink":true,
 "destinationCreated":true}
```

Ce n'est pas un benchmark aléatoire. Le remplacement est fait sur le retour du `lstat` qui validait le répertoire.

## Correctif

Node n'expose pas `openat`. Sur Linux, le parcours ouvre `/proc/self/fd/<descripteur>/<nom>` avec `O_NOFOLLOW` (et `O_DIRECTORY` pour un parent). Le nom est cherché dans l'inode déjà tenu. `..` et `.` sont refusés avant cet appel. Le chemin relu du descripteur doit rester sous la racine ouverte. Ailleurs que Linux, ou sans `/proc/self/fd`, l'export échoue au lieu d'employer l'ancien parcours.

Une erreur après création du dossier de destination le supprime. S'il reste, la fonction lève `Development snapshot failed and left an unusable destination` et ne retourne pas de succès. Elle ne prétend pas survivre à un arrêt brutal du processus.

## Commandes et résultats

```sh
node --test deploy/hq-pilot/development-snapshot.test.mjs
```

9 tests, 0 échec, 0,229 s. Les 5 tests déjà présents passent encore. Les ajouts couvrent :

| Cas | Résultat observé |
| --- | --- |
| Lien de répertoire et lien de fichier déjà en place | refus `/Symlink/`, destination absente |
| `src/nested` remplacé par un lien après l'ouverture de son descripteur | refus `/Symlink/`, destination absente, octets extérieurs inchangés |
| L'entrée `nested` devient un lien après l'ouverture de `src`, avant sa recherche | refus `/Symlink/`, destination absente, `OUTSIDE-SENTINEL` non copié |
| `src/example.test.mjs` remplacé par un lien après l'ouverture de `src` | refus `/Symlink/`, destination absente, fichier extérieur inchangé |
| Fichier suivi puis supprimé | exclusion `deleted_working_file`, absent de l'export, voisin exporté |
| Échec injecté pendant la copie | exception `injected copy failure`, destination absente, source inchangée |
| Même échec alors que `fs.rmSync` est neutralisé | exception `unusable`, pas de manifeste, pas de retour succès |
| Contenu normal | octets exportés égaux à la source |

La neutralisation de `fs.rmSync` force la branche d'échec du nettoyage. Ce n'est pas un refus du noyau.

## Coût sur le même jeu

308 fichiers (300 fichiers générés identiques plus les fichiers exigés du fixture), 2 tours d'échauffement, puis 15 mesures alternées de `planDevelopmentSnapshot` sur le même arbre. Les deux durées incluent `git ls-files`.

| | min | médiane | max | moyenne |
| --- | --- | --- | --- | --- |
| Avant | 9,090 ms | 10,277 ms | 12,638 ms | 10,410 ms |
| Après | 7,174 ms | 8,344 ms | 8,979 ms | 8,160 ms |

Écart de médiane : −1,933 ms sur cette machine. Ce n'est pas un objectif de performance et ce n'est pas généralisé. L'ancien code faisait deux `lstat` par composant puis une ouverture ; le nouveau ouvre chaque répertoire une fois. Le coût ajouté des descripteurs n'a pas augmenté la médiane de ce jeu.

## Limites

- Garantie limitée à Linux avec `/proc/self/fd`, `O_NOFOLLOW` et `O_DIRECTORY`. Pas de repli silencieux.
- Un point de montage posé sur un vrai répertoire n'est pas distingué d'un répertoire. Le code ne le prétend pas.
- L'inventaire vient encore de `git -C <chemin>`. La racine est épinglée par descripteur juste avant. Si ce chemin est remplacé ensuite, la liste et l'arbre épinglé peuvent diverger : un nom lien est refusé, un nom absent est `deleted_working_file`. Les octets de l'arbre étranger ne sont pas lus à travers le chemin remplacé.
- Un descripteur dont le chemin sort de la racine, y compris après un renommage, est refusé avec l'erreur de lien. Le test qui déplace `nested` hors du dépôt observe ce refus, pas une lecture du lien.
- Un `kill` pendant la copie peut laisser un dossier partiel. Le chemin d'erreur, lui, ne retourne pas de succès.
- La suite Python de l'hôte n'a pas été rejouée : ces fichiers ne sont pas dans ce diff.

Relecture du 30 septembre, sans changement de mécanisme : `node --test deploy/hq-pilot/development-snapshot.test.mjs` donne 9 tests, 0 échec, 0,204 s.

## Hypothèse qui invaliderait la conclusion

La conclusion est étroite : sur ce Linux, remplacer un répertoire parent par un lien symbolique ne fait plus exporter les octets étrangers. Elle tomberait si `/proc/self/fd/<descripteur>/<nom>` avec `O_NOFOLLOW` suivait quand même un lien, ou si `readlink` de ce descripteur restait préfixé par la racine source alors que l'inode lu est un arbre étranger. Le cas déjà connu qui la ferait tomber sans contredire les tests actuels : un point de montage, donc un vrai répertoire et non un lien, posé sur une entrée après l'ouverture du parent. `O_NOFOLLOW` ne le refuse pas. Aucun test ici ne monte un système de fichiers. Les substitutions exercées sont des liens et un renommage, séquencés dans le processus au bord de `openSync`, pas deux processus concurrents.

## Contrat Hermes, revue non faite

Direction retenue, non implémentée dans ce lot : ORIA héberge HQ ; Hermes est l'interlocuteur quotidien et le chef orchestrateur ; OpenHands est l'outil de développement délégué ; HQ garde les missions, les permissions et les preuves. Deux vues, Discuter et Atelier, portent la même mission. La maquette Antigravity attend une validation utilisateur. Elle n'est pas construite ici.

L'adaptateur Hermes vers une mission HQ/OpenHands appartient à Claude. Aucun second adaptateur n'est ajouté.

La revue en lecture seule de ce contrat n'a pas eu lieu : l'artefact n'est pas dans cette branche ni sur les branches distantes présentes après `git fetch` (`main`, `codex/cursor-recovery-handoff`, `codex/integrated-qualification`, `cursor/operator-inspect`, `cursor/snapshot-parent-race`). `integrations/` ne contient pas Hermes. `docs/PREMIERE-MISSION-HQ.md` est un mandat de première mission, pas ce contrat. La correction du snapshot n'attend pas cet artefact.

Quand le contrat sera lisible, la revue devra trancher cinq points sans les inventer : une seule identité de mission, l'autorisation qui permet l'action, le refus d'un doublon, la reconnexion à la mission déjà ouverte, et un résultat incertain qui ne devient pas un succès. Aucune de ces conclusions n'est tirée ici.
