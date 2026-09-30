# Operator supplies a local alias for an inspected, qualified dependency image.
# Record the resolved image ID; a tag alone is not immutable.
# Build with --network=none; dependency manifests must match byte for byte.
ARG DEPENDENCY_IMAGE
FROM ${DEPENDENCY_IMAGE} AS dependencies
COPY package.json package-lock.json /tmp/expected-dependencies/
RUN cmp /workspace/hq/package.json /tmp/expected-dependencies/package.json \
    && cmp /workspace/hq/package-lock.json /tmp/expected-dependencies/package-lock.json

FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /workspace/hq
ENV NEXT_TELEMETRY_DISABLED=1 HOME=/tmp/hq-validation
RUN chown node:node /workspace/hq
COPY --from=dependencies --chown=1000:1000 /workspace/hq/node_modules ./node_modules
COPY --chown=1000:1000 . .
USER 1000:1000
CMD ["npm", "test"]
