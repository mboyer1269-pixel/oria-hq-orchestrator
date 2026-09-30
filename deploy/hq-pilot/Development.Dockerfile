# Dedicated validation image, not the live HQ or provider-login runner.
# Build context must be the reviewed source-only development snapshot.
FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /workspace/hq
ENV NEXT_TELEMETRY_DISABLED=1 HOME=/tmp/hq-validation
RUN chown node:node /workspace/hq
USER 1000:1000
COPY --chown=1000:1000 package.json package-lock.json ./
RUN npm ci --no-audit --no-fund && npm cache clean --force
# Owning the source directories also handles restrictive SCP permissions without
# a second full layer rewriting ownership of every dependency.
COPY --chown=1000:1000 . .
CMD ["npm", "test"]
