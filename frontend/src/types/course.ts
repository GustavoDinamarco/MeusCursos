// Types matching the FastAPI backend Pydantic schemas (snake_case)

export interface Course {
  id: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  created_at: string;
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  description: string | null;
  video_url: string | null;
  /** Computed by the backend from the video_url prefix */
  video_source: "minio" | "google_drive" | "youtube" | null;
  module_id: string | null;
  position: number;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface Module {
  id: string;
  course_id: string;
  title: string;
  position: number;
  created_at: string;
  lessons: Lesson[];
}

export interface CourseWithLessons extends Course {
  lessons: Lesson[];
  modules: Module[];
}

export interface Note {
  id: string;
  lesson_id: string;
  content: string;
  video_timestamp: number;
  created_at: string;
}

// Payloads
export interface CreateCoursePayload {
  title: string;
  description?: string | null;
}

export interface CreateLessonPayload {
  title: string;
  description?: string | null;
}

export interface UpdateLessonPayload {
  title?: string;
  description?: string | null;
  module_id?: string | null;
  position?: number;
}

export interface CreateModulePayload {
  title: string;
  position?: number;
}

export interface UpdateModulePayload {
  title?: string;
  position?: number;
}

export interface CreateNotePayload {
  content: string;
  video_timestamp: number;
}

export interface ImportResult {
  imported: number;
  lessons: Lesson[];
}

// Local Folder Import
export interface LocalFolderEntry {
  name: string;
  type: "directory" | "file";
  size_bytes?: number;
  path: string;
}

export interface LocalBrowseResponse {
  available: boolean;
  path: string;
  entries: LocalFolderEntry[];
}

export interface LocalImportProgress {
  type: "progress" | "error" | "result";
  current?: number;
  total?: number;
  filename?: string;
  status?: string;
  detail?: string;
  imported?: number;
  lessons?: Lesson[];
}
