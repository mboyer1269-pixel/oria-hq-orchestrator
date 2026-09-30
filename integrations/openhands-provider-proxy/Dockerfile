FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c
USER 0:0
RUN apt-get update && apt-get install -y --no-install-recommends squid socat ca-certificates \
    && dpkg-query -W > /opt/proxy-system-packages.txt \
    && rm -rf /var/lib/apt/lists/*
COPY squid.conf /etc/squid/squid.conf
COPY entrypoint.sh /opt/proxy-entrypoint.sh
RUN chmod 0555 /opt/proxy-entrypoint.sh
USER 10001:10001
ENTRYPOINT ["/bin/bash", "/opt/proxy-entrypoint.sh"]
