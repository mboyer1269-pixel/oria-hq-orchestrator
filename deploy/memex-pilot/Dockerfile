# Official node:22-bookworm-slim linux/amd64 manifest resolved 2026-09-29.
FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2 AS dependencies
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ && rm -rf /var/lib/apt/lists/*
COPY --from=memex_source package.json package-lock.json ./
RUN npm ci --omit=dev && node -e "const D=require('better-sqlite3');const d=new D(':memory:');d.exec('CREATE VIRTUAL TABLE probe USING fts5(content)');d.close()"

FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=memex_source package.json package-lock.json ./
COPY --from=memex_source src ./src
COPY --from=memex_source fixtures/mcp-tools-list.expected.json fixtures/mcp-resources-list.expected.json ./fixtures/
COPY entrypoint.mjs acceptance.mjs mint-read-handle.mjs mint-proposal-handle.mjs ./pilot/
RUN chmod -R a+rX /app/src /app/fixtures && mkdir -p /runtime/graph /runtime/intake /runtime/vault && chown -R node:node /runtime
ENV NODE_ENV=production HOME=/tmp
USER 1000:1000
ENTRYPOINT ["node", "--experimental-strip-types", "/app/pilot/entrypoint.mjs"]
