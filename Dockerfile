
FROM python:3.11-slim AS build

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir --upgrade "pip>=24.0" && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

RUN pytest -q

FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r app && useradd -r -g app -u 1000 app && \
    mkdir -p /app && \
    chown -R app:app /app

COPY --from=build --chown=app:app /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=build --chown=app:app /usr/local/bin /usr/local/bin

COPY --chown=app:app requirements.txt ./
COPY --chown=app:app src/ ./src/
COPY --chown=app:app pyproject.toml ./

RUN chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:${PATH}"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1

ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]
