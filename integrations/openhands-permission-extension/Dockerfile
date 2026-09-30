FROM oria-openhands-qualification:sdk1.50.0
USER root
COPY *.py /extension/
RUN python /extension/apply_patch.py
ENV LITELLM_LOCAL_MODEL_COST_MAP=True
USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["python", "/extension/qualify_instance_policies.py"]
