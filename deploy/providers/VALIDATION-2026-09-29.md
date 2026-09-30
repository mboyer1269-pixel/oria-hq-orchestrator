# Intégrations fournisseurs — validation du 29 septembre 2026

## Résultat vérifié

| Fournisseur | Installation VPS | Compte | Appel modèle | Pilotage depuis Paperclip |
|---|---|---|---|---|
| Antigravity 1.2.13 | binaire officiel, SHA512 fournisseur vérifié | Google AI Pro ; conditions acceptées explicitement ; collecte facultative désactivée | Réponse réelle validée en JSON, NDJSON corrigé et via notre runner | Point d’entrée préparé et désactivé ; pas encore raccordé |
| Cursor 2026.09.28-64d2043 | distribution officielle, checksum local enregistré | Connexion CLI réussie et persistante | Non validé : sorties vides puis timeout ; plugins synchronisés déclenchent hooks/LSP | Environnement SSH prêt ; agent non enregistré |
| Gemini CLI 0.61.0 | fourni par l’image officielle attestée | Google refuse ce client pour Code Assist individuel et renvoie vers Antigravity | Aucun appel réussi | Non activé ; aucune clé API payante ajoutée |

## Antigravity : preuves et limites

Le runner est exécuté dans un nouveau conteneur non privilégié : utilisateur node, racine en lecture seule, capacités retirées, limite CPU/RAM/PID, répertoire temporaire borné. Seuls le binaire, le module de raccord et le volume de connexion propre à Antigravity sont montés. Aucun socket Docker, variable de base de données ou socket DBus n’est fourni.

Résultat réel du runner : `ok:true`, `providerStatus:SUCCESS`, réponse attendue `ANTIGRAVITY_READY`, durée fournisseur 2,489 s ; 13 800 tokens d’entrée, 196 de sortie, dont 190 de réflexion déclarés, total 13 996. Ces chiffres sont ceux du fournisseur et ne constituent pas une estimation de facturation. Le volume d’entrée justifie de regrouper les tâches utiles plutôt que multiplier les micro-appels.

Une incompatibilité a été détectée : `--disable-slash-commands` annule l’effet de `--mode plan`. L’option incompatible a été retirée, les commandes slash sont rejetées par le prototype et le parseur exige `request-review`. Un résultat fournisseur réussi reste `deliveryVerified:false` : la livraison d’une application exige une validation séparée.

15 tests locaux passent. L’annulation réelle, les refus de permissions et le confinement d’une tâche avec outils restent à qualifier avant activation. Aucun agent autonome Antigravity n’a été ajouté à Paperclip.

## Cursor : cause en cours de qualification

Le profil synchronisé importe des plugins qui lancent des MCP, hooks et serveurs de langage même pour une invite minimale. Une désactivation locale de 134 identifiants MCP observés a supprimé les nouveaux démarrages MCP constatés dans les logs npm du dernier test ; elle ne désactive pas les autres composants des plugins. Aucun réglage cloud n’a été modifié. Les processus enfants du diagnostic ont été arrêtés. Aucun mode `--yolo` utilisé.

## Transport et isolation

Deux runners SSH distincts sont déployés avec homes, workspaces, clés hôtes, clés clients et réseaux de contrôle séparés. Aucune publication de port sur le VPS. Paperclip est relié aux réseaux de contrôle ; PostgreSQL reste sur son réseau interne. Les sorties Internet des fournisseurs ne sont pas limitées par domaine.

Vérifications réelles réussies pour les deux runners : UID 1000, HOME attendu, absence de DATABASE_URL/BETTER_AUTH_SECRET dans le shell distant, racine non inscriptible, refus SSH d’une clé hôte inconnue, transfert tar d’un fichier synthétique depuis le workspace. Cela ne remplace pas un test du helper SSH de Paperclip ni une preuve d’inaccessibilité réseau de la base.

## Autorisation de configuration restante

Le formulaire de création d’environnement est préparé dans HQ et l’option Environments est affichée pour le pilote. Le CLI officiel dispose d’un parcours d’autorisation opérateur qui permet d’enregistrer les clés directement sur le VPS, sans les afficher ou les saisir dans le navigateur. Son accès porte les droits du compte opérateur (30 jours par défaut, non limité à une organisation par le seul argument company-id). Une demande explicite d’autorisation temporaire a été présentée ; l’accès devra être révoqué après configuration. Aucun accès n’est présumé accepté tant que la confirmation n’est pas reçue.

## Étape suivante

Terminer l’isolation locale des plugins Cursor, valider un appel réel, puis enregistrer l’environnement et tester une tâche synthétique via Paperclip. Pour Antigravity, terminer le raccord au runtime isolé et aux événements d’arrêt avant inscription. Ne pas annoncer une orchestration multi-fournisseur opérationnelle sur la seule base des connexions de comptes.

## Diagnostic final Cursor et cohérence du déploiement

L’analyse du client installé n’a trouvé aucun réglage local supporté qui désactive tous les plugins synchronisés tout en conservant ce mode de connexion par abonnement. Le profil local active plugins/hooks et reçoit les plugins effectifs du backend. `--plugin-dir` ajoute des plugins ; il ne remplace pas la liste synchronisée. Nous n’avons modifié aucun réglage du compte distant et n’avons pas activé de contournement d’authentification. Cursor reste connecté, mais son exécution autonome n’est pas qualifiée. Détails : CURSOR-PLAN.md.

L’image des runners a été reconstruite avec le Dockerfile final puis les deux conteneurs ont été recréés en préservant leurs volumes. Image réellement exécutée : `sha256:aae9796dc5622423beeedc12d7b34ed4be0494ff14d77e0bf0274ce8d79385da`. Après recréation, SSH strict, UID, HOME et absence des variables serveur repassent ; les bindings de ports restent vides. Les permissions des fichiers de clés publiques sont celles du système hôte : Docker Compose ignore ici le mode déclaré pour ses configs liées à des fichiers.
