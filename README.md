# FreeCourse

Plataforma local para organizar e assistir cursos em video com modulos, progresso de aulas e anotacoes vinculadas a timestamps. Frontend em React + Vite, backend em FastAPI, tudo orquestrado com Docker Compose.

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│  Vite+React │     │   FastAPI    │     │     16       │
│  :3000      │     │   :8000      │     │   :5432      │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐      ┌─────────────┐
                    │    MinIO     │      │  ./imports/ │
                    │  (S3-compat) │      │  (volume    │
                    │  :9000/:9001 │      │   local)    │
                    └──────────────┘      └─────────────┘
```

### Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18, Vite 5, TypeScript, Tailwind CSS, shadcn/ui, React Router v6, Lucide Icons |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Uvicorn |
| Banco de dados | PostgreSQL 16 |
| Armazenamento de videos | MinIO (compativel com S3) |
| Importacao YouTube | yt-dlp (sem API key) |
| Infraestrutura | Docker, Docker Compose |
| Testes | pytest + pytest-asyncio (84 testes) |

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
#    Frontend:      http://localhost:3000
#    Backend API:   http://localhost:8000/docs
#    MinIO Console: http://localhost:9001
```

## Variaveis de ambiente

Copie `.env.example` para `.env` e preencha os valores:

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
| `GOOGLE_API_KEY` | Chave da Google API — necessaria apenas para import via Drive | vazio |
| `IMPORTS_HOST_PATH` | Pasta do host montada para import local de videos | `./imports` |

> **Importante:** Caracteres especiais na senha do banco devem ser URL-encoded na `DATABASE_URL` (ex: `@` vira `%40`).

## Funcionalidades

- **Catalogo de cursos** com busca, thumbnails, barra de progresso e "Continuar Assistindo"
- **Modulos** — organize aulas em modulos dentro de cada curso
- **Progresso de aulas** — marque aulas como concluidas, progresso calculado automaticamente
- **Player de video** com controles customizados (play/pause, seek, volume, fullscreen)
  - Videos do MinIO via HTML5 com range requests (seeking)
  - Videos do YouTube via IFrame API com controles sobrepostos
  - Videos do Google Drive via iframe embed
- **Anotacoes por timestamp** — clique no timestamp para pular ao ponto do video
- **Exportacao para Notion** — envia anotacoes formatadas para um database Notion
- **Importacao em lote:**
  - **YouTube** — importa playlist inteira via yt-dlp (sem API key)
  - **Google Drive** — importa pasta publica (requer `GOOGLE_API_KEY`)
  - **Pasta local** — importe qualquer video baixado manualmente (sem API key)
- **Dark theme** com acentos em dourado/laranja e glass morphism

## Importacao de pasta local

Permite importar videos de uma pasta do seu computador para o MinIO sem precisar de API keys.

**Como usar:**

1. Coloque os videos na pasta `./imports/` (ou qualquer subpasta):
   ```
   imports/
     Modulo 1/
       01-introducao.mp4
       02-instalacao.mp4
     Modulo 2/
       03-conceitos.mp4
   ```

2. No Admin, expanda um curso > **Importar Aulas** > **Pasta Local**

3. Navegue pelas pastas, selecione o diretorio com os videos e clique **"Importar X video(s)"**

4. O upload e feito em tempo real com barra de progresso por arquivo

**Dica com Google Drive Desktop:** Se voce usa o app de sincronizacao do Drive, aponte o caminho diretamente:
```env
IMPORTS_HOST_PATH=G:/Meu Drive/Cursos
```

Extensoes suportadas: `.mp4`, `.mkv`, `.webm`, `.avi`, `.mov`, `.m4v`

## API Endpoints

Todos os endpoints usam o prefixo `/api/v1`. Documentacao interativa disponivel em `http://localhost:8000/docs`.

### Courses

| Metodo | Endpoint | Descricao |
|---|---|---|
| `GET` | `/courses` | Lista todos os cursos (com modulos e aulas) |
| `POST` | `/courses` | Cria um novo curso |
| `GET` | `/courses/{id}` | Retorna curso com modulos e aulas |
| `DELETE` | `/courses/{id}` | Remove curso (cascade) |
| `POST` | `/courses/{id}/upload-thumbnail` | Upload de thumbnail |
| `GET` | `/courses/{id}/thumbnail` | Stream da thumbnail |

### Modules

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/courses/{id}/modules` | Cria um modulo no curso |
| `PATCH` | `/modules/{id}` | Atualiza titulo/posicao do modulo |
| `DELETE` | `/modules/{id}` | Remove modulo (aulas ficam sem modulo) |

### Lessons

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/courses/{id}/lessons` | Adiciona aula ao curso |
| `PATCH` | `/lessons/{id}` | Atualiza titulo, descricao, modulo ou posicao |
| `DELETE` | `/lessons/{id}` | Remove aula |
| `POST` | `/lessons/{id}/upload-video` | Upload de video (multipart) |
| `GET` | `/lessons/{id}/video` | Stream de video (suporta Range) |
| `POST` | `/lessons/{id}/complete` | Marca aula como concluida |
| `DELETE` | `/lessons/{id}/complete` | Desmarca conclusao |

### Notes

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/lessons/{id}/notes` | Cria anotacao com timestamp do video |
| `GET` | `/lessons/{id}/notes` | Lista anotacoes da aula |
| `DELETE` | `/notes/{id}` | Remove anotacao |
| `POST` | `/lessons/{id}/export-notion` | Exporta anotacoes para o Notion |

### Imports

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/courses/{id}/import-youtube` | Importa playlist do YouTube (yt-dlp) |
| `POST` | `/courses/{id}/import-drive` | Importa pasta do Google Drive (requer API key) |
| `POST` | `/courses/{id}/import-local` | Importa pasta local → MinIO (stream NDJSON) |
| `GET` | `/imports/local/browse` | Lista arquivos/pastas do diretorio de imports |

## Modelos de dados

```
Course
├── id (UUID)
├── title
├── description (opcional)
├── thumbnail_url (opcional — path no MinIO ou URL externa)
├── created_at
├── modules[] ──▶ Module
│                 ├── id (UUID)
│                 ├── course_id (FK)
│                 ├── title
│                 ├── position
│                 └── lessons[] (aulas atribuidas a este modulo)
└── lessons[] ──▶ Lesson
                  ├── id (UUID)
                  ├── course_id (FK)
                  ├── module_id (FK, opcional)
                  ├── title
                  ├── description (opcional)
                  ├── video_url (path MinIO | "youtube:{id}" | "drive:{id}")
                  ├── video_source (computado: minio | youtube | google_drive | null)
                  ├── position
                  ├── completed (bool)
                  ├── completed_at (datetime, opcional)
                  ├── created_at
                  └── notes[] ──▶ Note
                                  ├── id (UUID)
                                  ├── lesson_id (FK)
                                  ├── content
                                  ├── video_timestamp (segundos)
                                  └── created_at
```

## Estrutura do projeto

```
meu-projeto-cursos/
├── docker-compose.yml           # Orquestracao dos servicos
├── .env.example                 # Template de variaveis de ambiente
├── imports/                     # Pasta para import local de videos (montada read-only)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI + lifespan
│   │   ├── api/
│   │   │   ├── router.py        # Agrega todos os sub-routers
│   │   │   ├── courses.py
│   │   │   ├── lessons.py
│   │   │   ├── modules.py
│   │   │   ├── notes.py
│   │   │   └── imports.py       # YouTube, Drive e Local import
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   └── database.py      # Engine async + AsyncSessionLocal
│   │   ├── models/              # SQLAlchemy: Course, Module, Lesson, Note
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   └── services/
│   │       ├── course_service.py
│   │       ├── lesson_service.py
│   │       ├── module_service.py
│   │       ├── note_service.py
│   │       ├── minio_service.py
│   │       ├── local_import_service.py  # Listagem + validacao de path
│   │       ├── youtube_service.py       # yt-dlp
│   │       ├── google_drive_service.py  # Drive API v3
│   │       └── notion_service.py
│   └── tests/                   # 84 testes (pytest-asyncio)
└── frontend/
    ├── Dockerfile
    ├── vite.config.ts
    └── src/
        ├── pages/
        │   ├── Index.tsx          # Catalogo + "Continuar Assistindo"
        │   ├── WatchCourse.tsx    # Player + modulos + notas
        │   ├── AdminCourses.tsx   # Gerenciamento completo
        │   └── NotFound.tsx
        ├── components/
        │   ├── Header.tsx         # Glass morphism, variante full/minimal
        │   ├── CourseCard.tsx     # Card com barra de progresso
        │   ├── ContinueWatchingCard.tsx
        │   ├── VideoPlayer.tsx    # Controles customizados MinIO/YouTube/Drive
        │   └── ui/                # shadcn/ui
        ├── lib/
        │   └── storage.ts         # API client completo
        └── types/
            └── course.ts          # Interfaces TypeScript
```

## Comandos uteis

```bash
# Subir todos os servicos
docker compose up -d --build

# Rebuild apenas o backend (apos mudar codigo Python)
docker compose up -d --build backend

# Rebuild apenas o frontend (apos mudar codigo React)
docker compose up -d --build frontend

# Ver logs em tempo real
docker compose logs -f backend
docker compose logs -f frontend

# Rodar testes do backend
docker compose exec backend pytest -q

# Rodar testes com cobertura
docker compose exec backend pytest --cov -q

# Acessar shell do backend
docker compose exec backend bash

# Parar tudo (preserva dados)
docker compose down

# Reset completo (apaga banco e arquivos MinIO)
docker compose down -v

# Verificar status dos containers
docker compose ps
```

## Testes

```bash
docker compose exec backend pytest -q
```

84 testes cobrindo: CRUD de cursos/modulos/aulas/notas, upload e stream de video, progresso de aulas, exportacao Notion, modelos SQLAlchemy.
