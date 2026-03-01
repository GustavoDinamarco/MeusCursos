# backend/Dockerfile
# Imagem multi-stage: dev (com ferramentas de teste) e prod (enxuto).

# ---------------------------------------------------------------
# Stage base: Python + WORKDIR
# ---------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copia arquivos de dependências primeiro (cache de camadas Docker)
COPY pyproject.toml ./

# ---------------------------------------------------------------
# Stage dev: inclui dependências de teste + hot-reload
# ---------------------------------------------------------------
FROM base AS dev

# Instala TODAS as dependências (prod + dev)
RUN pip install --no-cache-dir ".[dev]"

# Copia o código fonte
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------
# Stage prod: apenas dependências de produção
# ---------------------------------------------------------------
FROM base AS prod

RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
