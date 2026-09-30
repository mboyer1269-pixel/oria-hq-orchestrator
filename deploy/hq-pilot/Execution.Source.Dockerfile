# Source-only exported context. Reuse installed dependencies only after an exact
# manifest comparison; never overlay a previous source tree with stale files.
ARG DEPENDENCIES_IMAGE
FROM ${DEPENDENCIES_IMAGE} AS dependencies
FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /workspace/hq
RUN chown 1000:1000 /workspace/hq
ENV NEXT_TELEMETRY_DISABLED=1 HOME=/tmp/hq-validation
COPY --from=dependencies --chown=1000:1000 /workspace/hq/node_modules ./node_modules
COPY --from=dependencies /workspace/hq/package.json /tmp/qualified-package.json
COPY --from=dependencies /workspace/hq/package-lock.json /tmp/qualified-package-lock.json
COPY --chown=1000:1000 . .
RUN cmp package.json /tmp/qualified-package.json && cmp package-lock.json /tmp/qualified-package-lock.json
RUN node -e 'const fs=require("node:fs"),crypto=require("node:crypto"),m=JSON.parse(fs.readFileSync("development-source-manifest.json"));for(const f of m.files){const b=fs.readFileSync(f.path);if(b.length!==f.size||crypto.createHash("sha256").update(b).digest("hex")!==f.sha256)throw Error("Source mismatch: "+f.path)}console.log(JSON.stringify({verifiedSourceFiles:m.files.length,testFiles:m.files.filter(f=>f.path.endsWith(".test.mjs")).length}))'
USER 1000:1000
CMD ["npm","test"]
