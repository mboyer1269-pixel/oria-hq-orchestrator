# Contexte Memex pour OpenHands — état vérifié

30 septembre 2026. Dépôts inspectés : `C:/Users/micha/Dev/Oria.HQ` et
`C:/Users/micha/Documents/memex-core`.

## Preuve disponible

Le test HQ `src/server/mcp/memex-live-contract.test.mjs` a été exécuté avec
MEMEX_CORE_TEST_ROOT pointant sur ce dépôt Memex canonique : 1 test réussi,
aucun test ignoré. Il utilise les vrais handlers avec une base en mémoire et
des données synthétiques. Il confirme filtrage de namespace, rejet de source
absente et evidence pack non fiable. Aucun fournisseur ni donnée active utilisés.

## Ce qui manque

Le chemin Joris appelle graph_query avec namespace et limit10; taskIntent n'est
pas un filtre de cette requête. Ne pas réutiliser ce contexte général comme
contexte de projet OpenHands. Le dossier OpenHands ne contient actuellement
ni ancre de projet ni snapshot mémoire approuvé.

L'outil context_pack est disponible dans Memex `src/mcp/tools.ts`, et non dans
le shim `src/mcp/server.ts`. Il accepte une entité centrale et des bornes de
taille. Le format JSON évite la branche d'enrichissement Vault du format Markdown.
Un graphe centré ne constitue pas en soi une isolation de projet au sein d'un
workspace : les voisins doivent respecter un périmètre explicitement établi.

## Décision d'intégration

Résoudre côté serveur un rattachement explicite mission/projet/mémoire; aucune
déduction depuis le titre ou le commit. Réutiliser transport et vérifications
de provenance existants. Limiter le contenu et enregistrer le snapshot exact
avec son empreinte dans le dossier confirmé. Une absence de correspondance doit
rester visible comme mémoire indisponible, sans injecter dix souvenirs généraux.
Ne pas inventer une révision distante : la date de récupération et le hash du
snapshot décrivent ce qui a réellement été reçu.

La mémoire AgentMemory locale de développement ne doit jamais être montée ni
interrogée comme mémoire runtime des agents ORIA.
