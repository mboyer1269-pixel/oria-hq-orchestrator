# Candidate runtime only. Parent supplies the immutable local permissions image.
# NOT built in this session: see RESULTS.md for exact state and reproduction.
ARG PERMISSION_BASE=oria-openhands-qualification:permissions1
FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c AS node_runtime
WORKDIR /opt/codex-acp
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm ls --all --json > /opt/codex-acp/dependencies-observed.json \
    && node -e "const fs=require('fs');const path=require('path'); \
        const pkgJson=require.resolve('@openai/codex-linux-x64/package.json'); \
        const bin=path.join(path.dirname(pkgJson),'vendor','x86_64-unknown-linux-musl','bin','codex'); \
        fs.accessSync(bin,fs.constants.X_OK);"

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
COPY --from=node_runtime /opt/codex-acp /opt/codex-acp
COPY codex-acp /usr/local/bin/codex-acp
RUN chmod 0555 /usr/local/bin/codex-acp \
    && mkdir -p /workspace /home/runner \
    && chown 10001:10001 /workspace /home/runner
ENV HOME=/home/runner LITELLM_LOCAL_MODEL_COST_MAP=True
USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["python"]
