# Frontend — MeusCursos

Documentação completa da estrutura frontend para fins de remodelagem/redesign.

---

## Stack Tecnológica

| Tecnologia | Versão | Uso |
|---|---|---|
| React | 18.3.1 | Framework UI |
| TypeScript | 5.8.3 | Tipagem estática |
| Vite | 5.4.19 | Build tool (SWC compiler) |
| Tailwind CSS | 3.4.17 | Estilização utility-first |
| shadcn/ui | — | Componentes base (Radix UI) |
| React Router | 6.30.1 | Roteamento SPA |
| React Query | 5.83.0 | Cache e estado do servidor |
| React Hook Form | 7.61.1 | Formulários |
| Zod | 3.25.76 | Validação de schemas |
| Lucide React | 0.462.0 | Ícones |
| Sonner | 1.7.4 | Notificações toast |
| Recharts | 2.15.4 | Gráficos |

---

## Estrutura de Diretórios

```
src/
├── main.tsx                  # Bootstrap (ReactDOM.createRoot)
├── App.tsx                   # Router + Providers
├── index.css                 # Tema (CSS variables + fontes)
├── vite-env.d.ts
│
├── components/
│   ├── Header.tsx            # Barra de navegação superior
│   ├── NavLink.tsx           # Link com estado ativo
│   ├── CourseCard.tsx         # Card de curso (listagem)
│   └── ui/                   # 54 componentes shadcn/ui
│       ├── accordion.tsx
│       ├── alert-dialog.tsx
│       ├── alert.tsx
│       ├── aspect-ratio.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── breadcrumb.tsx
│       ├── button.tsx
│       ├── calendar.tsx
│       ├── card.tsx
│       ├── carousel.tsx
│       ├── chart.tsx
│       ├── checkbox.tsx
│       ├── collapsible.tsx
│       ├── command.tsx
│       ├── context-menu.tsx
│       ├── dialog.tsx
│       ├── drawer.tsx
│       ├── dropdown-menu.tsx
│       ├── form.tsx
│       ├── hover-card.tsx
│       ├── input-otp.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── menubar.tsx
│       ├── navigation-menu.tsx
│       ├── pagination.tsx
│       ├── popover.tsx
│       ├── progress.tsx
│       ├── radio-group.tsx
│       ├── resizable.tsx
│       ├── scroll-area.tsx
│       ├── select.tsx
│       ├── separator.tsx
│       ├── sheet.tsx
│       ├── sidebar.tsx
│       ├── skeleton.tsx
│       ├── slider.tsx
│       ├── sonner.tsx
│       ├── switch.tsx
│       ├── table.tsx
│       ├── tabs.tsx
│       ├── textarea.tsx
│       ├── toast.tsx
│       ├── toaster.tsx
│       ├── toggle-group.tsx
│       ├── toggle.tsx
│       └── tooltip.tsx
│
├── hooks/
│   └── use-mobile.tsx        # Hook: detecta viewport mobile (<768px)
│
├── lib/
│   ├── storage.ts            # Cliente API (fetch → FastAPI backend)
│   └── utils.ts              # cn() — merge de classes Tailwind
│
├── pages/
│   ├── Index.tsx              # Listagem de cursos + busca
│   ├── WatchCourse.tsx        # Player de vídeo + aulas + notas
│   ├── AdminCourses.tsx       # CRUD de cursos e aulas
│   └── NotFound.tsx           # Página 404
│
└── types/
    └── course.ts              # Interfaces TypeScript (Course, Lesson, Note, etc.)
```

---

## Rotas (App.tsx)

| Rota | Página | Descrição |
|---|---|---|
| `/` | `Index` | Listagem de cursos com busca |
| `/course/:courseId` | `WatchCourse` | Player de vídeo, lista de aulas, notas |
| `/admin` | `AdminCourses` | Gerenciamento de cursos e aulas |
| `*` | `NotFound` | 404 |

**Providers configurados no App.tsx:**
- `QueryClientProvider` — React Query
- `TooltipProvider` — Radix UI tooltips
- `Toaster` — shadcn/ui toasts
- `Sonner` — Notificações toast
- `BrowserRouter` — React Router

---

## Tipos (types/course.ts)

```typescript
Course {
  id: string
  title: string
  description: string | null
  thumbnail_url: string | null
  created_at: string
}

CourseWithLessons extends Course {
  lessons: Lesson[]
}

Lesson {
  id: string
  course_id: string
  title: string
  description: string | null
  video_url: string | null
  video_source: "minio" | "google_drive" | "youtube" | null
  created_at: string
}

Note {
  id: string
  lesson_id: string
  content: string
  video_timestamp: number
  created_at: string
}

CreateCoursePayload   { title, description? }
CreateLessonPayload   { title, description? }
UpdateLessonPayload   { title?, description? }
CreateNotePayload     { content, video_timestamp }
ImportResult          { imported: number, lessons: Lesson[] }
```

---

## Cliente API (lib/storage.ts)

Base URL: `VITE_API_URL` ou `http://localhost:8000`
Prefixo: `/api/v1`

| Função | Método | Endpoint | Retorno |
|---|---|---|---|
| `getCourses()` | GET | `/courses` | `Course[]` |
| `getCourse(id)` | GET | `/courses/{id}` | `CourseWithLessons` |
| `createCourse(data)` | POST | `/courses` | `Course` |
| `deleteCourse(id)` | DELETE | `/courses/{id}` | `void` |
| `uploadCourseThumbnail(id, file)` | POST | `/courses/{id}/upload-thumbnail` | `Course` |
| `courseThumbnailUrl(course)` | — | Helper local | `string \| null` |
| `createLesson(courseId, data)` | POST | `/courses/{courseId}/lessons` | `Lesson` |
| `uploadVideo(lessonId, file)` | POST | `/lessons/{lessonId}/upload-video` | `Lesson` |
| `updateLesson(lessonId, data)` | PATCH | `/lessons/{lessonId}` | `Lesson` |
| `deleteLesson(lessonId)` | DELETE | `/lessons/{lessonId}` | `void` |
| `videoStreamUrl(lessonId)` | — | Helper local | `string` |
| `getNotes(lessonId)` | GET | `/lessons/{lessonId}/notes` | `Note[]` |
| `createNote(lessonId, data)` | POST | `/lessons/{lessonId}/notes` | `Note` |
| `deleteNote(noteId)` | DELETE | `/notes/{noteId}` | `void` |
| `importFromDrive(courseId, url)` | POST | `/courses/{courseId}/import-drive` | `ImportResult` |
| `importFromYoutube(courseId, url)` | POST | `/courses/{courseId}/import-youtube` | `ImportResult` |

**Tratamento de erros:** Classe `ApiError` com `status` e `message`. Parseia JSON do backend ou usa `statusText` como fallback.

---

## Componentes Customizados

### Header (`components/Header.tsx`)

Barra de navegação fixa no topo.

- **Props:** Nenhuma
- **Ícones usados:** `BookOpen`, `Home`, `Plus` (lucide-react)
- **Comportamento:**
  - Logo "MeusCursos" com ícone à esquerda
  - Links: Home (`/`) e Gerenciar (`/admin`)
  - Destaque visual no link ativo via `useLocation()`
- **Classes-chave:**
  - `sticky top-0 z-50`
  - `bg-background/80 backdrop-blur-xl`
  - `border-b border-border`

---

### NavLink (`components/NavLink.tsx`)

Wrapper do `NavLink` do React Router com suporte a classes condicionais.

- **Props:**
  - `className?: string` — classe padrão
  - `activeClassName?: string` — classe quando rota ativa
  - `pendingClassName?: string` — classe quando rota carregando
- **Usa:** `React.forwardRef`, `cn()` para merge de classes

---

### CourseCard (`components/CourseCard.tsx`)

Card de exibição de curso usado na listagem principal.

- **Props:** `{ course: Course }`
- **Ícones usados:** `Play`, `BookOpen` (lucide-react)
- **Imports de lib:** `courseThumbnailUrl` de `storage.ts`
- **Comportamento:**
  - Link para `/course/{id}`
  - Thumbnail do curso (se disponível) ou fallback com gradiente + inicial do título
  - Overlay com botão Play no hover
  - Título (1 linha), descrição (2 linhas), data de criação (pt-BR)
- **Gradientes determinísticos:** 8 gradientes baseados no hash do título
- **Classes-chave:**
  - `card-gradient rounded-xl border border-border`
  - `hover:border-primary/40 hover:glow-shadow`
  - `animate-fade-in`
  - `aspect-video` para proporção do thumbnail

---

## Páginas

### Index (`pages/Index.tsx`)

Página principal com listagem de cursos.

- **Estado:**
  - `courses: Course[]` — lista de cursos
  - `search: string` — filtro de busca
  - `loading: boolean`
- **Comportamento:**
  - Busca cursos no mount via `getCourses()`
  - Filtro em tempo real por título e descrição (case-insensitive)
  - Grid responsivo: 1 col (mobile) → 2 (sm) → 3 (lg) → 4 (xl)
  - Estados: loading (spinner), vazio (mensagem), resultados (grid de CourseCards)
- **Ícones usados:** `Search`, `BookOpen` (lucide-react)
- **Layout:**
  ```
  Header
  Hero: título "Seus Cursos" (gradiente) + descrição + input de busca
  Grid de CourseCards ou estado vazio
  ```

---

### WatchCourse (`pages/WatchCourse.tsx`)

Player de vídeo com lista de aulas e sistema de notas.

- **Parâmetro de rota:** `courseId`
- **Estado principal:**
  - `course: CourseWithLessons | null`
  - `activeLesson: Lesson | null`
  - `notes: Note[]`
  - `newNote: string`
  - `loading: boolean`
- **Refs:**
  - `videoRef` — elemento `<video>` HTML5
  - `ytPlayerRef` — instância YouTube IFrame Player
  - `ytContainerRef` — container div para player YouTube
- **Fontes de vídeo suportadas:**
  - **MinIO:** `<video>` nativo com URL de streaming
  - **Google Drive:** `<iframe>` com embed do Drive
  - **YouTube:** YouTube IFrame Player API (controlável via JS)
  - **Nenhum:** Placeholder com ícone
- **Sistema de notas:**
  - Captura timestamp atual do vídeo ao criar nota
  - Clique no timestamp faz seek para o momento
  - Suporte Ctrl+Enter para submeter
  - Delete individual de notas
- **YouTube IFrame API:**
  - Loader singleton (carrega script uma vez)
  - `getCurrentTime()` para timestamp
  - `seekTo(seconds, true)` para navegação
  - Lifecycle: create/destroy ao trocar de aula
- **Ícones usados:** `ArrowLeft`, `Play`, `Video`, `BookOpen`, `Clock`, `Trash2`, `Send` (lucide-react)
- **Layout:**
  ```
  Header
  Link "voltar"
  Grid 2 colunas (lg):
    Esquerda:
      Player de vídeo (adaptativo por fonte)
      Info da aula ativa (título + descrição)
      Lista de aulas (ScrollArea numerada)
    Direita (sticky):
      Lista de notas com timestamps
      Formulário de nova nota (textarea + botão)
  ```

---

### AdminCourses (`pages/AdminCourses.tsx`)

Interface completa de gerenciamento (CRUD).

- **Estado:**
  - Cursos: `courses`, `loading`, `showForm`, `newTitle`, `newDescription`, `saving`
  - Curso expandido: `expandedCourseId`, `expandedCourse`
  - Aulas: `lessonTitle`, `lessonDescription`, `addingLesson`
  - Upload de vídeo: `uploadingLessonId`, `fileInputRef`
  - Upload de thumbnail: `uploadingThumbnailId`, `thumbnailInputRef`
  - Importação: `importMode` (`"drive" | "youtube" | null`), `importUrl`, `importing`
  - Edição inline: `editingLessonId`, `editTitle`, `editDescription`, `savingEdit`
  - Deleção: `deletingLessonId`
- **Operações:**
  - **Cursos:** criar, deletar, upload de thumbnail
  - **Aulas:** criar, editar (inline), deletar, upload de vídeo
  - **Importação em lote:** Google Drive (URL de pasta) e YouTube (URL de playlist)
- **Ícones usados:** `Plus`, `Trash2`, `ChevronDown`, `ChevronRight`, `Upload`, `Video`, `FolderOpen`, `Youtube`, `Loader2`, `Camera`, `Pencil`, `X`, `Check`, `BookOpen` (lucide-react)
- **Imports de lib:** `getCourses`, `getCourse`, `createCourse`, `deleteCourse`, `createLesson`, `uploadVideo`, `updateLesson`, `deleteLesson`, `importFromDrive`, `importFromYoutube`, `uploadCourseThumbnail`, `courseThumbnailUrl`
- **Toasts:** `sonner` para feedback de todas as operações
- **Layout:**
  ```
  Header
  Título + botão "Novo Curso"

  [Formulário de criação — condicional]
    Input título (obrigatório)
    Textarea descrição
    Botões criar/cancelar

  [Lista de cursos]
    Card de curso:
      Seta expandir/colapsar
      Thumbnail (clicável para upload) ou fallback
      Título + data de criação
      Botões "Gerenciar" e "Deletar"

      [Conteúdo expandido]
        Lista de aulas:
          Número | Título | Status do vídeo | Botões (editar/deletar/upload)
          [Formulário inline de edição — condicional]
        Formulário adicionar aula
        Seção de importação:
          Toggle Drive/YouTube
          Input URL + botão importar

  [Inputs file escondidos]
    input video (video/*)
    input thumbnail (image/jpeg, image/png, image/webp)
  ```

---

### NotFound (`pages/NotFound.tsx`)

Página 404.

- Exibe "404" e "Page not found"
- Link para voltar à home
- Layout centralizado (`min-h-screen flex items-center justify-center`)

---

## Sistema de Tema (index.css)

### Fontes

- **Sans-serif:** Inter (300, 400, 500, 600, 700, 800)
- **Monospace:** JetBrains Mono (400, 500)

### Paleta de Cores (CSS Variables — HSL)

| Variável | Valor HSL | Descrição |
|---|---|---|
| `--background` | `220 20% 7%` | Fundo principal (azul muito escuro) |
| `--foreground` | `40 10% 92%` | Texto principal (off-white) |
| `--primary` | `38 92% 55%` | Cor de destaque (laranja/âmbar) |
| `--primary-foreground` | `220 20% 7%` | Texto sobre primary |
| `--secondary` | `220 16% 16%` | Fundo secundário |
| `--muted` | `220 14% 16%` | Elementos sutis |
| `--muted-foreground` | `220 10% 55%` | Texto sutil |
| `--accent` | `38 92% 55%` | Destaque (= primary) |
| `--destructive` | `0 72% 51%` | Vermelho para ações destrutivas |
| `--border` | `220 14% 18%` | Bordas |
| `--ring` | `38 92% 55%` | Focus ring (= primary) |
| `--radius` | `0.75rem` | Border radius padrão |
| `--card` | `220 18% 10%` | Fundo de cards |
| `--popover` | `220 18% 12%` | Fundo de popovers |

### Gradientes e Efeitos Customizados

```css
--gradient-hero: linear-gradient(135deg, hsl(38,92%,55%), hsl(28,95%,48%))
--gradient-card: linear-gradient(145deg, hsl(220,18%,12%), hsl(220,18%,9%))
--shadow-glow: 0 0 40px -10px hsl(38 92% 55% / 0.3)
```

| Classe utilitária | Efeito |
|---|---|
| `.text-gradient` | Gradiente hero aplicado ao texto |
| `.card-gradient` | Fundo com gradiente de card |
| `.glow-shadow` | Sombra brilhante laranja |

### Animações (tailwind.config.ts)

| Nome | Efeito |
|---|---|
| `accordion-down` | Expand (Radix collapsible) |
| `accordion-up` | Collapse (Radix collapsible) |
| `fade-in` | Fade + translate-y (0.5s ease-out) |

---

## Componentes shadcn/ui Instalados (54)

Todos em `src/components/ui/`. Baseados em Radix UI primitives com Tailwind CSS.

**Mais utilizados pelo projeto:**
- `button` — botões em todas as páginas
- `input` / `textarea` — formulários
- `scroll-area` — listas roláveis (aulas, notas)
- `toast` / `toaster` / `sonner` — notificações
- `tooltip` — dicas de hover
- `badge` — indicadores de status
- `separator` — divisores visuais
- `dialog` / `alert-dialog` — modais e confirmações
- `card` — containers de conteúdo
- `form` / `label` — formulários com React Hook Form
- `skeleton` — estados de loading
- `tabs` — navegação por abas

**Instalados mas sem uso direto ainda:**
accordion, aspect-ratio, avatar, breadcrumb, calendar, carousel, chart, checkbox, collapsible, command, context-menu, drawer, dropdown-menu, hover-card, input-otp, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, select, sheet, sidebar, slider, switch, table, toggle, toggle-group

---

## Hook Customizado

### `useIsMobile` (`hooks/use-mobile.tsx`)

- Retorna `boolean` — `true` se viewport < 768px
- Usa `window.matchMedia` com listener de mudança
- Breakpoint alinhado com Tailwind `md`

---

## Configuração de Build (vite.config.ts)

- **Compilador:** SWC (via `@vitejs/plugin-react-swc`)
- **Dev server:** `0.0.0.0:3000`
- **Alias:** `@` → `./src`

---

## Dependências Notáveis

| Pacote | Uso |
|---|---|
| `@tanstack/react-query` | Cache de dados do servidor, refetch automático |
| `react-hook-form` + `zod` | Formulários com validação tipada |
| `class-variance-authority` | Variantes de componentes (usado pelos shadcn/ui) |
| `clsx` + `tailwind-merge` | Merge inteligente de classes Tailwind (`cn()`) |
| `date-fns` + `react-day-picker` | Manipulação de datas e calendar picker |
| `embla-carousel-react` | Carousel (shadcn carousel) |
| `recharts` | Gráficos (shadcn chart) |
| `vaul` | Drawer (shadcn drawer) |
| `cmdk` | Command palette (shadcn command) |
| `next-themes` | Alternância de tema (light/dark) |
| `react-resizable-panels` | Painéis redimensionáveis |

---

## Mapa de Dependências entre Componentes

```
App.tsx
├── Header.tsx
│   └── NavLink.tsx
├── Index.tsx
│   ├── Header.tsx
│   ├── CourseCard.tsx
│   │   └── lib/storage.ts (courseThumbnailUrl)
│   └── lib/storage.ts (getCourses)
├── WatchCourse.tsx
│   ├── Header.tsx
│   ├── lib/storage.ts (getCourse, getNotes, createNote, deleteNote, videoStreamUrl)
│   └── YouTube IFrame Player API (externo)
├── AdminCourses.tsx
│   ├── Header.tsx
│   └── lib/storage.ts (todas as funções CRUD + import)
└── NotFound.tsx
```

---

## Notas para Remodelagem

1. **Tema é 100% dark** — todas as variáveis CSS são otimizadas para fundo escuro. Para suportar light mode, adicionar bloco `:root` ou `.light` com valores claros.

2. **Cor primária é laranja/âmbar** (`hsl(38, 92%, 55%)`) — usada em botões, links ativos, focus rings e gradientes.

3. **Páginas são monolíticas** — `WatchCourse.tsx` e `AdminCourses.tsx` contêm toda a lógica inline (sem componentes filhos extraídos). Para remodelagem, considerar extrair:
   - `LessonList` — lista de aulas reutilizável
   - `NotePanel` — painel de notas
   - `VideoPlayer` — componente de player adaptativo
   - `ImportSection` — seção de importação em lote
   - `CourseForm` — formulário de criação de curso
   - `LessonItem` — item individual de aula com ações

4. **shadcn/ui** — muitos componentes instalados não são usados. Podem ser removidos para reduzir bundle ou mantidos para uso futuro.

5. **React Query** está configurado mas não utilizado com hooks `useQuery`/`useMutation` — as pages fazem `fetch` manual via `useEffect` + `useState`. Migrar para React Query hooks traria cache automático, loading/error states, e refetch.

6. **Sem SSR/SSG** — é um SPA puro via Vite. Para SEO ou performance inicial, avaliar Next.js ou Remix.

7. **Responsividade** — grid de cursos é responsivo, mas `WatchCourse` em mobile pode precisar de layout vertical (player em cima, aulas/notas embaixo via tabs).
