# Coherent execution artifacts — 2026-09-30

Qualification candidates only; not deployed to the active HQ.

## Identity

- Source manifest: `6225d49c0a9fa05e853318671dd8d0c4f35643fcb2434acf77404e231bc0cea1` (1137 files).
- Source/bridge image: `sha256:29d5b6644947ea6a6c2d8dc7c740dc8fe4bafcab57c3129765681b6632ced332`.
- Standalone web image: `sha256:5b3b486a13a9d34017c0fc7bc39153ece8d692a366eeeeb0cdfe6d7ccead2400`.

Both images derive from the same filtered source export. Dependency reuse requires identical package and lock files. The source build verifies exported file sizes and hashes. The consumer qualification accepts the pinned HQ image without substituting individual source files.

## Evidence and limits

The isolated consumer-service qualification passed with the coherent source image: canonical launch discovery, preparation, actual host consumer and Docker execution, durable failure recording, restart without replay, exclusive consumer lock and graceful idle stop. Claude reported authentication required; this is not a successful coding mission. Six ledger events survived database restart. This fixture does not prove production owner authentication or RLS.

The standalone production build succeeded. Runtime probe executed on the VPS on 2026-09-30: health 200; anonymous launch POST 401; anonymous tool route GET 401. Container UID 1000:1000, read-only root, network none, no published ports and no operational mounts. Required runtime configuration used only explicitly synthetic owner and Supabase values; no real credentials or model calls. Initial configuration-free probing returned 500 because the production environment guard correctly rejected missing required settings. No guard was weakened.

The probe does not establish database connectivity, authenticated owner flows, provider access, launch execution or application performance. It removes a runtime packaging uncertainty only.

## Remaining integration

Provision matching protected bridge/profile/source bindings; validate owner flows against disposable persistence; resolve the pending Claude consent and governed Memex project publication/read handle; then execute a real isolated coding mission with independent validation, interruption/recovery and measured resource use. Active services remain unchanged.
