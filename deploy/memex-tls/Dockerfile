FROM node@sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2
WORKDIR /app
COPY --chown=root:root proxy.mjs /app/proxy.mjs
USER 1000:1000
CMD ["node", "/app/proxy.mjs"]
