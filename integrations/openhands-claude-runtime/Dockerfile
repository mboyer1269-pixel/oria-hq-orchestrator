# Candidate runtime only. Parent supplies the immutable local permissions image.
ARG PERMISSION_BASE=oria-openhands-qualification:permissions1
FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c AS node_runtime
WORKDIR /opt/claude-acp
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm ls --all --json > /opt/claude-acp/dependencies-observed.json \
    && node -e "const fs=require('fs'); const p=require.resolve('@anthropic-ai/claude-agent-sdk-linux-x64/claude'); fs.accessSync(p,fs.constants.X_OK)"

FROM ${PERMISSION_BASE}
USER 0:0
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && dpkg-query -W > /opt/runtime-system-packages.txt \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node_runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node_runtime /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
COPY --from=node_runtime /opt/claude-acp /opt/claude-acp
COPY claude-agent-acp /usr/local/bin/claude-agent-acp
RUN chmod 0555 /usr/local/bin/claude-agent-acp \
    && mkdir -p /workspace /home/runner \
    && chown 10001:10001 /workspace /home/runner
ENV HOME=/home/runner LITELLM_LOCAL_MODEL_COST_MAP=True
USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["python"]
