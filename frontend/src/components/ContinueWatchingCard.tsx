import { CourseWithLessons } from "@/types/course";
import { courseThumbnailUrl, getCourseProgress } from "@/lib/storage";
import { Link } from "react-router-dom";
import { Play, ArrowRight } from "lucide-react";

interface ContinueWatchingCardProps {
  course: CourseWithLessons;
}

const ContinueWatchingCard = ({ course }: ContinueWatchingCardProps) => {
  const thumbUrl = courseThumbnailUrl(course);
  const { completed, total, percentage } = getCourseProgress(course.lessons);
  const initial = course.title.charAt(0).toUpperCase();

  // Find the next incomplete lesson
  const nextLesson = course.lessons.find((l) => !l.completed);
  // Find which module the next lesson belongs to
  const nextModule = nextLesson
    ? course.modules.find((m) => m.id === nextLesson.module_id)
    : null;

  return (
    <Link
      to={`/course/${course.id}`}
      className="group flex flex-col md:flex-row rounded-xl border border-white/10 bg-white/5 overflow-hidden transition-all hover:border-primary/50"
    >
      {/* Thumbnail */}
      <div className="relative w-full md:w-64 h-48 md:h-auto flex-shrink-0 overflow-hidden">
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={course.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-700 to-orange-900">
            <span className="text-4xl font-bold text-white/60">{initial}</span>
          </div>
        )}
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
          <div className="rounded-full bg-primary/90 p-3 text-primary-foreground">
            <Play className="h-6 w-6" />
          </div>
        </div>
        {/* Progress bar overlay at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
          <div
            className="h-full bg-primary"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-col justify-between p-6 grow">
        <div>
          <span className="inline-block rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-primary mb-2">
            {total} aulas
          </span>
          <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors">
            {course.title}
          </h3>
          {nextModule && nextLesson && (
            <p className="mt-1 text-sm text-muted-foreground">
              {nextModule.title} &bull; {nextLesson.title}
            </p>
          )}
          {!nextModule && nextLesson && (
            <p className="mt-1 text-sm text-muted-foreground">
              {nextLesson.title}
            </p>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            {completed} de {total} aulas &bull; {percentage}%
          </span>
          <span className="flex items-center gap-1 text-xs font-bold text-primary">
            Retomar Aula
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
          </span>
        </div>
      </div>
    </Link>
  );
};

export default ContinueWatchingCard;
