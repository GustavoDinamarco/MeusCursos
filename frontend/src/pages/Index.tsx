import { useState, useEffect, useMemo } from "react";
import CourseCard from "@/components/CourseCard";
import ContinueWatchingCard from "@/components/ContinueWatchingCard";
import Header from "@/components/Header";
import { getCourses, getCourseProgress } from "@/lib/storage";
import { CourseWithLessons } from "@/types/course";
import { Search, BookOpen, Loader2 } from "lucide-react";

const Index = () => {
  const [courses, setCourses] = useState<CourseWithLessons[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCourses()
      .then(setCourses)
      .catch(() => setCourses([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = courses.filter(
    (c) =>
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      (c.description ?? "").toLowerCase().includes(search.toLowerCase()),
  );

  // Courses with partial progress (started but not finished) — max 2
  const continueWatching = useMemo(() => {
    return courses
      .filter((c) => {
        const { completed, total } = getCourseProgress(c.lessons);
        return total > 0 && completed > 0 && completed < total;
      })
      .slice(0, 2);
  }, [courses]);

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-7xl px-6 pt-24 pb-16">
        {/* Hero */}
        <div className="mb-10">
          <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
            Seus <span className="text-gradient">Cursos</span>
          </h1>
          <p className="mt-3 text-lg text-muted-foreground max-w-xl">
            Plataforma local para organizar e assistir seus cursos. Adicione
            videos, faca anotacoes e aprenda no seu ritmo.
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-10 max-w-lg">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            placeholder="Buscar cursos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-11 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30 transition-colors"
          />
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            {/* Continue Watching */}
            {continueWatching.length > 0 && !search && (
              <section className="mb-12">
                <h2 className="mb-6 text-xl font-bold text-foreground">
                  Continuar Assistindo
                </h2>
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {continueWatching.map((course) => (
                    <ContinueWatchingCard key={course.id} course={course} />
                  ))}
                </div>
              </section>
            )}

            {/* All Courses */}
            <section>
              <h2 className="mb-6 text-xl font-bold text-foreground">
                {search ? "Resultados" : "Todos os Meus Cursos"}
              </h2>

              {filtered.length > 0 ? (
                <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
                  {filtered.map((course) => (
                    <CourseCard key={course.id} course={course} />
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="rounded-2xl bg-white/5 p-6 mb-4">
                    <BookOpen className="h-12 w-12 text-muted-foreground" />
                  </div>
                  <h3 className="text-xl font-semibold">
                    Nenhum curso encontrado
                  </h3>
                  <p className="mt-2 text-muted-foreground">
                    {courses.length === 0
                      ? "Comece adicionando seus cursos na pagina de gerenciamento."
                      : "Nenhum resultado para sua busca."}
                  </p>
                </div>
              )}
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8">
        <div className="mx-auto max-w-7xl px-6 text-center text-xs text-muted-foreground">
          MeusCursos &mdash; Plataforma local de cursos
        </div>
      </footer>
    </div>
  );
};

export default Index;
