import { useState, useEffect, useRef } from "react";
import Header from "@/components/Header";
import {
  getCourses,
  getCourse,
  createCourse,
  deleteCourse as apiDeleteCourse,
  createLesson,
  uploadVideo,
  importFromDrive,
  importFromYoutube,
  browseLocalFolder,
  importFromLocalFolder,
  updateLesson,
  deleteLesson as apiDeleteLesson,
  uploadCourseThumbnail,
  courseThumbnailUrl,
  createModule as apiCreateModule,
  deleteModule as apiDeleteModule,
} from "@/lib/storage";
import { CourseWithLessons, Lesson, Module, LocalFolderEntry, LocalImportProgress } from "@/types/course";
import { Textarea } from "@/components/ui/textarea";
import {
  Plus,
  Trash2,
  Save,
  BookOpen,
  X,
  ChevronDown,
  ChevronRight,
  Upload,
  Loader2,
  Video,
  Youtube,
  Link2,
  Pencil,
  Camera,
  Layers,
  FolderOpen,
  HardDrive,
} from "lucide-react";
import { toast } from "sonner";

const AdminCourses = () => {
  const [courses, setCourses] = useState<CourseWithLessons[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [saving, setSaving] = useState(false);

  // Expanded course management
  const [expandedCourseId, setExpandedCourseId] = useState<string | null>(null);
  const [expandedCourse, setExpandedCourse] = useState<CourseWithLessons | null>(null);

  // Add lesson form
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonDescription, setLessonDescription] = useState("");
  const [lessonModuleId, setLessonModuleId] = useState<string>("");
  const [addingLesson, setAddingLesson] = useState(false);

  // Add module form
  const [moduleTitle, setModuleTitle] = useState("");
  const [addingModule, setAddingModule] = useState(false);

  // Video upload
  const [uploadingLessonId, setUploadingLessonId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Thumbnail upload
  const [uploadingThumbnailId, setUploadingThumbnailId] = useState<string | null>(null);
  const thumbnailInputRef = useRef<HTMLInputElement>(null);

  // Bulk import
  const [importMode, setImportMode] = useState<"drive" | "youtube" | "local" | null>(null);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);

  // Local folder browse
  const [localBrowsePath, setLocalBrowsePath] = useState("");
  const [localEntries, setLocalEntries] = useState<LocalFolderEntry[]>([]);
  const [localAvailable, setLocalAvailable] = useState(false);
  const [localBrowseLoading, setLocalBrowseLoading] = useState(false);
  const [localProgress, setLocalProgress] = useState<LocalImportProgress | null>(null);

  // Edit / delete lesson
  const [editingLessonId, setEditingLessonId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingLessonId, setDeletingLessonId] = useState<string | null>(null);

  const refreshCourses = () => {
    getCourses()
      .then(setCourses)
      .catch(() => setCourses([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshCourses();
  }, []);

  const refreshExpanded = async (courseId: string) => {
    try {
      const full = await getCourse(courseId);
      setExpandedCourse(full);
    } catch {
      // silently fail
    }
  };

  const handleCreateCourse = async () => {
    if (!newTitle.trim()) {
      toast.error("O titulo e obrigatorio");
      return;
    }
    setSaving(true);
    try {
      await createCourse({
        title: newTitle.trim(),
        description: newDescription.trim() || null,
      });
      setNewTitle("");
      setNewDescription("");
      setShowForm(false);
      refreshCourses();
      toast.success("Curso criado com sucesso!");
    } catch {
      toast.error("Erro ao criar curso");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCourse = async (id: string) => {
    try {
      await apiDeleteCourse(id);
      if (expandedCourseId === id) {
        setExpandedCourseId(null);
        setExpandedCourse(null);
      }
      refreshCourses();
      toast.success("Curso removido");
    } catch {
      toast.error("Erro ao remover curso");
    }
  };

  const handleToggleExpand = async (courseId: string) => {
    if (expandedCourseId === courseId) {
      setExpandedCourseId(null);
      setExpandedCourse(null);
      return;
    }
    setExpandedCourseId(courseId);
    try {
      const full = await getCourse(courseId);
      setExpandedCourse(full);
    } catch {
      toast.error("Erro ao carregar curso");
      setExpandedCourseId(null);
    }
  };

  const handleAddLesson = async () => {
    if (!lessonTitle.trim() || !expandedCourseId) return;
    setAddingLesson(true);
    try {
      const lesson = await createLesson(expandedCourseId, {
        title: lessonTitle.trim(),
        description: lessonDescription.trim() || null,
      });
      // If a module is selected, assign the lesson to it
      if (lessonModuleId) {
        await updateLesson(lesson.id, { module_id: lessonModuleId });
      }
      setLessonTitle("");
      setLessonDescription("");
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      toast.success("Aula adicionada!");
    } catch {
      toast.error("Erro ao adicionar aula");
    } finally {
      setAddingLesson(false);
    }
  };

  const handleAddModule = async () => {
    if (!moduleTitle.trim() || !expandedCourseId) return;
    setAddingModule(true);
    try {
      await apiCreateModule(expandedCourseId, {
        title: moduleTitle.trim(),
        position: expandedCourse?.modules.length ?? 0,
      });
      setModuleTitle("");
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      toast.success("Modulo criado!");
    } catch {
      toast.error("Erro ao criar modulo");
    } finally {
      setAddingModule(false);
    }
  };

  const handleDeleteModule = async (moduleId: string) => {
    if (!expandedCourseId) return;
    try {
      await apiDeleteModule(moduleId);
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      toast.success("Modulo removido!");
    } catch {
      toast.error("Erro ao remover modulo");
    }
  };

  const handleUploadVideo = async (lessonId: string, file: File) => {
    setUploadingLessonId(lessonId);
    try {
      await uploadVideo(lessonId, file);
      if (expandedCourseId) await refreshExpanded(expandedCourseId);
      toast.success("Video enviado!");
    } catch {
      toast.error("Erro ao enviar video");
    } finally {
      setUploadingLessonId(null);
    }
  };

  const handleUploadThumbnail = async (courseId: string, file: File) => {
    setUploadingThumbnailId(courseId);
    try {
      await uploadCourseThumbnail(courseId, file);
      refreshCourses();
      toast.success("Thumbnail atualizada!");
    } catch {
      toast.error("Erro ao enviar thumbnail");
    } finally {
      setUploadingThumbnailId(null);
    }
  };

  const handleImport = async () => {
    if (!importUrl.trim() || !expandedCourseId || !importMode) return;
    setImporting(true);
    try {
      const result =
        importMode === "drive"
          ? await importFromDrive(expandedCourseId, importUrl.trim())
          : await importFromYoutube(expandedCourseId, importUrl.trim());
      setImportMode(null);
      setImportUrl("");
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      if (result.imported > 0) {
        toast.success(`${result.imported} aula(s) importada(s) com sucesso!`);
      } else {
        toast.info("Nenhum video encontrado para importar.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao importar";
      toast.error(msg);
    } finally {
      setImporting(false);
    }
  };

  const handleBrowseLocal = async (path: string) => {
    setLocalBrowseLoading(true);
    try {
      const result = await browseLocalFolder(path);
      setLocalAvailable(result.available);
      setLocalEntries(result.entries);
      setLocalBrowsePath(result.path);
    } catch {
      toast.error("Erro ao listar pasta local");
      setLocalAvailable(false);
      setLocalEntries([]);
    } finally {
      setLocalBrowseLoading(false);
    }
  };

  const handleLocalImport = async () => {
    if (!expandedCourseId) return;
    const videoCount = localEntries.filter((e) => e.type === "file").length;
    if (videoCount === 0) return;

    setImporting(true);
    setLocalProgress(null);
    try {
      const result = await importFromLocalFolder(
        expandedCourseId,
        localBrowsePath,
        lessonModuleId || null,
        (event) => setLocalProgress(event),
      );
      setImportMode(null);
      setLocalProgress(null);
      setLocalEntries([]);
      setLocalBrowsePath("");
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      if (result.imported > 0) {
        toast.success(`${result.imported} aula(s) importada(s) com sucesso!`);
      } else {
        toast.info("Nenhum video importado.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao importar";
      toast.error(msg);
      setLocalProgress(null);
    } finally {
      setImporting(false);
    }
  };

  const localBreadcrumbs = localBrowsePath
    ? localBrowsePath.split("/").filter(Boolean)
    : [];

  const handleStartEdit = (lesson: Lesson) => {
    setEditingLessonId(lesson.id);
    setEditTitle(lesson.title);
    setEditDescription(lesson.description ?? "");
  };

  const handleCancelEdit = () => {
    setEditingLessonId(null);
    setEditTitle("");
    setEditDescription("");
  };

  const handleSaveEdit = async () => {
    if (!editTitle.trim() || !editingLessonId || !expandedCourseId) return;
    setSavingEdit(true);
    try {
      await updateLesson(editingLessonId, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      handleCancelEdit();
      await refreshExpanded(expandedCourseId);
      toast.success("Aula atualizada!");
    } catch {
      toast.error("Erro ao atualizar aula");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteLesson = async (lessonId: string) => {
    if (!expandedCourseId) return;
    setDeletingLessonId(lessonId);
    try {
      await apiDeleteLesson(lessonId);
      await refreshExpanded(expandedCourseId);
      refreshCourses();
      toast.success("Aula removida!");
    } catch {
      toast.error("Erro ao remover aula");
    } finally {
      setDeletingLessonId(null);
    }
  };

  const renderLessonRow = (lesson: Lesson, index: number) => {
    if (editingLessonId === lesson.id) {
      return (
        <div key={lesson.id} className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2">
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Titulo *</label>
              <input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm focus:border-primary/50 focus:outline-none"
                autoFocus
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Descricao</label>
              <input
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Opcional"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm focus:border-primary/50 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSaveEdit}
              disabled={!editTitle.trim() || savingEdit}
              className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground disabled:opacity-50"
            >
              {savingEdit ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
              Salvar
            </button>
            <button
              onClick={handleCancelEdit}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              Cancelar
            </button>
          </div>
        </div>
      );
    }

    return (
      <div key={lesson.id} className="flex items-center justify-between rounded-lg p-3 hover:bg-primary/5 transition-colors">
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-primary/20 text-xs font-semibold text-primary">
            {index + 1}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{lesson.title}</p>
            <p className="text-[11px] text-muted-foreground">
              {lesson.video_source === "google_drive"
                ? "Google Drive"
                : lesson.video_source === "youtube"
                  ? "YouTube"
                  : lesson.video_url
                    ? "Video enviado"
                    : "Sem video"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {!lesson.video_url && (
            <button
              disabled={uploadingLessonId === lesson.id}
              onClick={() => {
                fileInputRef.current?.setAttribute("data-lesson-id", lesson.id);
                fileInputRef.current?.click();
              }}
              className="flex items-center gap-1 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors disabled:opacity-50"
            >
              {uploadingLessonId === lesson.id ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <>
                  <Upload className="h-3.5 w-3.5" />
                  Upload
                </>
              )}
            </button>
          )}
          {lesson.video_url && <Video className="h-4 w-4 text-primary" />}
          <button
            onClick={() => handleStartEdit(lesson)}
            className="p-1.5 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => handleDeleteLesson(lesson.id)}
            disabled={deletingLessonId === lesson.id}
            className="p-1.5 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50"
          >
            {deletingLessonId === lesson.id ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-5xl px-6 pt-24 pb-16">
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-black md:text-4xl">
              Gerenciar <span className="text-gradient">Cursos</span>
            </h1>
            <p className="text-muted-foreground mt-1">
              Adicione e organize seus cursos.
            </p>
          </div>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/20 transition-colors hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              Novo Curso
            </button>
          )}
        </div>

        {/* Create Course Form */}
        {showForm && (
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">Novo Curso</h2>
              <button
                onClick={() => { setShowForm(false); setNewTitle(""); setNewDescription(""); }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-medium">Titulo *</label>
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ex: Curso de React Avancado"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Descricao</label>
                <Textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Uma breve descricao do curso..."
                  className="bg-white/5 border-white/10 resize-none"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleCreateCourse}
                  disabled={saving}
                  className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground disabled:opacity-50"
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  Criar Curso
                </button>
                <button
                  onClick={() => { setShowForm(false); setNewTitle(""); setNewDescription(""); }}
                  className="rounded-xl border border-white/10 px-5 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Course List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : courses.length > 0 ? (
          <div className="space-y-3">
            {courses.map((course) => (
              <div key={course.id}>
                {/* Course Row */}
                <div
                  className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${
                    expandedCourseId === course.id
                      ? "border-primary/30 bg-primary/5"
                      : "border-white/10 bg-white/5 hover:border-primary/20"
                  }`}
                >
                  <button
                    onClick={() => handleToggleExpand(course.id)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {expandedCourseId === course.id ? (
                      <ChevronDown className="h-5 w-5" />
                    ) : (
                      <ChevronRight className="h-5 w-5" />
                    )}
                  </button>

                  {/* Thumbnail */}
                  <div
                    className="h-16 w-24 shrink-0 rounded-lg border border-white/10 overflow-hidden flex items-center justify-center relative group/thumb cursor-pointer"
                    onClick={() => {
                      thumbnailInputRef.current?.setAttribute("data-course-id", course.id);
                      thumbnailInputRef.current?.click();
                    }}
                  >
                    {courseThumbnailUrl(course) ? (
                      <img src={courseThumbnailUrl(course)!} alt={course.title} className="h-full w-full object-cover" />
                    ) : (
                      <BookOpen className="h-5 w-5 text-muted-foreground" />
                    )}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/thumb:opacity-100 transition-opacity flex items-center justify-center">
                      {uploadingThumbnailId === course.id ? (
                        <Loader2 className="h-4 w-4 text-white animate-spin" />
                      ) : (
                        <Camera className="h-4 w-4 text-white" />
                      )}
                    </div>
                  </div>

                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-foreground truncate">{course.title}</h3>
                    <p className="text-xs text-muted-foreground">
                      {course.lessons.length} aulas &bull; {course.modules.length} modulos
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleToggleExpand(course.id)}
                      className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                    >
                      Gerenciar
                    </button>
                    <button
                      onClick={() => handleDeleteCourse(course.id)}
                      className="rounded-lg border border-white/10 p-1.5 text-muted-foreground hover:text-destructive hover:border-destructive/30 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedCourseId === course.id && expandedCourse && (
                  <div className="mt-2 mb-4 ml-10 space-y-4">
                    {/* Modules section */}
                    {expandedCourse.modules.length > 0 && (
                      <div className="space-y-3">
                        {expandedCourse.modules
                          .slice()
                          .sort((a, b) => a.position - b.position)
                          .map((mod) => (
                            <div key={mod.id} className="rounded-xl border border-white/10 bg-white/5 overflow-hidden">
                              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                                <div className="flex items-center gap-2">
                                  <Layers className="h-4 w-4 text-primary" />
                                  <span className="text-sm font-semibold uppercase tracking-wider text-primary">
                                    {mod.title}
                                  </span>
                                  <span className="text-[10px] text-muted-foreground">
                                    ({mod.lessons.length} aulas)
                                  </span>
                                </div>
                                <button
                                  onClick={() => handleDeleteModule(mod.id)}
                                  className="text-muted-foreground hover:text-destructive transition-colors"
                                  title="Excluir modulo"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                              {mod.lessons.length > 0 ? (
                                <div className="divide-y divide-white/5">
                                  {mod.lessons
                                    .slice()
                                    .sort((a, b) => a.position - b.position)
                                    .map((lesson, i) => renderLessonRow(lesson, i))}
                                </div>
                              ) : (
                                <p className="px-4 py-3 text-xs text-muted-foreground">
                                  Nenhuma aula neste modulo.
                                </p>
                              )}
                            </div>
                          ))}
                      </div>
                    )}

                    {/* Ungrouped lessons */}
                    {(() => {
                      const moduleLessonIds = new Set(
                        expandedCourse.modules.flatMap((m) => m.lessons.map((l) => l.id)),
                      );
                      const ungrouped = expandedCourse.lessons.filter(
                        (l) => !moduleLessonIds.has(l.id),
                      );
                      if (ungrouped.length === 0) return null;
                      return (
                        <div className="rounded-xl border border-white/10 bg-white/5 overflow-hidden">
                          <div className="px-4 py-3 border-b border-white/5">
                            <span className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                              Sem Modulo
                            </span>
                          </div>
                          <div className="divide-y divide-white/5">
                            {ungrouped.map((lesson, i) => renderLessonRow(lesson, i))}
                          </div>
                        </div>
                      );
                    })()}

                    {/* No lessons at all */}
                    {expandedCourse.lessons.length === 0 && expandedCourse.modules.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4 rounded-lg border border-dashed border-white/10">
                        Nenhuma aula ou modulo adicionado.
                      </p>
                    )}

                    {/* Add Module Form */}
                    <div className="rounded-xl border border-white/10 bg-primary/5 p-4 space-y-3">
                      <p className="text-sm font-semibold flex items-center gap-2">
                        <Layers className="h-4 w-4 text-primary" />
                        Adicionar Modulo
                      </p>
                      <div className="flex gap-2">
                        <input
                          value={moduleTitle}
                          onChange={(e) => setModuleTitle(e.target.value)}
                          placeholder="Ex: Introducao ao Ecossistema"
                          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                        />
                        <button
                          onClick={handleAddModule}
                          disabled={!moduleTitle.trim() || addingModule}
                          className="flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-50"
                        >
                          {addingModule ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                          Criar
                        </button>
                      </div>
                    </div>

                    {/* Add Lesson Form */}
                    <div className="rounded-xl border border-white/10 bg-primary/5 p-4 space-y-3">
                      <p className="text-sm font-semibold">Adicionar Aula</p>
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div className="space-y-1">
                          <label className="text-xs text-muted-foreground">Titulo *</label>
                          <input
                            value={lessonTitle}
                            onChange={(e) => setLessonTitle(e.target.value)}
                            placeholder="Ex: Introducao"
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-xs text-muted-foreground">Descricao</label>
                          <input
                            value={lessonDescription}
                            onChange={(e) => setLessonDescription(e.target.value)}
                            placeholder="Opcional"
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-xs text-muted-foreground">Modulo</label>
                          <select
                            value={lessonModuleId}
                            onChange={(e) => setLessonModuleId(e.target.value)}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                          >
                            <option value="">Sem modulo</option>
                            {expandedCourse.modules.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.title}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <button
                        onClick={handleAddLesson}
                        disabled={!lessonTitle.trim() || addingLesson}
                        className="flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-50"
                      >
                        {addingLesson ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                        Adicionar Aula
                      </button>
                    </div>

                    {/* Bulk Import */}
                    <div className="rounded-xl border border-white/10 bg-primary/5 p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold">Importar Aulas</p>
                        {importMode && (
                          <button
                            onClick={() => { setImportMode(null); setImportUrl(""); setLocalEntries([]); setLocalBrowsePath(""); setLocalProgress(null); }}
                            className="text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        )}
                      </div>

                      {!importMode ? (
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => setImportMode("drive")}
                            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                          >
                            <Link2 className="h-3.5 w-3.5" />
                            Google Drive
                          </button>
                          <button
                            onClick={() => setImportMode("youtube")}
                            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                          >
                            <Youtube className="h-3.5 w-3.5" />
                            YouTube
                          </button>
                          <button
                            onClick={() => { setImportMode("local"); handleBrowseLocal(""); }}
                            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                          >
                            <HardDrive className="h-3.5 w-3.5" />
                            Pasta Local
                          </button>
                        </div>
                      ) : importMode === "local" ? (
                        <div className="space-y-3">
                          {/* Breadcrumb navigation */}
                          <div className="flex items-center gap-1 text-xs text-muted-foreground flex-wrap">
                            <button
                              onClick={() => handleBrowseLocal("")}
                              className="hover:text-primary transition-colors font-medium"
                            >
                              /imports
                            </button>
                            {localBreadcrumbs.map((segment, i) => {
                              const pathUpTo = localBreadcrumbs.slice(0, i + 1).join("/");
                              return (
                                <span key={i} className="flex items-center gap-1">
                                  <span>/</span>
                                  <button
                                    onClick={() => handleBrowseLocal(pathUpTo)}
                                    className="hover:text-primary transition-colors font-medium"
                                  >
                                    {segment}
                                  </button>
                                </span>
                              );
                            })}
                          </div>

                          {localBrowseLoading ? (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="h-5 w-5 animate-spin text-primary" />
                            </div>
                          ) : !localAvailable ? (
                            <div className="text-center py-6 text-sm text-muted-foreground">
                              <HardDrive className="h-8 w-8 mx-auto mb-2 opacity-50" />
                              <p>Pasta de imports nao disponivel.</p>
                              <p className="text-xs mt-1">Verifique o volume Docker <code className="bg-white/10 px-1 rounded">./imports:/imports:ro</code></p>
                            </div>
                          ) : localEntries.length === 0 ? (
                            <div className="text-center py-6 text-sm text-muted-foreground">
                              <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                              <p>Pasta vazia.</p>
                              <p className="text-xs mt-1">Coloque arquivos de video na pasta <code className="bg-white/10 px-1 rounded">./imports/</code></p>
                            </div>
                          ) : (
                            <>
                              {/* File/folder listing */}
                              <div className="rounded-lg border border-white/10 overflow-hidden max-h-[280px] overflow-y-auto custom-scrollbar">
                                {localEntries.map((entry) => (
                                  <div
                                    key={entry.path}
                                    className={`flex items-center gap-3 px-3 py-2.5 border-b border-white/5 last:border-b-0 ${
                                      entry.type === "directory"
                                        ? "cursor-pointer hover:bg-primary/5"
                                        : "bg-white/[0.02]"
                                    } transition-colors`}
                                    onClick={
                                      entry.type === "directory"
                                        ? () => handleBrowseLocal(entry.path)
                                        : undefined
                                    }
                                  >
                                    {entry.type === "directory" ? (
                                      <FolderOpen className="h-4 w-4 text-primary shrink-0" />
                                    ) : (
                                      <Video className="h-4 w-4 text-muted-foreground shrink-0" />
                                    )}
                                    <span className="text-sm truncate flex-1">{entry.name}</span>
                                    {entry.type === "file" && entry.size_bytes != null && (
                                      <span className="text-[10px] text-muted-foreground shrink-0">
                                        {(entry.size_bytes / (1024 * 1024)).toFixed(1)} MB
                                      </span>
                                    )}
                                    {entry.type === "directory" && (
                                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                                    )}
                                  </div>
                                ))}
                              </div>

                              {/* Module selector for import */}
                              {expandedCourse && expandedCourse.modules.length > 0 && (
                                <div className="space-y-1">
                                  <label className="text-xs text-muted-foreground">Atribuir ao modulo</label>
                                  <select
                                    value={lessonModuleId}
                                    onChange={(e) => setLessonModuleId(e.target.value)}
                                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                                  >
                                    <option value="">Sem modulo</option>
                                    {expandedCourse.modules.map((m) => (
                                      <option key={m.id} value={m.id}>
                                        {m.title}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                              )}

                              {/* Progress bar during import */}
                              {importing && localProgress && localProgress.type !== "result" && (
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between text-xs">
                                    <span className="text-muted-foreground truncate">
                                      {localProgress.type === "error" ? (
                                        <span className="text-destructive">Erro: {localProgress.filename}</span>
                                      ) : (
                                        <>Enviando: {localProgress.filename}</>
                                      )}
                                    </span>
                                    <span className="text-muted-foreground shrink-0">
                                      {localProgress.current}/{localProgress.total}
                                    </span>
                                  </div>
                                  <div className="h-1.5 w-full rounded-full bg-white/10">
                                    <div
                                      className="h-full rounded-full bg-primary transition-all duration-300"
                                      style={{
                                        width: `${((localProgress.current ?? 0) / (localProgress.total ?? 1)) * 100}%`,
                                      }}
                                    />
                                  </div>
                                </div>
                              )}

                              {/* Import button */}
                              {(() => {
                                const videoCount = localEntries.filter((e) => e.type === "file").length;
                                return videoCount > 0 ? (
                                  <button
                                    onClick={handleLocalImport}
                                    disabled={importing}
                                    className="flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-50"
                                  >
                                    {importing ? (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                      <Upload className="h-3.5 w-3.5" />
                                    )}
                                    {importing
                                      ? "Importando..."
                                      : `Importar ${videoCount} video(s)`}
                                  </button>
                                ) : null;
                              })()}
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="space-y-1">
                            <label className="text-xs text-muted-foreground">
                              {importMode === "drive"
                                ? "URL da pasta do Google Drive"
                                : "URL da playlist do YouTube"}
                            </label>
                            <input
                              value={importUrl}
                              onChange={(e) => setImportUrl(e.target.value)}
                              placeholder={
                                importMode === "drive"
                                  ? "https://drive.google.com/drive/folders/..."
                                  : "https://www.youtube.com/playlist?list=..."
                              }
                              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm focus:border-primary/50 focus:outline-none"
                            />
                          </div>
                          <button
                            onClick={handleImport}
                            disabled={!importUrl.trim() || importing}
                            className="flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-50"
                          >
                            {importing ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : importMode === "drive" ? (
                              <Link2 className="h-3.5 w-3.5" />
                            ) : (
                              <Youtube className="h-3.5 w-3.5" />
                            )}
                            {importing ? "Importando..." : "Importar"}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          !showForm && (
            <div className="text-center py-20">
              <div className="rounded-2xl bg-white/5 p-6 inline-block mb-4">
                <BookOpen className="h-12 w-12 text-muted-foreground" />
              </div>
              <h2 className="text-xl font-semibold">Nenhum curso cadastrado</h2>
              <p className="mt-2 text-muted-foreground mb-6">
                Comece criando seu primeiro curso.
              </p>
              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 mx-auto rounded-xl bg-primary px-6 py-3 text-sm font-bold text-primary-foreground"
              >
                <Plus className="h-4 w-4" />
                Criar Primeiro Curso
              </button>
            </div>
          )
        )}

        {/* Hidden file inputs */}
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            const lessonId = fileInputRef.current?.getAttribute("data-lesson-id");
            if (file && lessonId) handleUploadVideo(lessonId, file);
            e.target.value = "";
          }}
        />
        <input
          ref={thumbnailInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            const courseId = thumbnailInputRef.current?.getAttribute("data-course-id");
            if (file && courseId) handleUploadThumbnail(courseId, file);
            e.target.value = "";
          }}
        />
      </main>
    </div>
  );
};

export default AdminCourses;
