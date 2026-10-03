# Build candidat + lecture locale de connexion — résultat

**Correction (2 octobre 2026, `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`)** :
la version précédente de ce document annonçait une « connexion fournisseur
vérifiée ». C'est une sur-affirmation, corrigée ci-dessous (sections 3 et
4) : la sonde a tourné sous `--network none`, donc `auth status --json` n'a
pu lire QUE l'état de session déjà persisté localement sur disque — jamais
contacté un serveur distant. Ce qui est réellement prouvé : ce CLI plus
récent lit ce fichier de credentials existant sans erreur (compatibilité de
FORMAT). Ce qui N'est PAS prouvé : que le jeton qu'il contient est encore
accepté par le fournisseur distant aujourd'hui (compatibilité OAuth
distante, jamais testée ici, volontairement — le mandat interdit tout appel
réseau/modèle).

2 octobre 2026. Mandats : `docs/CLAUDE-BUILD-CANDIDAT-CONNEXION.md`,
complété par `docs/CLAUDE-COORDINATION-REVUE-CIBLEE.md`. Périmètre :
runner/runtime/qualification uniquement (`integrations/`, `deploy/`,
Orchestrator) — pas `src/server/ai`, pas UI, pas production, pas Cursor.
Détail technique complet (commandes, hash, sortie exacte) :
`integrations/openhands-claude-runtime/RESULTS.md`, section « Build réel du
candidat + sonde corrigée ». Ce document résume les quatre volets du mandat.

## 1. Correction préalable exigée avant toute sonde — faite, prouvée par test

Les deux scripts shell défaillants identifiés en revue
(`qualify_existing_image_account_probe.sh`, `cat` brut de stderr malgré
promesse, aucun contrat de code de sortie réel) sont supprimés. Remplacés
par `qualify_connection_account.py` (module pur) et
`test_qualify_connection_account.py` (23 tests). Un sous-agent natif en
lecture seule, borné au diff + critères de revue, a trouvé deux défauts
réels supplémentaires avant toute sonde (jamais une fuite) : un code de
sortie insuffisamment distinctif pour une commande `--version` en échec, et
une reconnaissance de message stderr connu-sûr trop permissive (sous-chaîne
plutôt qu'ancrée). Les deux corrigés par moi-même avec test de régression ;
aucun accès credentials/Docker délégué au relecteur.

## 2. Construction locale réelle — base manquante résolue, pas redemandée

Aucune des trois images (`sdk1.50.0`, `permissions1`, `candidate1`)
n'existait sur cette machine. Construites dans l'ordre documenté depuis les
Dockerfiles existants, versions/digests déjà épinglés, sans modification de
Dockerfile ni affaiblissement de permission. Le hash du patch de permissions
obtenu localement est identique à celui déjà documenté pour le build VPS —
reconstruction prouvée équivalente. Un vrai défaut a été trouvé et corrigé
pendant la construction : le lanceur `claude-agent-acp` versionné dans ce
dépôt avait des fins de ligne CRLF, cassant son exécution sur Linux
indépendamment de tout drapeau de sécurité Docker (vérifié avec et sans
chaque drapeau individuellement) ; corrigé (fins de ligne LF) et protégé par
`.gitattributes` contre une régression future sur un checkout Windows.

## 3. Sonde isolée contre le candidat construit — exécutée, nettoyée

Conteneur `--rm`, entrypoint remplacé par `python` explicite exécutant
uniquement le script corrigé, réseau désactivé (`--network none`), racine
lecture-seule, capacités supprimées. Seul montage réel : les credentials
Claude existants en lecture seule. Jamais `.openhands`, jamais le répertoire
projets, jamais le socket Docker. Résultat : diagnostic entièrement
classifié (code de sortie 0) — `loggedIn=true`, `authMethod="claude.ai"`,
`apiProvider="firstParty"`, `subscriptionType="pro"`, avec la CLI/adaptateur
plus récents de ce candidat (2.1.284/0.84.0). Réseau coupé par
`--network none` : ceci prouve une lecture locale cohérente du fichier de
credentials existant par ce CLI plus récent (compatibilité de format), PAS
que le fournisseur distant accepte encore ce jeton aujourd'hui
(compatibilité OAuth distante non testée, volontairement).
Un message stderr benin (fichier de config absent, sauvegarde disponible),
reformulé par cette CLI plus récente, a été structurellement examiné
(longueur, absence de marqueurs sensibles, puis contenu redigé caractère
par caractère) avant d'élargir le motif connu-sûr de façon précise et
ancrée — jamais par une recherche de sous-chaîne large. Nettoyage vérifié
par label : aucun conteneur ni image résiduel de cette sonde.

## 4. Statut et identité — jamais confondus

Session d'abonnement reconnue LOCALEMENT par ce candidat (lecture de fichier
de credentials existant, réseau coupé pendant la sonde) ; jamais confondue
avec une autorisation HQ, et jamais annoncée comme une validation distante
confirmée. Identité utilisateur (email,
orgId, orgName) : présente dans la réponse officielle mais jamais lue ni
imprimée par valeur, donc explicitement inconnue pour ce rapport — conforme
à la correction du lot précédent sur `orgId` ≠ identifiant utilisateur.
Codex : toujours aucune sous-commande auth, non retesté.

## Fichiers modifiés / ajoutés (Orchestrator, ce worktree)

```
M integrations/openhands-claude-runtime/RESULTS.md
M integrations/openhands-claude-runtime/claude-agent-acp   (fins de ligne LF)
M .gitattributes
A integrations/openhands-claude-runtime/qualify_connection_account.py
A integrations/openhands-claude-runtime/test_qualify_connection_account.py
A integrations/openhands-claude-runtime/probe_connection_candidate.sh
D integrations/openhands-claude-runtime/qualify_existing_image_account.sh
D integrations/openhands-claude-runtime/qualify_existing_image_account_probe.sh
A docs/CLAUDE-BUILD-CANDIDAT-CONNEXION-RESULTAT-2026-10-02.md
```

Images Docker locales créées (conservées, ce sont le livrable, pas des
ressources temporaires) : `oria-openhands-qualification:sdk1.50.0`,
`oria-openhands-qualification:permissions1`,
`oria-openhands-claude-runtime:candidate1`. Aucun fichier Oria.HQ touché.
Aucun contrôle HQ désactivé ou remplacé (`provider_policy.py`,
`model-emission-launch-gate.ts` inchangés). Aucune vraie mission modèle
exécutée, aucun déploiement, catalogue Cursor non touché.

## Prochaine action concrète unique

Obtenir l'approbation écrite explicite de Michael pour une policy/compte
approuvés et un budget borné (`provider_policy.py`,
`validate_authorization`, `maxCostCents`/`maxTokens`/`maxIterations`), puis
lancer ce candidat via son vrai point d'entrée ACP (pas l'override de
diagnostic) pour une tâche réelle unique, bornée et minimale — recette
complète dans `integrations/openhands-claude-runtime/RESULTS.md`.
