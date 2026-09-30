# Private HQ deployment qualification

Use the canonical HQ checkout `C:/Users/micha/Dev/Oria.HQ`. `snapshot.mjs` copies only explicit build files and source/public/config directories into a new immutable staging directory; it refuses symlinks, dotfiles below those roots and common credential/database file extensions. It records individual hashes. This is an inclusion boundary, not a comprehensive secret scanner.

The snapshot excludes `.env.local`, `.vercel`, AgentMemory, browser sessions, Git metadata, existing build output and local runtime data. Do not tar the whole development directory. Do not modify a snapshot after recording its manifest; generate another directory after source changes.

Next public Supabase settings are build inputs and must match the intended deployment. They are public client configuration, not service-role credentials. Runtime secrets must never be supplied as Docker build arguments or copied into the context. A successful build or health response alone does not validate owner login, persistence, provider dispatch or mission completion.

`compose.json` runs the verified image privately with no published ports, read-only root, non-root image user, dropped capabilities and resource limits. `runtime.env` is an external mode0600 file containing only the six required runtime settings; never copy it into this repository. Provider/dispatch bridges are explicitly off until qualified. The separate outbound network is not a domain allowlist.

Actual VPS qualification on 2026-09-29: source-v3 contains823 hashed files, build passed, image `sha256:e2a7cbc3f1e2973b71bc492f9fe858c377cc7656ebeee14f6a84593cbb1b15d1`. Initial runtime exposed two Docker defects: localhost healthcheck selected a refused address, and the dynamically loaded free-model catalog was absent from standalone output. The final image uses127.0.0.1 and copies the exact catalog. Both corrections passed actual container checks. Catalog presence does not establish current free availability or enable its disabled entries.

The service is Docker-healthy, health HTTP200 explicitly degraded for missing Inngest keys, missions redirect to login and unauthenticated orchestration API returns401. Owner login and mission flow remain unverified. A temporary SSH tunnel exposes it only on local127.0.0.1:3321; keep it alive for the pending user sign-in. No new database records or scheduled jobs were created by these tests. Before wider exposure, qualify owner authentication, exact workspace bindings, durable mission persistence, and the complete controlled agent execution path.

## Dependency failure discovered after startup

The configured Supabase project hostname failed DNS resolution on both the VPS and Windows. General supabase.com resolution succeeds. The connected Supabase MCP returned no projects; the dashboard requires user sign-in. Neither observation establishes deletion, pausing or ownership. The earlier request to log into HQ is superseded by the request to identify the original project through the Supabase dashboard. Do not create a replacement database or change owner credentials speculatively.

`readiness.mjs` is a separate read-only release gate: it checks Auth reachability and requests zero rows for the exact mission/ledger columns. It refuses redirects, bounds each request to five seconds, stops on the first failed dependency and never prints credentials or response bodies. It does not replace owner-login, RLS, write/CAS or agent-execution acceptance tests. Run it inside the application environment:

```sh
docker exec -i oria-hq-pilot-hq-1 node --input-type=module - < /opt/oria-hq-pilot/readiness.mjs
```

Actual result: ready=false, supabase_auth=dns_not_found. Three diagnostic tests pass locally. A healthy Docker liveness probe must not override this failed dependency gate.

## Audit HQ connecté — version privée v6

Supabase restauré et propriétaire connecté : les anciennes observations de blocage ci-dessus sont historiques. Auth/colonnes missions/ledger renvoient200 au contrôle read-only. Cette sonde ne teste pas les écritures.

Accueil recentré sur objectif/assistant/missions réelles/activité, filtres et détails; mémoire accessible avec sélecteur, écriture RAM refusée en production; journal détaillé dans /hq/activity. Dates Toronto harmonisées. Sidebar mobile nommée pour lecteurs d’écran; palette focusborné et retourfocus; débordement en-tête corrigé. Aucun LLM au rendu cash-action page. Contexte Memex advisory ne devient plus vérifié; seeds datés à la source et profils activés distingués des connexions.

Validation: suite complète3899pass0fail2skip (intégrationsMemexoptin); typecheck/lint/build/smokePASS, lint5warnings préexistants. Après corrections mobiles/fuseau, typecheck/lint et testsledger9pass, buildsLinuxVPS v5/v6PASS. Diffcheck propre. Tests navigateur authentifié: exemplesansenvoyer, filtres, agenda14j, paletteclavierfocus, choixconnaissance, étatPaperclipdésactivé, journalSupabase, filecashvide. Dimensions390/1440pasdébordementglobal. Pas de test d’inférence ni données créées.

Snapshot v6 829 fichiers; manifestSHA256 F9FEAAB370641ED7F02898BC7A20696914B234D5A331473DDB7095047E07589E. Image sha256:7cf5b4e72b7ce728106abf1640a7de5dcf0e71f4cc1003f902096e7c21dc200a. Nonrootoria, readonly, aucunportpublié. rollback compose.before-v4.json vers v3 disponible distant. Tunnel3321 conservé. Captures .validation/hq-audit-desktop.png et hq-audit-mobile.png. Rapport canonique Oria.HQ/docs/HQ-ARCHITECTURE-AUDIT-2026-09-29.md.

Limites: HQmono-propriétaire, vaultfichiersglobal à partitionner avantmultiworkspace; mémoire durableUI nonraccordée; dispatch/readPaperclip et Memexdésactivés; vraie missionagent toujours nonqualifiée. Aucune promesse zérobug. Aucuncommitpush. Goal existant blocked/inachevé empêche create_goal nouveau; erreur signalée, pas contournée par fauxcomplete.
