# Revue ciblée — délai des réponses fournisseur

**Auteur :** Claude Code (revue indépendante, lecture seule)
**Date :** 1er octobre 2026
**Source lue :** `C:/Users/micha/Dev/Oria.HQ/.claude/worktrees/hq-acces-reprise`, candidat `58712d0`
(« Record real browser acceptance and independent storage review »).
**Propriétaire du correctif :** Cursor. **Je n'ai modifié aucun client, test ni migration.**

## Verdict

**Reproduit.** `timeoutMs` ne borne plus l'appel dès que les en-têtes sont reçus. Une réponse dont le
corps ne termine jamais échappe au délai, dans les **deux** clients.

## Lignes concernées

Le minuteur d'annulation est désarmé à la réception des en-têtes, alors que le corps est consommé
ensuite :

| | `anthropic-json-client.ts` | `openai-json-client.ts` |
| :--- | :--- | :--- |
| `setTimeout(() => controller.abort(), timeoutMs)` | 108 | 105 |
| `await fetchFn(...)` — en-têtes reçus | 111 | 108 |
| **`clearTimeout(timeoutId)`** | **128** | **127** |
| `await response.json()` — hors délai | 139 | 138 |
| `clearTimeout` + branche `AbortError` → `timeout` | 176, 178 | 175, 177 |

Entre le `clearTimeout` et la fin de `response.json()`, plus aucun minuteur ne peut appeler
`controller.abort()`. La fenêtre n'est bornée par rien côté client.

## Scénario et résultat observé

Sonde bornée : `Orchestrator/.validation/provider-deadline/probe.mjs`, exécutée sous Node 22.14
(WSL). Serveur HTTP **strictement local** (`127.0.0.1`, port éphémère), clés **synthétiques**, aucun
modèle, aucun réseau fournisseur. Le `fetchFn` injecté transmet `init` — **signal compris** — au
`fetch` natif de Node et ne redirige que la destination : les sémantiques d'annulation sont donc
celles de la production, pas celles d'un mock. Le processus sort explicitement, même si le client pend.

```
-- Contrôle : le harnais honore-t-il l'annulation ? ------------------
anthropic / en-têtes bloqués       timeoutMs=600  -> 611ms  ok=false  errorCode=timeout
openai    / en-têtes bloqués       timeoutMs=600  -> 600ms  ok=false  errorCode=timeout
anthropic / réponse complète       timeoutMs=600  -> 25ms  ok=true
openai    / réponse complète       timeoutMs=600  -> 7ms  ok=true

-- Cas examiné : corps qui ne termine jamais -------------------------
anthropic / corps bloqué           timeoutMs=600  -> AUCUN RÉSULTAT après 3000ms : délai échappé
openai    / corps bloqué           timeoutMs=600  -> AUCUN RÉSULTAT après 3001ms : délai échappé

-- Responsabilité du transport de test (pas du client) ---------------
anthropic / fetch sourd au signal  timeoutMs=600  -> AUCUN RÉSULTAT après 3001ms : délai échappé
```

Le code de sortie 1 est le verdict de la sonde (« non borné »), pas une panne du harnais.

Les deux premières lignes sont le contrôle qui rend la preuve exploitable : avec le **même** serveur,
le **même** client et le **même** `fetchFn`, un blocage **avant** les en-têtes est bien coupé à
~600 ms avec `errorCode:"timeout"`. L'annulation fonctionne donc ; seule la fenêtre postérieure au
`clearTimeout` n'est pas couverte. Le blocage n'est pas un artefact du harnais.

## Client ou transport : la frontière

- **Corps bloqué via le `fetch` natif → défaut du client.** Le transport respecte le signal ; c'est le
  client qui a désarmé son minuteur trop tôt. Un `fetch` conforme ne peut rien y faire : plus personne
  n'appellera `abort()`.
- **`fetchFn` sourd au signal → défaut du transport de test.** Le contrat du client délègue
  l'annulation au signal qu'il fournit ; un transport injecté qui l'ignore pend légitimement. Ce
  troisième cas est documenté pour qu'il ne soit pas confondu avec le précédent, et il ne fonde aucune
  demande de correction côté client.

## Effet

- **Délai :** le `timeoutMs` annoncé (défaut 20 000 ms, `anthropic:30` / `openai:31`) ne garantit plus
  de borne supérieure. `errorCode:"timeout"` devient **inatteignable** pour un corps qui stagne.
- **Appelant :** la promesse ne se règle jamais, donc aucun repli ni réessai en aval ne s'exécute. La
  seule borne restante est celle que le runtime hôte impose, pas celle du contrat du client.
- **Budget :** un appel qui ne se règle jamais ne renvoie jamais `tokenUsage`. Toute comptabilisation
  faite **au point d'appel** n'enregistre donc rien pour une tentative qui a pu consommer de la sortie
  fournisseur. Je m'arrête là : la refonte du débit appartient à Cursor et je ne la réaudite pas.

## Correction minimale recommandée (à Cursor, pas appliquée ici)

Garder le minuteur armé pendant la lecture du corps : supprimer le `clearTimeout` précoce
(`anthropic:128`, `openai:127`) et désarmer dans un `finally` couvrant l'ensemble du `try`. Le
`fetch` natif rejette alors `response.json()` avec `AbortError` quand le signal tombe en cours de
corps, et la branche existante (`anthropic:178`, `openai:177`) produit déjà `errorCode:"timeout"` :
aucun nouveau chemin d'erreur à écrire. Un `finally` couvre aussi uniformément le retour anticipé
`provider_error` (`!response.ok`), qui laisse aujourd'hui le minuteur courir jusqu'à son terme.

## Limites

Un seul défaut examiné, sur le point précis du mandat — ce n'est pas une revue des clients. Aucun
appel fournisseur réel, donc le comportement d'un vrai corps tronqué par le réseau n'est pas observé :
la sonde le simule fidèlement côté transport, et aucun résultat ici n'est présenté comme un appel
réel. Les quatre gates n'ont pas été rejoués sur du code inchangé. La lacune est aussi une lacune de
couverture — les tests existants injectent un rejet `AbortError` immédiat
(`anthropic-json-client.test.mjs:58,145`), ce qui n'exerce jamais la fenêtre du corps — mais je n'ai
ajouté ni modifié aucun test, conformément au mandat.
