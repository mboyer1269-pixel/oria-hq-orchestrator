FROM ghcr.io/paperclipai/paperclip@sha256:c735428fa81a719c0f8ca194bb345d0cdaaf3187f2fbecea1933a8d0513caf86
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-server \
 && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_* \
 && usermod --home /paperclip --shell /bin/sh --password '*' node \
 && mkdir -p /run/sshd /etc/oria-runner /workspace /var/lib/oria-ssh /opt/cursor \
 && chown node:node /workspace /var/lib/oria-ssh \
 && chmod 0755 /run/sshd /etc/oria-runner \
 && test "$(id -u node)" = 1000 \
 && command -v node && command -v gemini && command -v git && command -v tar
COPY --chmod=0644 sshd_config /etc/oria-runner/sshd_config
COPY --chmod=0755 entrypoint.sh /usr/local/bin/oria-runner-entrypoint
RUN printf '%s\n' 'export PATH=/opt/cursor:/paperclip/.local/bin:/usr/local/bin:/usr/bin:/bin' > /etc/profile.d/oria-runner-path.sh
ENV HOME=/paperclip PATH=/opt/cursor:/paperclip/.local/bin:/usr/local/bin:/usr/bin:/bin
WORKDIR /workspace
USER node
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/oria-runner-entrypoint"]
CMD []
