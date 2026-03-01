# FreeCourse

Plataforma local para organizar e assistir cursos em video com anotacoes vinculadas a timestamps. Frontend em React + Vite, backend em FastAPI, tudo orquestrado com Docker Compose.

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend   │────▶│   Backend    │────▶│  PostgreSQL   │
│  Vite+React │     │   FastAPI    │     │     16        │
│  :3000      │     │   :8000      │     │   :5432       │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    MinIO     │
                    │  (S3-compat) │
                    │  :9000/:9001 │
                    └──────────────┘
```

### Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18, Vite 5, TypeScript, Tailwind CSS, shadcn/ui, React Router v6 |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Uvicorn |
| Banco de dados | PostgreSQL 16 |
| Armazenamento de videos | MinIO (compativel com S3) |
| Infraestrutura | Docker, Docker Compose |
| Testes | pytest + pytest-asyncio (backend), Vitest (frontend) |

## Pre-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando
- Git

## Inicio rapido

```bash
# 1. Clone o repositorio
git clone <url-do-repo>
cd meu-projeto-cursos

# 2. Copie o arquivo de ambiente e ajuste as senhas
cp .env.example .env

# 3. Suba todos os servicos
docker compose up -d --build

# 4. Acesse
#    Frontend: http://localhost:3000
#    Backend API: http://localhost:8000/docs
#    MinIO Console: http://localhost:9001
```

## Variaveis de ambiente

Copie `.env.example` para `.env` e preencha os valores. As principais variaveis:

| Variavel | Descricao | Padrao |
|---|---|---|
| `POSTGRES_USER` | Usuario do PostgreSQL | `courseuser` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL | (definir) |
| `POSTGRES_DB` | Nome do banco | `coursedb` |
| `DATABASE_URL` | URL de conexao SQLAlchemy | (gerada das vars acima) |
| `MINIO_ROOT_USER` | Usuario admin do MinIO | `minio_admin` |
| `MINIO_ROOT_PASSWORD` | Senha do MinIO | (definir) |
| `SECRET_KEY` | Chave secreta do backend | (definir) |
| `FRONTEND_PORT` | Porta do frontend | `3000` |
| `BACKEND_PORT` | Porta do backend | `8000` |
| `NOTION_API_KEY` | Chave da API do Notion (opcional) | vazio |
| `NOTION_DATABASE_ID` | ID do database Notion (opcional) | vazio |

> **Importante:** Caracteres especiais na senha do banco devem ser URL-encoded na `DATABASE_URL` (ex: `@` vira `%40`).

## API Endpoints

Todos os endpoints usam o prefixo `/api/v1`. Documentacao interativa disponivel em `http://localhost:8000/docs`.

### Courses

| Metodo | Endpoint | Descricao |
|---|---|---|
| `GET` | `/courses` | Lista todos os cursos |
| `POST` | `/courses` | Cria um novo curso |
| `GET` | `/courses/{id}` | Retorna curso com suas aulas |
| `DELETE` | `/courses/{id}` | Remove curso (cascade para aulas e notas) |

### Lessons

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/courses/{id}/lessons` | Adiciona aula ao curso |
| `GET` | `/lessons/{id}` | Detalhes de uma aula |
| `POST` | `/lessons/{id}/upload-video` | Upload de video (multipart) |
| `GET` | `/lessons/{id}/video` | Stream de video (suporta Range) |

### Notes

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/lessons/{id}/notes` | Cria anotacao com timestamp do video |
| `GET` | `/lessons/{id}/notes` | Lista anotacoes da aula |
| `DELETE` | `/notes/{id}` | Remove anotacao |
| `POST` | `/lessons/{id}/export-notion` | Exporta anotacoes para o Notion |

## Modelos de dados

```
Course
├── id (UUID)
├── title (string)
├── description (string, opcional)
├── created_at (datetime)
└── lessons[] ──▶ Lesson
                  ├── id (UUID)
                  ├── course_id (UUID, FK)
                  ├── title (string)
                  ├── description (string, opcional)
                  ├── video_url (string, opcional - path no MinIO)
                  ├── created_at (datetime)
                  └── notes[] ──▶ Note
                                  ├── id (UUID)
                                  ├── lesson_id (UUID, FK)
                                  ├── content (string)
                                  ├── video_timestamp (int, segundos)
                                  └── created_at (datetime)
```

## Estrutura do projeto

```
meu-projeto-cursos/
├── docker-compose.yml          # Orquestracao dos 5 servicos
├── .env.example                # Template de variaveis de ambiente
├── backend/
│   ├── Dockerfile              # Multi-stage: dev (com testes) / prod
│   ├── pyproject.toml          # Dependencias Python
│   ├── app/
│   │   ├── main.py             # Entry point FastAPI + lifespan
│   │   ├── api/                # Routers (courses, lessons, notes)
│   │   ├── core/               # Config e database engine
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas (request/response)
│   │   └── services/           # Logica de negocio (CRUD, MinIO, Notion)
│   └── tests/                  # 84 testes (pytest)
└── frontend/
    ├── Dockerfile              # Multi-stage: deps → build → serve
    ├── vite.config.ts          # Configuracao Vite (porta 3000)
    ├── src/
    │   ├── pages/              # Index, WatchCourse, AdminCourses, NotFound
    │   ├── components/         # CourseCard, Header + shadcn/ui
    │   ├── lib/                # API client (storage.ts), utils
    │   └── types/              # TypeScript interfaces
    └── package.json
```

## Comandos uteis

```bash
# Subir todos os servicos
docker compose up -d --build

# Ver logs de um servico
docker compose logs -f backend
docker compose logs -f frontend

# Rodar testes do backend
docker compose exec backend pytest -q

# Parar tudo
docker compose down

# Reset completo (apaga banco e arquivos do MinIO)
docker compose down -v

# Verificar status dos containers
docker compose ps -a
```

## Testes

### Backend (84 testes)

```bash
docker compose exec backend pytest -q
```

Cobre: CRUD de cursos, aulas e notas, upload/stream de video, exportacao Notion, modelos SQLAlchemy.

### Frontend

```bash
# Rodar testes em container isolado
docker run --rm -v "$(pwd)/frontend:/app" -w /app node:20-alpine \
  sh -c "npm install && npx vitest run"
```

> **Nota (Git Bash no Windows):** Adicione `export MSYS_NO_PATHCONV=1` antes de comandos Docker que usam paths com `$(pwd)`.

## Funcionalidades

- **Catalogo de cursos** com busca e cards com gradiente deterministico
- **Player de video** com streaming via MinIO (suporta seek via Range headers)
- **Anotacoes por timestamp** — clique no timestamp para pular ao ponto do video
- **Gerenciamento** — criar cursos, adicionar aulas, upload de video
- **Exportacao para Notion** — envia anotacoes formatadas para um database Notion
- **Dark theme** com acentos em dourado/laranja e componentes shadcn/ui
