# Raccordement accountId — patch testé livré séparément, non appliqué

**Mise à jour (même jour)** : ce qui suit décrivait une proposition
documentaire. Elle est maintenant un vrai patch testé, livré à
`patches/hq-account-identity-binding/` (diff unifié + README). Une revue
ciblée bornée a trouvé deux défauts réels (test de non-déterminisme
insuffisant ; email non normalisé avant usage comme clé, risque de double
`accountId` pour un même compte) — tous deux corrigés, tests ajoutés
nommément, **12/12** après correction, `npx tsc --noEmit` propre. Testé
directement dans le worktree HQ réel puis extrait sans toucher aux
fichiers en cours de modification concurrente. Reste non appliqué : voir
prérequis en fin de document.

3 octobre 2026. Mandat : `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, point 2,
complété par sa « Clarification du responsable ». Ce document répond
précisément à cette clarification : l'interdiction porte sur l'INVENTION
d'identité (orgId/profileId en substitut) et sur l'EXPOSITION de données
personnelles dans les rapports — pas sur l'usage d'un identifiant utilisateur
officiellement renvoyé en soi.

## Ce qui existe déjà (constaté, pas touché)

`classifyClaudeCodeProbe` (`src/server/agents/runtimes/local-runtime-probe.ts`,
worktree HQ `hq-acces-reprise`, **actuellement en cours de modification non
commitée par un autre travail — non touché par ce document**) lit déjà le
JSON complet de `claude auth status --json`, mais ne lit JAMAIS le champ
`email` (seul le whitelist `CLAUDE_AUTH_EVIDENCE_FIELDS` est lu — ligne 622 :
« email/orgId/orgName sont simplement non lus »). Son propre commentaire
écarte `email` pour une raison précise : un accountId qui serait un HASH de
l'email serait réversible par dictionnaire/rainbow-table, l'email étant un
identifiant personnel à faible entropie — contrairement à un UUID à haute
entropie. Ce raisonnement est correct **pour un hash**, mais un hash n'est
pas le seul mécanisme possible.

## Le chemin proposé : liaison opaque côté serveur, jamais un hash

Pas un hash de l'email. Une **table d'indirection côté serveur**, strictement
privée, qui ne journalise ni n'expose jamais l'email dans un rapport :

1. **Nouveau fichier** (pas de modification d'un fichier existant) :
   `src/server/agents/models/account-identity-binding.ts`. Exporte une
   fonction pure injectée-dépendances (même style que tout le reste du
   dépôt — `resolveProviderConnectionDiscovery`, `provider_policy.py`) :

   ```ts
   export type AccountIdentityStore = {
     findByEmail(email: string): { accountId: string } | undefined;
     create(email: string, accountId: string, observedAtIso: string): void;
   };

   export function resolveOpaqueAccountId(
     email: string,
     store: AccountIdentityStore,
     clock: () => string,
   ): string {
     const existing = store.findByEmail(email);
     if (existing) return existing.accountId;
     const accountId = crypto.randomUUID(); // jamais dérivé de l'email
     store.create(email, accountId, clock());
     return accountId;
   }
   ```

   `accountId` est un UUID aléatoire, **jamais calculé à partir de
   l'email** — rien à inverser par dictionnaire, contrairement à un hash.
   L'email n'est lu qu'à l'intérieur de cette fonction et du store ; il ne
   remonte JAMAIS dans la valeur retournée, ni dans `evidence[]`, ni dans un
   log.

2. **Stockage** : un nouveau répertoire protégé, même classe que
   `/etc/oria-hq/provider-policies` (racine uniquement, mêmes règles que
   `protected_bytes()` côté `provider_policy.py` — propriétaire root, pas de
   bit d'écriture groupe/autres). Un enregistrement par compte :
   `{ "email": "...", "accountId": "<uuid>", "firstObservedAtIso": "..." }`.
   La protection vient des permissions fichier, pas d'une clé de recherche
   obscurcie — inutile de hacher la clé de recherche quand le fichier entier
   est déjà root-only : la même logique que pourquoi `provider_policy.py` ne
   hache pas non plus ses chemins de policy.

3. **Point d'intégration unique** (non modifié par ce document, décrit pour
   qui reprendra ce fichier une fois le chantier en cours commité) : dans
   `classifyClaudeCodeProbe`, branche `parsed.loggedIn === true`
   (`local-runtime-probe.ts`, ~ligne 628 au moment de cette lecture), lire
   `parsed.email` UNIQUEMENT pour l'passer à `resolveOpaqueAccountId`, et
   placer son résultat dans `contract`/le retour comme `accountId` — jamais
   l'email lui-même. Si `email` est absent/vide/de type inattendu : `accountId`
   reste absent, exactement comme aujourd'hui (aucune régression du
   comportement de refus existant).

## Stabilité et rotation — documenté, pas supposé

- **Stable tant que l'email ne change pas** : le même email produit toujours
  le même `accountId` (recherche par égalité stricte avant création).
- **Rotation non résolue par ce document** : si Michael change l'email de son
  compte Anthropic, ce mécanisme créerait un NOUVEAU `accountId` (nouvel
  enregistrement, email différent) — traitant cela comme un compte différent,
  jamais comme une continuité silencieuse. C'est un choix par défaut
  délibérément prudent (ne jamais supposer que deux emails différents sont la
  même personne), pas une garantie que Michael a validée. Décision explicite
  requise de sa part si une continuité à travers un changement d'email est un
  jour souhaitée.
- **Source réelle** : `email` tel que renvoyé par `claude-agent-acp --cli auth
  status --json` du CLI Claude officiel — jamais lu depuis un fichier, jamais
  deviné depuis la présence d'un chemin.

## Ce que ce patch ne fait PAS

- Ne modifie AUCUN fichier EXISTANT du worktree HQ `hq-acces-reprise`
  (travail en cours non commité détecté là, voir § « Pas de modifications
  concurrentes » du rapport principal de ce lot) — seulement deux fichiers
  NOUVEAUX, additifs, testés en place puis extraits sans toucher aux
  fichiers en cours de modification. Non appliqué pour de vrai (laissé en
  `??` non suivi dans ce worktree, exactement comme trouvé).
- Ne crée aucun secret ad hoc, ne touche à aucun fichier de credentials
  (`C:\Users\micha\Dev\openhands-credentials\claude` non touché, comme
  toujours).
- Ne crée pas le nouveau répertoire protégé `/etc/oria-hq/account-identities`
  pour de vrai — c'est un nouveau stockage de données personnelles (même
  minime : un email, un UUID, une date), ce qui mérite l'accord explicite de
  Michael avant toute création réelle, pas une décision prise seule par ce
  lot.
- Ne décide pas la question de rotation d'email ci-dessus — présentée à
  Michael, pas résolue ici.

## Prérequis avant application réelle

1. Accord explicite de Michael pour créer ce nouveau stockage server-side de
   données personnelles (même minimal).
2. Décision de Michael sur la continuité d'identité à travers un changement
   d'email (traiter comme nouveau compte par défaut, ou prévoir une
   migration manuelle).
3. Que le chantier actuellement en cours, non commité, dans
   `hq-acces-reprise` (`local-runtime-probe.ts`,
   `provider-connection-discovery.ts`, `model-emission-launch-gate.ts`) soit
   d'abord commité, pour éviter d'appliquer ce patch sur un état mouvant.
