# Qualification de la factory par instance — 30 septembre 2026

Construction de l'image distincte `oria-openhands-qualification:permissions1` sur le VPS, sans réseau pendant le build. La version et le SHA256 du fichier SDK installé correspondent aux garde-fous du patch. Fichier original : `8c949ea7053c74ef42d5ee1f775069cbefe7fe4f59d922ccf724595717f541f9`; fichier modifié : `7a496b59265b8139e3dd965e9ef95e28133db5cfa4b48ee20da12c328e152455`.

`run.sh` termine avec code 0 : deux conversations SDK concurrentes observent respectivement DENIED et ALLOWED via de vrais échanges ACP avec des pairs synthétiques. Un troisième essai deny après allow observe DENIED. La méthode globale d'origine reste identique. Aucun conteneur portant le label de qualification ne reste après exécution.

Confinement : réseau désactivé, racine en lecture seule, utilisateur non root, ressources bornées, espace temporaire, aucun secret ni montage applicatif. Aucun appel de modèle. Les services actifs et l'image SDK initiale ne sont pas modifiés.

L'extension est un patch local ciblé, pas une API upstream existante. Le test ne démontre pas une approbation humaine durable, la restauration du sous-type, ni le confinement d'un fournisseur qui omettrait une demande de permission. Les avertissements de stockage en mémoire et d'absence d'usage concernent ce scénario synthétique. Ne pas déduire des coûts réels de ses compteurs zéro.

Étape suivante : relier une décision durable, expirante et liée à la mission à cette factory, puis tester un fournisseur officiellement connecté dans un workspace isolé. Le dossier HQ de soumission est préparé séparément sans activer l'exécution réelle.

## Callback borné par instance
Image reconstruite depuis base intacte. qualify_callbacks.py termine code 0 sur VPS : option offerte autorisée, option inconnue refusée, exception refusée, timeout refusé, annulation appelant propagée, isolation des instances, reconstruction sans callback en refus. Ce test invoque le bridge directement avec modèles ACP validés; il ne simule pas une approbation HQ durable. Ancien scénario de conversations concurrentes rejoué code 0 après changement. Aucun fournisseur testé ni modèle appelé.

## Callback dans une vraie conversationSDK
Scénario instancePolicies étendu et exécuté VPS code0 : callback sélectionnant option offerte donne ALLOWED sur le filACP; callback simulant autorité indisponible donne DENIED. Les conversations concurrentes deny/allow et denyaprèsallow passent encore. Ceci complète les appels directs de qualify_callbacks.py avec une preuve du raccordement factory→bridge→callback→pair. Pair synthétique, aucune approbationHQ durable ni fournisseur réel.
# Qualification des budgets de session — 30 septembre 2026

Durcissement ultérieur : BudgetPermissionAgent refuse désormais la politique de
test upstream-auto-allow et tout mode de session autre que default; champs gelés.
Reconstruction budgets1 après correction des scripts de patch (gardes explicites)
et tests de configurations invalides : image retournée par Docker build
`sha256:7ef7880436d4a7738e6c527ea16dad8c62e16efceb8c0b1fb34099c0c49becb8`.
Cet identifiant a ensuite été revérifié par `docker image inspect ... --format
{{.Id}}` sur le VPS : c'est l'ID immuable local de l'image. Ne pas le confondre
avec le digest du manifest/index des constructions précédentes. Le futur
lancement doit résoudre et lier cet ID côté serveur, puis le comparer à
`.Image` du conteneur, plutôt que faire confiance au tag mutable `budgets1`.
Qualification concurrente rejouée code0, aucun modèle. Les références d'image
ci-dessous décrivent la première construction, antérieure à ce durcissement.

Image séparée `oria-openhands-claude:budgets1` construite sur le manifest Claude
`0c894a12d134550817570bb5727854bf8da5f708165ba011916b80eec2b1c2c4`.
Manifest résultant `b14f4398c0a305e3ed5749638e36e542127900f6d2ff7f507072888c607090e0`.
Le patch vérifie la source déjà qualifiée; SHA après extension metadata :
`0c95575be6fddaef11a98ff645a42b2cba3441be244a78a7c0e443aff4513b23`.

Premier essai échoué : HOME en lecture seule empêchait la création des profils
OpenHands. Ajout d'un tmpfs HOME borné, privé, UID10001, sans credentials.
Deux conversations SDK simultanées ont ensuite transmis au pair ACP synthétique
respectivement maxTurns2/maxBudgetUsd1.25 et maxTurns7/maxBudgetUsd3.5, avec
allowDangerouslySkipPermissions=false et politique de permission deny. Code0.
Réseau désactivé, aucun modèle, aucun changement aux services existants.

Ce résultat atteste le transport et la séparation des options entre instances.
Il ne prouve ni enforcement Claude, ni plafond strict tokens/coût, ni reprise
d'une session existante. Le pair n'émet pas d'usage : avertissement SDK attendu,
aucune consommation réelle mesurée.

# Per-invocation permission boundary — 2026-09-30

CallbackBridge now accepts only offered allow_once/reject_once option IDs.
An offered allow_always selection is cancelled, preventing one scoped decision
from becoming a persistent provider grant. Actual ACP schema and SDK callback
qualification passed on VPS with the two updated source files mounted read-only
over runner image152df564 (no rebuild/deployment). Existing cancellation,
timeout, unknown-option, failure and instance-isolation checks also passed.
No network, credentials or model calls. Durable HQ tool approval remains unwired;
this change does not grant any new tools to the currently default-deny runner.
