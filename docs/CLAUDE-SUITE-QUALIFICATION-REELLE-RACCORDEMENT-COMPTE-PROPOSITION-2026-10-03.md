# Raccordement accountId — patch testé livré séparément, non appliqué

**Mise à jour (troisième passe)** : le helper en mémoire ci-dessous est
désormais SUPERSEDÉ. Livrable final :
`patches/hq-account-identity-binding/account-identity-repository.patch` —
stockage RÉEL réutilisant `approval-record-repository.ts` (Supabase +
fallback mémoire local, même garde `isLocalPersistenceFallbackAllowed`),
clé `(provider, workspaceId, email)` inchangée. 12/12 tests (identité
stable, restart, changement de compte, refus inconnu, non-déterminisme,
non-fuite, normalisation, échec fermé en production), `tsc` propre avec
résolution réelle des alias `@/*` (fichiers écrits en place cette fois,
sous contrôle parent, rien d'autre touché). Détail : README du patch.

**Mise à jour (même jour, seconde passe)** : une revue a trouvé que
(a) les fichiers avaient été laissés non suivis DANS `hq-acces-reprise`
malgré le mandat de patch séparé, (b) le README affirmait « mêmes 12
erreurs TS Cursor », faux pour l'état courant (`tsc` est vert), et (c) la
clé du store était `email` seul, ce qui fusionnerait deux comptes de
fournisseurs différents partageant le même email. Les trois corrigés :
fichiers supprimés de `hq-acces-reprise` (zéro trace désormais), preuve
remplacée par les sorties exactes de cette passe, clé du store étendue à
`(provider, workspaceId, email)`. **13/13** tests, `npx tsc --noEmit`
propre sur tout le dépôt (vérifié à l'instant, pas réutilisé). Détail
complet et méthode (comment patché/testé sans jamais écrire dans
`hq-acces-reprise`) : `patches/hq-account-identity-binding/README.md`.

3 octobre 2026. Mandat : `docs/CLAUDE-SUITE-QUALIFICATION-REELLE.md`, point 2,
complété par sa « Clarification du responsable » et son « Constat revue
immédiat ». Ce document répond précisément à la clarification initiale :
l'interdiction porte sur l'INVENTION d'identité (orgId/profileId en
substitut) et sur l'EXPOSITION de données personnelles dans les rapports —
pas sur l'usage d'un identifiant utilisateur officiellement renvoyé en soi.

## Ce qui existe déjà (constaté, pas touché)

`classifyClaudeCodeProbe` (`src/server/agents/runtimes/local-runtime-probe.ts`,
worktree HQ `hq-acces-reprise`, **actuellement en cours de modification non
commitée par un autre travail — non touché par ce document**) lit déjà le
JSON complet de `claude auth status --json`, mais ne lit JAMAIS le champ
`email` (seul le whitelist `CLAUDE_AUTH_EVIDENCE_FIELDS` est lu). Son
propre commentaire écarte `email` pour une raison précise : un accountId
qui serait un HASH de l'email serait réversible par dictionnaire/rainbow-
table, l'email étant un identifiant personnel à faible entropie —
contrairement à un UUID à haute entropie. Ce raisonnement est correct
**pour un hash**, mais un hash n'est pas le seul mécanisme possible.

## Le chemin proposé : liaison opaque côté serveur, jamais un hash, jamais l'email seul comme clé

Pas un hash de l'email. Une **table d'indirection côté serveur**, strictement
privée, qui ne journalise ni n'expose jamais l'email dans un rapport — et
dont la clé de recherche est le triplet `(provider, workspaceId, email)`,
jamais l'email seul (correction de revue : l'email seul comme clé
fusionnerait silencieusement deux comptes différents — par exemple un
compte Claude et un compte Codex séparé partageant le même email humain,
ou le même fournisseur sous deux workspaces HQ différents — en un seul
`accountId`, exactement la confusion que ce module existe pour empêcher) :

```ts
export type AccountIdentityKey = { provider: string; workspaceId: string; email: string };
export type AccountIdentityRecord = AccountIdentityKey & { accountId: string; firstObservedAtIso: string };
export type AccountIdentityStore = {
  find(key: AccountIdentityKey): AccountIdentityRecord | undefined;
  create(record: AccountIdentityRecord): void;
};

export function resolveOpaqueAccountId(
  key: AccountIdentityKey,
  store: AccountIdentityStore,
  clock: () => string,
): string {
  const normalized = { provider: key.provider.trim(), workspaceId: key.workspaceId.trim(), email: key.email.trim().toLowerCase() };
  const existing = store.find(normalized);
  if (existing) return existing.accountId;
  const accountId = crypto.randomUUID(); // jamais dérivé de l'email
  store.create({ ...normalized, accountId, firstObservedAtIso: clock() });
  return accountId;
}
```

`accountId` est un UUID aléatoire, **jamais calculé à partir de l'email**
— rien à inverser par dictionnaire, contrairement à un hash. L'email n'est
lu qu'à l'intérieur de cette fonction et du store ; il ne remonte JAMAIS
dans la valeur retournée, ni dans `evidence[]`, ni dans un log. `provider`
et `workspaceId` sont des identifiants déjà utilisés ailleurs dans ce dépôt
(`providerProfileSchema`, `ApprovedServerBinding.workspaceId`) — jamais
inventés ici.

**Stockage** : un nouveau répertoire protégé, même classe que
`/etc/oria-hq/provider-policies` (racine uniquement, mêmes règles que
`protected_bytes()` côté `provider_policy.py`). La protection vient des
permissions fichier, pas d'une clé de recherche obscurcie.

**Point d'intégration unique** (non modifié par ce document, décrit pour
qui reprendra ce fichier une fois le chantier en cours commité) : dans
`classifyClaudeCodeProbe`, branche `parsed.loggedIn === true`, lire
`parsed.email` UNIQUEMENT pour le passer à `resolveOpaqueAccountId` avec le
`provider`/`workspaceId` déjà connus à cet endroit de l'appel, et placer le
résultat dans `contract`/le retour comme `accountId` — jamais l'email
lui-même. Si `email` est absent/vide/de type inattendu : `accountId` reste
absent, exactement comme aujourd'hui (aucune régression du comportement de
refus existant).

## Stabilité et rotation — documenté, pas supposé

- **Stable tant que le triplet (provider, workspaceId, email) ne change
  pas** : le même triplet produit toujours le même `accountId` (recherche
  par égalité stricte avant création).
- **Rotation non résolue par ce document** : si Michael change l'email de
  son compte Anthropic, ce mécanisme créerait un NOUVEAU `accountId` —
  traitant cela comme un compte différent, jamais comme une continuité
  silencieuse. Choix par défaut délibérément prudent, pas une garantie que
  Michael a validée. Décision explicite requise de sa part si une
  continuité à travers un changement d'email est un jour souhaitée.
- **Source réelle** : `email` tel que renvoyé par `claude-agent-acp --cli
  auth status --json` du CLI Claude officiel — jamais lu depuis un fichier,
  jamais deviné depuis la présence d'un chemin.

## Ce que ce patch ne fait PAS

- Ne modifie AUCUN fichier EXISTANT du worktree HQ `hq-acces-reprise`
  (travail en cours non commité détecté là) — seulement deux fichiers
  NOUVEAUX. **N'écrit plus du tout dans ce worktree** (correction de
  revue : la version précédente y avait laissé les fichiers non suivis
  après extraction ; celle-ci est entièrement écrite/testée hors de ce
  worktree — méthode exacte dans le README du patch).
- **N'est pas un raccordement opérationnel.** Seul
  `createInMemoryAccountIdentityStore()` est fourni — en mémoire, durée de
  vie d'un seul processus, usage test/fixture uniquement. Ce module seul,
  même une fois appliqué, ne fait rien tant qu'un vrai store persistant et
  protégé n'est pas construit et raccordé — décision séparée et explicite,
  pas une lacune dissimulée par ce patch.
- Ne crée aucun secret ad hoc, ne touche à aucun fichier de credentials.
- Ne crée pas le nouveau répertoire protégé `/etc/oria-hq/account-identities`
  pour de vrai — nouveau stockage de données personnelles (même minime),
  accord explicite de Michael requis avant toute création réelle.
- Ne décide pas la question de rotation d'email — présentée à Michael, pas
  résolue ici.

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
