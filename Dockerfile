# EXPERT Dockerfile (hardened)
FROM python:3.11-slim@sha256:9358444059ed78e2975ada2c189f1c1a3144a5dab6f35bff8c981afb38946634

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system appgroup \
 && useradd --system --gid appgroup --create-home --home-dir /home/appuser appuser

COPY web/requirements.txt /tmp/web-requirements.txt
COPY vault/requirements.txt /tmp/vault-requirements.txt

RUN pip install --no-cache-dir -r /tmp/web-requirements.txt \
 && pip install --no-cache-dir -r /tmp/vault-requirements.txt \
 && rm -f /tmp/web-requirements.txt /tmp/vault-requirements.txt

COPY --chown=appuser:appgroup web /app/web
COPY --chown=appuser:appgroup vault /app/vault

USER appuser

CMD ["python","web/app.py"]
