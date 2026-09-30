FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 HOME=/tmp/home
RUN python -m pip install --no-cache-dir --only-binary=:all: openhands-sdk==1.50.0 \
    && python -m pip check \
    && python -m pip freeze > /opt/qualification-packages.txt
USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["python"]
