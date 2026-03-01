import { CourseWithLessons } from "@/types/course";
import { courseThumbnailUrl, getCourseProgress } from "@/lib/storage";
import { Link } from "react-router-dom";
import { Play } from "lucide-react";

const GRADIENTS = [
  "from-amber-700 to-orange-900",
  "from-emerald-700 to-teal-900",
  "from-rose-700 to-red-900",
  "from-violet-700 to-purple-900",
  "from-cyan-700 to-blue-900",
  "from-amber-600 to-yellow-900",
];

function getGradient(title: string): string {
  let hash = 0;
  for (let i = 0; i < title.length; i++) {
    hash = title.charCodeAt(i) + ((hash << 5) - hash);
  }
  return GRADIENTS[Math.abs(hash) % GRADIENTS.length];
}

interface CourseCardProps {
  course: CourseWithLessons;
}

const CourseCard = ({ course }: CourseCardProps) => {
  const gradient = getGradient(course.title);
  const initial = course.title.charAt(0).toUpperCase();
  const thumbUrl = courseThumbnailUrl(course);
  const { completed, total, percentage } = getCourseProgress(course.lessons);

  return (
    <Link
      to={`/course/${course.id}`}
      className="group rounded-xl border border-white/10 bg-white/5 overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-primary/50"
    >
      <div className={`aspect-video relative overflow-hidden bg-gradient-to-br ${gradient}`}>
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={course.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <span className="text-5xl font-bold text-white/60">{initial}</span>
          </div>
        )}
        <div className="absolute inset-0 bg-black/60 opacity-0 transition-opacity duration-300 group-hover:opacity-100 flex items-center justify-center">
          <div className="rounded-full bg-primary p-3 text-primary-foreground">
            <Play className="h-6 w-6" />
          </div>
        </div>
      </div>

      <div className="p-4">
        <span className="inline-block rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-primary">
          {total} aulas
        </span>
        <h3 className="mt-2 font-bold leading-tight text-foreground line-clamp-1 group-hover:text-primary transition-colors">
          {course.title}
        </h3>
        {course.description && (
          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {course.description}
          </p>
        )}

        {total > 0 && (
          <div className="mt-3 flex items-center gap-3">
            <div className="h-1.5 flex-1 rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="text-xs font-medium text-muted-foreground">
              {percentage}%
            </span>
          </div>
        )}
      </div>
    </Link>
  );
};

export default CourseCard;
