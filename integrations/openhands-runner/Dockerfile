# Operator must inspect and record the resolved local budget-runtime image ID.
ARG RUNTIME_IMAGE=oria-openhands-claude:budgets1
FROM ${RUNTIME_IMAGE}
USER 0:0
COPY --chown=10001:10001 dossier.py request_io.py workspace.py run_mission.py /runner/
COPY --chown=10001:10001 permission_transport.py /runner/
COPY --chown=10001:10001 provider_relay.py /runner/
COPY --chown=10001:10001 qualify_run_mission.py /runner/
COPY --chown=10001:10001 fixtures/hq-memory-dossier.json /runner/fixtures/
RUN mkdir -p /results && chown 10001:10001 /results
ENV PYTHONPATH=/runner:/extension OPENHANDS_SUPPRESS_BANNER=1
USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["python", "/runner/run_mission.py"]
