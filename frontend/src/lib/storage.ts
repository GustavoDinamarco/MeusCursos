// API client for the FastAPI backend.
// Replaces the original localStorage-based storage.ts

import type {
  Course,
  CourseWithLessons,
  CreateCoursePayload,
  CreateLessonPayload,
  CreateModulePayload,
  CreateNotePayload,
  ImportResult,
  Lesson,
  LocalBrowseResponse,
  LocalImportProgress,
  Module,
  Note,
  UpdateLessonPayload,
  UpdateModulePayload,
} from "@/types/course";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const V1 = `${API_BASE}/api/v1`;

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

// ---- Courses ----

export async function getCourses(): Promise<CourseWithLessons[]> {
  const res = await fetch(`${V1}/courses`);
  return handleResponse<CourseWithLessons[]>(res);
}

export async function getCourse(id: string): Promise<CourseWithLessons> {
  const res = await fetch(`${V1}/courses/${id}`);
  return handleResponse<CourseWithLessons>(res);
}

export async function createCourse(data: CreateCoursePayload): Promise<Course> {
  const res = await fetch(`${V1}/courses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Course>(res);
}

export async function deleteCourse(id: string): Promise<void> {
  const res = await fetch(`${V1}/courses/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
}

// ---- Modules ----

export async function createModule(
  courseId: string,
  data: CreateModulePayload,
): Promise<Module> {
  const res = await fetch(`${V1}/courses/${courseId}/modules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Module>(res);
}

export async function updateModule(
  moduleId: string,
  data: UpdateModulePayload,
): Promise<Module> {
  const res = await fetch(`${V1}/modules/${moduleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Module>(res);
}

export async function deleteModule(moduleId: string): Promise<void> {
  const res = await fetch(`${V1}/modules/${moduleId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
}

// ---- Lessons ----

export async function createLesson(
  courseId: string,
  data: CreateLessonPayload,
): Promise<Lesson> {
  const res = await fetch(`${V1}/courses/${courseId}/lessons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Lesson>(res);
}

export async function uploadVideo(
  lessonId: string,
  file: File,
): Promise<Lesson> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${V1}/lessons/${lessonId}/upload-video`, {
    method: "POST",
    body: form,
  });
  return handleResponse<Lesson>(res);
}

export async function updateLesson(
  lessonId: string,
  data: UpdateLessonPayload,
): Promise<Lesson> {
  const res = await fetch(`${V1}/lessons/${lessonId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Lesson>(res);
}

export async function deleteLesson(lessonId: string): Promise<void> {
  const res = await fetch(`${V1}/lessons/${lessonId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
}

export function videoStreamUrl(lessonId: string): string {
  return `${V1}/lessons/${lessonId}/video`;
}

// ---- Lesson Completion ----

export async function completeLesson(lessonId: string): Promise<Lesson> {
  const res = await fetch(`${V1}/lessons/${lessonId}/complete`, {
    method: "POST",
  });
  return handleResponse<Lesson>(res);
}

export async function uncompleteLesson(lessonId: string): Promise<Lesson> {
  const res = await fetch(`${V1}/lessons/${lessonId}/complete`, {
    method: "DELETE",
  });
  return handleResponse<Lesson>(res);
}

// ---- Progress Helper ----

export function getCourseProgress(lessons: Lesson[]): {
  completed: number;
  total: number;
  percentage: number;
} {
  const total = lessons.length;
  const completed = lessons.filter((l) => l.completed).length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  return { completed, total, percentage };
}

// ---- Notes ----

export async function getNotes(lessonId: string): Promise<Note[]> {
  const res = await fetch(`${V1}/lessons/${lessonId}/notes`);
  return handleResponse<Note[]>(res);
}

export async function createNote(
  lessonId: string,
  data: CreateNotePayload,
): Promise<Note> {
  const res = await fetch(`${V1}/lessons/${lessonId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Note>(res);
}

export async function deleteNote(noteId: string): Promise<void> {
  const res = await fetch(`${V1}/notes/${noteId}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
}

// ---- Imports ----

export async function importFromDrive(
  courseId: string,
  folderUrl: string,
): Promise<ImportResult> {
  const res = await fetch(`${V1}/courses/${courseId}/import-drive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder_url: folderUrl }),
  });
  return handleResponse<ImportResult>(res);
}

export async function importFromYoutube(
  courseId: string,
  playlistUrl: string,
): Promise<ImportResult> {
  const res = await fetch(`${V1}/courses/${courseId}/import-youtube`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playlist_url: playlistUrl }),
  });
  return handleResponse<ImportResult>(res);
}

// ---- Local Folder Import ----

export async function browseLocalFolder(
  path: string = "",
): Promise<LocalBrowseResponse> {
  const params = new URLSearchParams();
  if (path) params.set("path", path);
  const res = await fetch(`${V1}/imports/local/browse?${params.toString()}`);
  return handleResponse<LocalBrowseResponse>(res);
}

export async function importFromLocalFolder(
  courseId: string,
  folderPath: string,
  moduleId?: string | null,
  onProgress?: (event: LocalImportProgress) => void,
): Promise<ImportResult> {
  const res = await fetch(`${V1}/courses/${courseId}/import-local`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      folder_path: folderPath,
      module_id: moduleId ?? null,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }

  // Read NDJSON stream
  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("Stream not available");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: ImportResult = { imported: 0, lessons: [] };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event: LocalImportProgress = JSON.parse(line);
        onProgress?.(event);
        if (event.type === "result") {
          finalResult = {
            imported: event.imported ?? 0,
            lessons: event.lessons ?? [],
          };
        }
      } catch {
        // skip malformed lines
      }
    }
  }

  // Process remaining buffer
  if (buffer.trim()) {
    try {
      const event: LocalImportProgress = JSON.parse(buffer);
      onProgress?.(event);
      if (event.type === "result") {
        finalResult = {
          imported: event.imported ?? 0,
          lessons: event.lessons ?? [],
        };
      }
    } catch {
      // skip
    }
  }

  return finalResult;
}

// ---- Thumbnails ----

export async function uploadCourseThumbnail(
  courseId: string,
  file: File,
): Promise<Course> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${V1}/courses/${courseId}/upload-thumbnail`, {
    method: "POST",
    body: form,
  });
  return handleResponse<Course>(res);
}

export function courseThumbnailUrl(course: Course): string | null {
  if (!course.thumbnail_url) return null;
  if (course.thumbnail_url.startsWith("http")) return course.thumbnail_url;
  return `${V1}/courses/${course.id}/thumbnail`;
}
