FROM python:3.12.10-slim@sha256:720cd93d722c2b3ec7ef7a93ad8965f711be0cd81f90f488ba5d10b3782ef2de

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app
COPY observatory/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt \
    && useradd --create-home --uid 10001 observatory
COPY --chown=observatory:observatory . /app
USER 10001
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=2).read()"
CMD ["uvicorn", "observatory.app:app", "--host", "0.0.0.0", "--port", "7860", "--no-access-log"]
