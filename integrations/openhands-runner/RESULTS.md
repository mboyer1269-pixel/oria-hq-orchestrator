# Vérification HQ → récepteur Python

30 septembre 2026. Parent : Python 3.14.7 Windows, Git local. Sept tests unittest passent, y compris budgets invalides, altération du dossier, mauvais workspace, commit absent et détournement du dépôt par variables Git héritées.

Le script `../export-openhands-fixture.mjs` a utilisé le vrai `createDevelopmentService` et `buildOpenHandsSubmission` du dépôt HQ avec un stockage de test en mémoire. Aucun accès Supabase. Le dossier contient accents et emoji, ainsi qu'un commit créé dans un dépôt dédié sous `.validation`.

Le récepteur accepte cette fixture exacte, vérifie la clé et l'empreinte calculées par TypeScript, puis constate la présence du commit dans le dépôt prévu. Résultat : prepared, executionRequested=false, approvalSatisfied=false. Cela prouve la compatibilité de ce contrat de données, pas un transport réseau authentifié ni une mission exécutée.

Le vérificateur ne modifie pas HEAD, ne vérifie pas encore un checkout de travail propre, ne réserve pas la mission et n'applique pas les budgets à un modèle. Ces étapes restent nécessaires avant le lancement réel.

## Ubuntu VPS
Les sept tests passent aussi avec Python3.12 sur le VPS. Le dépôt synthétique a été transporté par bundle Git (aucun dépôt applicatif ni secret). qualify_fixture.py accepte sur Linux le dossier exact émis sur Windows par HQ, avec le même commit local présent, et retourne prepared/executionRequested=false/approvalSatisfied=false. Aucun checkout applicatif, authentification fournisseur ou exécution modèle testé.

## Dossier vers checkout exact
Treize tests passent sur VPS Ubuntu : six concernent le workspace, dont commit ancien exact, source inchangée, destination existante, commit absent, root source et sousdossier source refusés. qualify_preparation.py passe sur le VPS avec la fixture TypeScript inchangée : dossier accepté, commit exact matérialisé, README attendu présent, Git clean, executionRequested=false et approvalSatisfied=false. La copie de qualification temporaire est nettoyée uniquement par son TemporaryDirectory. Aucune mission modèle exécutée.

## Entrée CLI
16tests locaux passent avec le décodeur borné : Unicode valide, JSON dupliqué à toute profondeur refusé, nonfini/UTF8invalide/surdimensionné refusé. prepare_job.py exécuté localement avec fixtureTS : clone exact propre, sans autorisation ni lancement. Le clone de test reste dans .validation/openhands-cli-jobs pour inspection.

## Reprise de préparation sans écrasement
17testsPASS Windows et Ubuntu. Nouveau testCLI crée checkout, ajoute fichieragent, répète demande : sortie3 preparation_conflict, unseulrépertoire, fichier préservé. SurVPS demande exacte fixtureTS préparée puis relancée : mêmeconflit attendu. ErreursCLI prévisibles renvoient résultatJSON sans stacktrace ni sortieGit brute; aucun retry/destruction automatique. Ce contrôle de destination ne remplace pas une réservation durable de lancement.

## Clone sans destination de publication
18testsPASS Windows et VPSUbuntu. La préparation retire origin aprèscheckout. Le nouveau test confirme aucune remote, aucune base objets alternée, push sansdestination refusé et HEADsourceinchangé. Cela réduit le risque d'envoi accidentel; un agent pouvant reconfigurerGit doit toujours rester confiné sans montage du dépôt source. Les anciennes copies de qualification n'ont pas été modifiées rétroactivement.
