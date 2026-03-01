import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams } from "react-router-dom";
import Header from "@/components/Header";
import VideoPlayer from "@/components/VideoPlayer";
import {
  getCourse,
  getNotes,
  createNote,
  deleteNote as apiDeleteNote,
  completeLesson as apiCompleteLesson,
  uncompleteLesson as apiUncompleteLesson,
  getCourseProgress,
} from "@/lib/storage";
import { CourseWithLessons, Lesson, Module, Note } from "@/types/course";
import { Textarea } from "@/components/ui/textarea";
import {
  Play,
  CheckCircle2,
  Circle,
  FileText,
  Loader2,
  Trash2,
  Plus,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const WatchCourse = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const [course, setCourse] = useState<CourseWithLessons | null>(null);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [newNote, setNewNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  // Refs for VideoPlayer integration
  const getTimeRef = useRef<() => number>(() => 0);
  const seekRef = useRef<(seconds: number) => void>(() => {});

  useEffect(() => {
    if (courseId) {
      getCourse(courseId)
        .then((c) => {
          setCourse(c);
          // Select first lesson
          if (c.lessons.length > 0) {
            // Find first incomplete lesson, or fallback to first
            const next = c.lessons.find((l) => !l.completed) ?? c.lessons[0];
            setActiveLesson(next);
          }
          // Expand all modules by default
          setExpandedModules(new Set(c.modules.map((m) => m.id)));
        })
        .catch(() => setCourse(null))
        .finally(() => setLoading(false));
    }
  }, [courseId]);

  useEffect(() => {
    if (activeLesson) {
      getNotes(activeLesson.id)
        .then(setNotes)
        .catch(() => setNotes([]));
    }
  }, [activeLesson?.id]);

  const handleAddNote = async () => {
    if (!newNote.trim() || !activeLesson) return;
    const currentTime = getTimeRef.current();
    try {
      const note = await createNote(activeLesson.id, {
        content: newNote.trim(),
        video_timestamp: currentTime,
      });
      setNotes((prev) => [...prev, note]);
      setNewNote("");
    } catch {
      // silently fail
    }
  };

  const handleDeleteNote = async (id: string) => {
    try {
      await apiDeleteNote(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
    } catch {
      // silently fail
    }
  };

  const handleSeekToTimestamp = (seconds: number) => {
    seekRef.current(seconds);
  };

  const handleToggleComplete = async () => {
    if (!activeLesson || !course) return;
    try {
      let updated: Lesson;
      if (activeLesson.completed) {
        updated = await apiUncompleteLesson(activeLesson.id);
      } else {
        updated = await apiCompleteLesson(activeLesson.id);
      }
      setActiveLesson(updated);
      // Update in the course state
      setCourse((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          lessons: prev.lessons.map((l) => (l.id === updated.id ? updated : l)),
          modules: prev.modules.map((m) => ({
            ...m,
            lessons: m.lessons.map((l) => (l.id === updated.id ? updated : l)),
          })),
        };
      });
    } catch {
      // silently fail
    }
  };

  const toggleModule = (moduleId: string) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleId)) next.delete(moduleId);
      else next.add(moduleId);
      return next;
    });
  };

  const onTimeRef = useCallback(
    (getter: () => number) => {
      getTimeRef.current = getter;
    },
    [],
  );

  const onSeekRef = useCallback(
    (seeker: (seconds: number) => void) => {
      seekRef.current = seeker;
    },
    [],
  );

  // Group lessons: modules with their lessons + "ungrouped" lessons
  const { modulesWithLessons, ungroupedLessons, progress } = useMemo(() => {
    if (!course) return { modulesWithLessons: [], ungroupedLessons: [], progress: { completed: 0, total: 0, percentage: 0 } };

    const mods = course.modules
      .slice()
      .sort((a, b) => a.position - b.position)
      .map((m) => ({
        ...m,
        lessons: m.lessons.slice().sort((a, b) => a.position - b.position),
      }));

    const moduleLessonIds = new Set(mods.flatMap((m) => m.lessons.map((l) => l.id)));
    const ungrouped = course.lessons
      .filter((l) => !moduleLessonIds.has(l.id))
      .sort((a, b) => a.position - b.position);

    return {
      modulesWithLessons: mods,
      ungroupedLessons: ungrouped,
      progress: getCourseProgress(course.lessons),
    };
  }, [course]);

  // Find the module for the active lesson
  const activeModule = useMemo(() => {
    if (!activeLesson || !course) return null;
    return course.modules.find((m) => m.id === activeLesson.module_id) ?? null;
  }, [activeLesson, course]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header variant="minimal" />
        <div className="flex items-center justify-center pt-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-background">
        <Header variant="minimal" />
        <div className="flex items-center justify-center pt-24">
          <p className="text-muted-foreground">Curso nao encontrado.</p>
        </div>
      </div>
    );
  }

  const renderLessonItem = (lesson: Lesson, index: number) => {
    const isActive = activeLesson?.id === lesson.id;
    const isCompleted = lesson.completed;

    return (
      <button
        key={lesson.id}
        onClick={() => setActiveLesson(lesson)}
        className={`flex w-full items-center justify-between p-4 text-left transition-colors rounded-r-lg border-l-4 ${
          isActive
            ? "bg-primary/10 border-primary"
            : isCompleted
              ? "border-transparent opacity-70 hover:bg-primary/5 hover:opacity-100"
              : "border-transparent hover:bg-primary/5"
        }`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded text-xs font-semibold ${
              isActive
                ? "bg-primary text-primary-foreground"
                : isCompleted
                  ? "bg-green-900/30 text-green-500"
                  : "bg-primary/20 text-primary"
            }`}
          >
            {isActive ? (
              <Play className="h-3.5 w-3.5" />
            ) : isCompleted ? (
              <CheckCircle2 className="h-3.5 w-3.5" />
            ) : (
              index + 1
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{lesson.title}</p>
          </div>
        </div>

        <span
          className={`ml-2 shrink-0 text-[10px] font-semibold uppercase tracking-wider ${
            isActive
              ? "text-primary"
              : isCompleted
                ? "text-green-500"
                : "text-muted-foreground"
          }`}
        >
          {isActive ? "Assistindo" : isCompleted ? "Concluida" : ""}
        </span>
      </button>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Header variant="minimal" />

      <main className="mx-auto max-w-[1440px] px-6 pt-20 pb-16">
        <div className="flex flex-col lg:grid lg:grid-cols-12 gap-8 items-start">
          {/* Left: Video + Info + Lesson List */}
          <div className="lg:col-span-8 space-y-6">
            {/* Video Player */}
            <VideoPlayer
              lesson={activeLesson}
              onTimeRef={onTimeRef}
              onSeekRef={onSeekRef}
            />

            {/* Lesson Info */}
            {activeLesson && (
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    {activeModule && (
                      <span className="text-sm font-semibold uppercase text-primary">
                        {activeModule.title}
                      </span>
                    )}
                    <h1 className="text-3xl font-bold">{activeLesson.title}</h1>
                  </div>
                  <button
                    onClick={handleToggleComplete}
                    className={`flex shrink-0 items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold transition-colors ${
                      activeLesson.completed
                        ? "bg-green-900/30 text-green-500 hover:bg-green-900/50"
                        : "bg-primary text-primary-foreground hover:bg-primary/90"
                    }`}
                  >
                    {activeLesson.completed ? (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Concluida
                      </>
                    ) : (
                      <>
                        <Circle className="h-4 w-4" />
                        Concluir Aula
                      </>
                    )}
                  </button>
                </div>

                {activeLesson.description && (
                  <div className="rounded-xl bg-primary/5 border border-primary/10 p-6">
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {activeLesson.description}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Lesson List grouped by module */}
            <div className="rounded-xl border border-white/10 bg-white/5 overflow-hidden">
              <div className="border-b border-white/10 px-5 py-4 flex items-center justify-between">
                <h2 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                  Conteudo do Curso
                </h2>
                <span className="text-xs text-muted-foreground">
                  {progress.completed} de {progress.total} aulas concluidas
                </span>
              </div>

              <div className="custom-scrollbar max-h-[400px] overflow-y-auto">
                {/* Modules */}
                {modulesWithLessons.map((mod) => (
                  <div key={mod.id}>
                    <button
                      onClick={() => toggleModule(mod.id)}
                      className="flex w-full items-center gap-3 px-5 py-3 text-left hover:bg-primary/5 transition-colors border-b border-white/5"
                    >
                      {expandedModules.has(mod.id) ? (
                        <ChevronDown className="h-4 w-4 text-primary shrink-0" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                      <span className="text-sm font-semibold uppercase tracking-wider text-primary">
                        {mod.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground ml-auto">
                        {mod.lessons.filter((l) => l.completed).length}/{mod.lessons.length}
                      </span>
                    </button>
                    {expandedModules.has(mod.id) && (
                      <div className="space-y-0.5 py-1 px-2">
                        {mod.lessons.map((lesson, i) =>
                          renderLessonItem(lesson, i),
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {/* Ungrouped lessons */}
                {ungroupedLessons.length > 0 && (
                  <div>
                    {modulesWithLessons.length > 0 && (
                      <div className="px-5 py-3 border-b border-white/5">
                        <span className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                          Sem Modulo
                        </span>
                      </div>
                    )}
                    <div className="space-y-0.5 py-1 px-2">
                      {ungroupedLessons.map((lesson, i) =>
                        renderLessonItem(lesson, i),
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Notes Sidebar */}
          <div className="lg:col-span-4 lg:sticky lg:top-24 w-full">
            <div className="rounded-xl border border-white/10 bg-white/5 flex flex-col">
              <div className="border-b border-white/10 px-5 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <h2 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                    Anotacoes
                  </h2>
                </div>
                <span className="rounded-full bg-primary/20 px-2.5 py-0.5 text-[10px] font-bold text-primary uppercase tracking-wider">
                  Sincronizado
                </span>
              </div>

              <div className="custom-scrollbar max-h-[400px] overflow-y-auto p-4">
                {notes.length > 0 ? (
                  <div className="space-y-3">
                    {notes.map((note) => (
                      <div
                        key={note.id}
                        className="group rounded-lg bg-primary/5 border border-primary/10 p-3"
                      >
                        <p className="text-sm text-foreground whitespace-pre-wrap">
                          {note.content}
                        </p>
                        <div className="mt-2 flex items-center justify-between">
                          <button
                            onClick={() =>
                              handleSeekToTimestamp(note.video_timestamp)
                            }
                            className="text-xs font-medium text-primary hover:underline"
                          >
                            {formatTimestamp(note.video_timestamp)}
                          </button>
                          <button
                            onClick={() => handleDeleteNote(note.id)}
                            className="text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    Nenhuma anotacao ainda.
                  </div>
                )}
              </div>

              <div className="border-t border-white/10 p-4 space-y-3">
                <Textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Escreva sua anotacao..."
                  className="bg-primary/5 border-primary/10 resize-none min-h-[80px] text-sm"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.ctrlKey) handleAddNote();
                  }}
                />
                <button
                  onClick={handleAddNote}
                  disabled={!newNote.trim()}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus className="h-4 w-4" />
                  Salvar Nota
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default WatchCourse;
