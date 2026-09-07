FROM python:3.12.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    BUNDLE_ROOT=/workspace

WORKDIR /app
COPY frontier/uds_observatory_v2/requirements.txt /tmp/requirements.txt
RUN python -m pip install --requirement /tmp/requirements.txt \
    && addgroup --system --gid 10002 uds \
    && adduser --system --uid 10002 --ingroup uds --home /app uds

COPY frontier/uds_observatory_v2/ /app/
COPY . /workspace/
RUN chown -R uds:uds /app /workspace

USER 10002:10002
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=4s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=3).read()"

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--no-server-header"]
