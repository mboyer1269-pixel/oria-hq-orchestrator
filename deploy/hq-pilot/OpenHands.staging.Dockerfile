# Build from the file-verified development image; no dependency installation.
# Operator must record the resolved local image ID for SOURCE_IMAGE.
ARG SOURCE_IMAGE
FROM ${SOURCE_IMAGE} AS builder
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
RUN node scripts/check-docker-public-env.mjs && npm run build

FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=builder --chown=1000:1000 /workspace/hq/public ./public
COPY --from=builder --chown=1000:1000 /workspace/hq/.next/standalone ./
COPY --from=builder --chown=1000:1000 /workspace/hq/.next/static ./.next/static
COPY --from=builder --chown=1000:1000 /workspace/hq/config/openrouter.free-models.json ./config/openrouter.free-models.json
USER 1000:1000
CMD ["node", "server.js"]
