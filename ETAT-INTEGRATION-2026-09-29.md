# État d’intégration vérifié — 29 septembre 2026

L’objectif complet reste ouvert : HQ doit encore être déployé durablement et exécuter une mission complète avec ses agents. Ce document sépare les preuves obtenues des intégrations non terminées.

## Avancées de ce lot

| Élément | Preuve actuelle | Limite |
|---|---|---|
| Memex Core | gate1 : 214 tests réussis ; collisions de publication et corrections concurrentes contrôlées ; handles signés sans token global | Un seul publisher par stockage ; le fichier vault d’une correction perdante peut subsister, mais reste exclu du graphe publié |
| Memex sur VPS | Image Node22 construite, test HTTP Linux réussi, service privé démarré, UID1000/racine readonly/aucun port public | Pilote synthétique, pas activation générale des agents |
| Persistance | Deux mémoires synthétiques relues après redémarrage avec leurs scopes et provenance | Ne prouve pas toutes les migrations de données existantes |
| Reprise Memex | Trois archives comparées après restauration, clone sans réseau démarré, lectures signées/scopes/refus vérifiés, clone arrêté | Test sur ce VPS ; sauvegardes locales privées non chiffrées, pas de copie hors machine |
| HQ → Memex | Test réel du backend HQ via HTTP signé : mémoire A acceptée, workspace B refusé ; 21:46:37 UTC | Module backend testé, application HQ déployée non activée ; handle de test temporaire, aucun secret dans .env |
| Interface HQ | Projection Paperclip ajoutée aux Missions ; 9 tests ciblés + validations requises | Connexion utilisateur nécessaire pour vérifier le rendu authentifié ; pas de faux statut opérationnel |
| Transport HTTP HQ | 16 tests ciblés, typecheck/lint/build/smoke réussis | 5 avertissements lint préexistants ; configuration opt-in désactivée |
| Sauvegarde Paperclip | Dump restauré, comptes de lignes identiques, archive applicative restaurée/comparée ; application source redémarrée HTTP200 | Login et mission sur instance restaurée non testés ; volumes des fournisseurs exclus |

## Identités reproductibles

- Source Memex canonique : `C:/Users/micha/Documents/memex-core`, branche `codex/memex-memory-foundations`, base `8bfd221`, modifications non commitées incluses dans snapshot explicite.
- Snapshot déployé : 37 fichiers source/manifests/catalogues MCP seulement. SHA256 du manifeste : `67b097bf05a54668ab804ec984d493d8b8ad1f1eebf1a6f3225ebf9ed79dc7d3`.
- Image Memex exécutée : `sha256:23805a5b18f4dd3379eaf4f43c6f36c9aaf9deade53a74346fcff214270561d7`.
- Déploiement : `/opt/oria-memex-pilot`, réseau interne `oria-memory-private`, volumes graph/intake/vault dédiés. Aucun partage avec AgentMemory local.
- Reprise Memex : `/opt/oria-memex-pilot/backups/20260929-first-restore/recovery-evidence.json` ; contient les résultats, pas à publier avec les clés adjacentes.
- Reprise Paperclip : `/opt/oria-paperclip-pilot/backups/20260929T213558Z-aeadbfa4/result.txt`.
- HQ canonique : `C:/Users/micha/Dev/Oria.HQ`, branche `codex/hq-mission-dossier`.

Le premier build Memex a échoué au test HTTP faute de deux catalogues JSON runtime. Le snapshot et le Dockerfile ont été corrigés, une régression du snapshot ajoutée, puis l’image réelle reconstruite et retestée. Aucune activation du build défectueux.

## Réseau et credentials

Les essais depuis les runners Gemini et Cursor vers le port3000 de Memex ont été refusés. Le backend HQ a utilisé un tunnel SSH local temporaire et un handle read_only de 15 minutes limité à `org:workspace:pilot-a`, capturé uniquement dans l’environnement du processus de test. Le tunnel3320 a été fermé et le handle n’a pas été persisté. La clé de signature reste exclusivement côté service mémoire/opérateur.

La procédure de rotation de credentials pour un backend permanent reste à finaliser ; le test ne prétend pas fournir une connexion durable. Aucun contenu réel utilisateur n’a été injecté dans le pilote mémoire.

## Dépendances encore ouvertes

1. Autorisation CLI Paperclip demandée précédemment, non reçue : auth whoami retourne401 et ancien processus d’attente absent. L’ancien challenge ne doit pas être réutilisé comme preuve d’approbation. Après accord explicite, créer un challenge frais, enregistrer les connexions puis révoquer l’accès opérateur temporaire.
2. Cursor : connexion réussie, mais exécution autonome non qualifiée ; plugins/hook/LSP synchronisés, aucun override local complet identifié. Aucun réglage cloud changé.
3. Gemini CLI : compte refusé par le fournisseur pour ce client ; Antigravity fonctionne avec Google AI Pro, mais son adaptateur Paperclip reste désactivé en attente du raccord de cycle de vie/exécution.
4. HQ : authentification réelle, configuration de déploiement, projection Paperclip réelle et dispatch d’une mission restent à tester ensemble. La session navigateur locale a correctement été redirigée vers login ; pas de contournement.
5. Grille HQ-ACCEPTATION.md : ne pas marquer les19 scénarios entièrement satisfaits. Les invariants mémoire et la reprise ont progressé ; mission complète, pause/reprise orchestrée, budget global, décisions distribuées et comparaison un/deux agents restent ouverts.

Aucun commit ni push effectué. Toutes les preuves runtime ci-dessus sont distinctes des tests simulés. La prochaine étape utile est une mission de développement réelle, bornée, reliée au contexte Memex et à une preuve de résultat, après raccord autorisé de l’exécutant.
## Antigravity — exécuteur SSH qualifié (29 septembre, suite)

L’exécuteur `oria-provider-runners-antigravity-runner-1` est maintenant déployé : utilisateur1000, racine en lecture seule, volumes propres, aucun port publié, binaire1.2.13 vérifié et modules montés en lecture seule. Son réseau de contrôle n’est pas encore raccordé à Paperclip.

- SSH strict : connexion vérifiée, clé hôte inconnue refusée (255), secrets serveur absents, workspace inscriptible.
- Watchdog distant : commande synthétique sleep20 interrompue à1seconde, sortie124, enfant absent.
- Appel réel par SSH à remote-entry : `ORIA_AGY_SSH_OK`, provider SUCCESS en4,521s, 13803tokens entrée/294sortie/14097total. Coût monétaire inconnu. Cette charge fixe reste importante pour une microtâche.
- Arrêt complet du runner après essai : Running=false et PID=0 vérifiés, puis redémarrage. Ceci ne constitue pas encore un test d’annulation d’une génération en cours depuis Paperclip.
- Adaptateur : 21tests synthétiques annoncés par l’agent ; dépendances hôte explicites pour rendre la tâche et prouver l’arrêt du runner. Le loader Paperclip n’est pas encore raccordé ; agent non activé.

L’accord utilisateur reçu concerne les conditions Antigravity, déjà appliquées. Il ne vaut pas accord pour le jeton CLI administrateur Paperclip distinct toujours en attente. Aucun secret copié dans ce rapport.

## HQ privé sur VPS — build et protection réels

Le snapshot v3 (823 fichiers, aucun .env ni état local) est déployé dans `/opt/oria-hq-pilot`. Image épinglée : `sha256:e2a7cbc3f1e2973b71bc492f9fe858c377cc7656ebeee14f6a84593cbb1b15d1`. UID100 non-root, lecture seule, aucun port hôte publié. Les six variables indispensables proviennent de la configuration existante, transférées par SSH sans affichage vers runtime.env mode600 ; aucun credential dans l’image, le code ou ce rapport.

La nouvelle UI prépare puis confirme un transfert vers une tâche backlog non attribuée. Le reçu durable empêche les doublons et survit à une reconfirmation du brouillon ; les réponses ambiguës ferment le renvoi. Ce transfert reste désactivé au runtime et n’est pas une exécution d’agent.

Validation locale de l’agent HQ : tests ciblés20 puis7 régressionsUI après revue, typecheck/lint/build/smoke et diffcheck PASS ; cinq avertissements lint préexistants. BuildLinuxVPS v3 PASS. Deux anomalies trouvées uniquement au runtime, corrigées et retestées : sonde localhost refusée →127.0.0.1 ; catalogue modèles gratuits absent de standalone →COPY explicite du fichier. Aucun modèle désactivé n’a été activé.

Preuves finales : Docker healthy, HTTPhealth200 avec degraded/inngest_keys_missing explicite, missions redirigées307 vers login, API sans session401. La connexion navigateur est affichée à http://localhost:3321/hq/missions via tunnel SSHsession86066 ; connexion utilisateur demandée, pas encore confirmée. Ne pas affirmer authentification propriétaire ou mission complète validées.

Claude : le chemin ai-local-logins historique a été vérifié absent. Le source Paperclip explique qu’il est temporaire et supprimé après promotion des credentials dans le service de connexions. Aucun montage de ce chemin périmé n’a été réalisé. Le runner doit employer son propre HOME, et l’adaptateur natif recevra les credentials via Paperclip ; ne pas copier le volume applicatif complet.

Antigravity : cette version Paperclip interdit aussi la cible SSH/sandbox aux types externes dans environment-support.ts. Un correctif hôte explicite est nécessaire en plus des bindings de rendu/arrêt. Le succès CLI ne prouve pas cette intégration native.

Claude exécuteur final : `oria-provider-runners-claude-runner-1` créé avec volume dédié oria-claude-home, workspace/hostkeys séparés ; aucun volume Paperclip monté. SSHstrict testé, clé inconnue255, CLI2.1.283, UID1000/HOME correct, secrets serveur absents, /usr non inscriptible. Aucun appel fournisseur ni agent natif lancé. La promotion des credentials devra passer par le service natif de connexions Paperclip, pas le répertoire de login supprimé. Réseau de contrôle non encore rattaché au serveur.

## Blocage Supabase identifié — remplace la demande de connexion HQ

La vérification dépendances depuis le conteneur HQ échoue avant toute lecture : DNS ENOTFOUND pour le projet Supabase configuré. Confirmé séparément sur Windows, tandis que supabase.com résout normalement. Le connecteur Supabase renvoie projects=[] ; le tableau de bord redirige vers login. Impossible de conclure projet supprimé, en pause ou compte incorrect sans accès utilisateur.

Demande utilisateur actuelle : se connecter à Supabase (onglet4) avec le compte propriétaire pour identifier/restaurer le projet existant. La demande précédente de loginHQ est suspendue ; ne pas inviter à réessayer tant que la dépendance échoue. Aucune nouvelle base, migration, session forgée ou credential substitué.

Ajout du contrôle deploy/hq-pilot/readiness.mjs : lecture seule, aucun contenu de ligne, trois dépendances bornées/redirects refusés, erreurs génériques sans secrets. Tests3/3 PASS ; exécution réelle VPS ready=false/supabase_auth dns_not_found. La santé Docker prouve seulement le serveur, pas une connexion utilisable. Objectif global toujours incomplet.

## Supabase rétabli après connexion utilisateur

L’utilisateur s’est connecté au dashboard Supabase et a demandé de poursuivre. Le projet Oria.hq était effectivement en pause (données annoncées conservées). Reprise déclenchée via Resume project puis Resume ; statut successif Coming up, Restoration in progress, Restoration complete puis Healthy. Aucun abonnement Pro acheté, aucune nouvelle base créée, aucune migration appliquée.

Les réponses DNSabsent, HTTP521 puis PGRST205 observées pendant la restauration étaient transitoires. Après terminaison confirmée : Auth200, missions200, action_ledger200 depuis le VPS. Vérification supplémentaire de toutes les colonnes écrites par le repository action_ledger réussie avec limit0 ; readiness.mjs étendu en conséquence, tests3/3 PASS. Les données métier n’ont pas été lues ni modifiées par les probes.

Le blocage d’infrastructure Supabase est levé. La session HQ reste distincte du dashboard Supabase : ongletHQ encore surlogin ; connexion utilisateur demandée pour vérifier les missions authentifiées. Le transfert Paperclip et les écritures CAS restent non validés en réel. Preuve visuelle .validation/supabase-restored.png. Le statut du goal retourné par get_goal reste blocked ; le tool update_goal ne propose pas active/resume, donc ne pas prétendre l’avoir réactivé par cet outil.

## Audit HQ connecté — version privée v6

Supabase restauré et propriétaire connecté : les anciennes observations de blocage ci-dessus sont historiques. Auth/colonnes missions/ledger renvoient200 au contrôle read-only. Cette sonde ne teste pas les écritures.

Accueil recentré sur objectif/assistant/missions réelles/activité, filtres et détails; mémoire accessible avec sélecteur, écriture RAM refusée en production; journal détaillé dans /hq/activity. Dates Toronto harmonisées. Sidebar mobile nommée pour lecteurs d’écran; palette focusborné et retourfocus; débordement en-tête corrigé. Aucun LLM au rendu cash-action page. Contexte Memex advisory ne devient plus vérifié; seeds datés à la source et profils activés distingués des connexions.

Validation: suite complète3899pass0fail2skip (intégrationsMemexoptin); typecheck/lint/build/smokePASS, lint5warnings préexistants. Après corrections mobiles/fuseau, typecheck/lint et testsledger9pass, buildsLinuxVPS v5/v6PASS. Diffcheck propre. Tests navigateur authentifié: exemplesansenvoyer, filtres, agenda14j, paletteclavierfocus, choixconnaissance, étatPaperclipdésactivé, journalSupabase, filecashvide. Dimensions390/1440pasdébordementglobal. Pas de test d’inférence ni données créées.

Snapshot v6 829 fichiers; manifestSHA256 F9FEAAB370641ED7F02898BC7A20696914B234D5A331473DDB7095047E07589E. Image sha256:7cf5b4e72b7ce728106abf1640a7de5dcf0e71f4cc1003f902096e7c21dc200a. Nonrootoria, readonly, aucunportpublié. rollback compose.before-v4.json vers v3 disponible distant. Tunnel3321 conservé. Captures .validation/hq-audit-desktop.png et hq-audit-mobile.png. Rapport canonique Oria.HQ/docs/HQ-ARCHITECTURE-AUDIT-2026-09-29.md.

Limites: HQmono-propriétaire, vaultfichiersglobal à partitionner avantmultiworkspace; mémoire durableUI nonraccordée; dispatch/readPaperclip et Memexdésactivés; vraie missionagent toujours nonqualifiée. Aucune promesse zérobug. Aucuncommitpush. Goal existant blocked/inachevé empêche create_goal nouveau; erreur signalée, pas contournée par fauxcomplete.

## Memex réellement consultable dans HQ — v7

Le 29 septembre 2026 : consultation authentifiée dans /hq/memory réussie, namespace projet vide affiché explicitement. HTTPS privé avec CA vérifiée, handle read_only limité au projet, renouvellement atomique toutes les vingt minutes pour une durée de vie d'une heure. Lecture réussie après renouvellement et redémarrage du relais, sans redémarrer HQ. Les trois services redémarrent automatiquement unless-stopped. Supabase readiness Auth/missions/ledger HTTP200.

HQ3904pass/2skip, Memex215pass, TLS6pass, rotation3pass ; gates et builds Linux passent. Canary réel TLS passe avec refus interprojets, écriture, tamper, CA inconnue et mauvais SAN. Aucun corpus utilisateur injecté ni inférence fournisseur déclenchée.

Déploiement exact et limites : deploy/hq-pilot/MEMEX-CONNECTION.md. Toujours inclure memex.overlay.json au déploiement HQ. Le certificat serveur est valable90jours et son renouvellement n'est pas encore automatisé. La lecture UI est un échantillon maximal50, pas une recherche exhaustive. La contribution/approbation/publication et la mission native multiagent restent à finaliser. Le goal est actif et incomplet.

## Contribution durable HQ → Memex — v11

Parcours navigateur qualifié : une règle proposée est conservée en proposed, reçu retrouvé après redémarrage Memex et rotation du handle, mappingSQLreadonly count1. Aucun publish/approve. Nouvelle proposition possible avec ancienreçu conservé. Originpublique explicite pour tunnel3321, reprise manuelle mêmeID et contenu ; aucunrenvoiautomatique. HQ3919pass0fail2skip +4gatesPASS, Memex215PASS, testinterreposHTTPsignéréelPASS. Images et limites dans deploy/hq-pilot/MEMEX-CONTRIBUTION.md. Prochaine tranche : revuehumaine attribuée, publication et historiquedurable UI. Goal toujoursactif/incomplet. Aucuncommitpush.

## Revue gouvernée locale — socle déployé
Memex217testsPASS ; revue atomique/hashversion1/markerreview_required et garde publisher/journal. Image04c47d5b4572fed80ea1a04a93bf6a525f8dcfa2567897e80bc0eae108ffd367. Preuveinterrepos submit->revuefixture->publication->lectureHQ aprèsreopen PASS ; acceptancesLinuxPASS. VPScontributionexistanteproposed+reviewRequired1, reçunavigateuraccessible. Pasd'approbationréelle ni endpointreviewHQ. Détails deploy/memex-pilot/GOVERNED-REVIEW.md. Goalactifincomplet.
