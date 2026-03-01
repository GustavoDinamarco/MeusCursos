import { useState, useEffect, useRef, useCallback } from "react";
import { Lesson } from "@/types/course";
import { videoStreamUrl } from "@/lib/storage";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Video,
} from "lucide-react";

/* ----------------------------------------------------------------
   Minimal YouTube IFrame Player API types
   ---------------------------------------------------------------- */
interface YTPlayer {
  getCurrentTime(): number;
  getDuration(): number;
  getVolume(): number;
  isMuted(): boolean;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  playVideo(): void;
  pauseVideo(): void;
  mute(): void;
  unMute(): void;
  setVolume(volume: number): void;
  getPlayerState(): number;
  destroy(): void;
}

interface YTPlayerConstructor {
  new (
    element: HTMLElement,
    options: {
      videoId: string;
      width?: string | number;
      height?: string | number;
      playerVars?: Record<string, number | string>;
      events?: Record<string, (event: { data: number }) => void>;
    },
  ): YTPlayer;
}

declare global {
  interface Window {
    YT?: { Player: YTPlayerConstructor; PlayerState: Record<string, number> };
    onYouTubeIframeAPIReady?: () => void;
  }
}

/* ----------------------------------------------------------------
   YouTube IFrame API loader (singleton)
   ---------------------------------------------------------------- */
let ytApiLoaded = false;
let ytApiReady = false;
const ytReadyCallbacks: Array<() => void> = [];

function loadYouTubeApi(): Promise<void> {
  return new Promise((resolve) => {
    if (ytApiReady && window.YT) {
      resolve();
      return;
    }
    ytReadyCallbacks.push(resolve);
    if (!ytApiLoaded) {
      ytApiLoaded = true;
      window.onYouTubeIframeAPIReady = () => {
        ytApiReady = true;
        ytReadyCallbacks.forEach((cb) => cb());
        ytReadyCallbacks.length = 0;
      };
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    }
  });
}

/* ----------------------------------------------------------------
   Helpers
   ---------------------------------------------------------------- */
function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return "0:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/* ----------------------------------------------------------------
   VideoPlayer Component
   ---------------------------------------------------------------- */
interface VideoPlayerProps {
  lesson: Lesson | null;
  /** Ref forwarded so parent (WatchCourse) can get currentTime for notes */
  onTimeRef?: (getter: () => number) => void;
  /** Called to seek to a specific timestamp (for clicking notes) */
  onSeekRef?: (seeker: (seconds: number) => void) => void;
}

const VideoPlayer = ({ lesson, onTimeRef, onSeekRef }: VideoPlayerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const ytPlayerRef = useRef<YTPlayer | null>(null);
  const ytContainerRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout>>();

  const source = lesson?.video_source ?? null;

  // Expose getCurrentTime to parent
  useEffect(() => {
    if (onTimeRef) {
      onTimeRef(() => {
        if (source === "youtube" && ytPlayerRef.current) {
          return Math.floor(ytPlayerRef.current.getCurrentTime());
        }
        if (videoRef.current) return Math.floor(videoRef.current.currentTime);
        return 0;
      });
    }
  }, [onTimeRef, source]);

  // Expose seek to parent
  useEffect(() => {
    if (onSeekRef) {
      onSeekRef((seconds: number) => {
        if (source === "youtube" && ytPlayerRef.current) {
          ytPlayerRef.current.seekTo(seconds, true);
        } else if (videoRef.current) {
          videoRef.current.currentTime = seconds;
          videoRef.current.play();
        }
      });
    }
  }, [onSeekRef, source]);

  // Auto-hide controls after 3s of no mouse movement
  const resetHideTimer = useCallback(() => {
    setShowControls(true);
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    hideTimerRef.current = setTimeout(() => {
      if (playing) setShowControls(false);
    }, 3000);
  }, [playing]);

  // MinIO video: sync state from <video> events
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid || source !== "minio") return;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onTimeUpdate = () => setCurrentTime(vid.currentTime);
    const onDurationChange = () => setDuration(vid.duration);
    const onVolumeChange = () => {
      setVolume(vid.volume);
      setMuted(vid.muted);
    };

    vid.addEventListener("play", onPlay);
    vid.addEventListener("pause", onPause);
    vid.addEventListener("timeupdate", onTimeUpdate);
    vid.addEventListener("durationchange", onDurationChange);
    vid.addEventListener("volumechange", onVolumeChange);

    return () => {
      vid.removeEventListener("play", onPlay);
      vid.removeEventListener("pause", onPause);
      vid.removeEventListener("timeupdate", onTimeUpdate);
      vid.removeEventListener("durationchange", onDurationChange);
      vid.removeEventListener("volumechange", onVolumeChange);
    };
  }, [source, lesson?.id]);

  // YouTube player lifecycle
  useEffect(() => {
    if (source !== "youtube") {
      if (ytPlayerRef.current) {
        try {
          ytPlayerRef.current.destroy();
        } catch {
          /* already destroyed */
        }
        ytPlayerRef.current = null;
      }
      return;
    }

    const videoId = lesson!.video_url!.replace("youtube:", "");
    let cancelled = false;
    let pollInterval: ReturnType<typeof setInterval>;

    loadYouTubeApi().then(() => {
      if (cancelled || !ytContainerRef.current || !window.YT) return;

      ytContainerRef.current.innerHTML = "";
      const target = document.createElement("div");
      ytContainerRef.current.appendChild(target);

      const player = new window.YT.Player(target, {
        videoId,
        width: "100%",
        height: "100%",
        playerVars: { autoplay: 0, rel: 0, modestbranding: 1, controls: 0 },
        events: {
          onStateChange: (e: { data: number }) => {
            setPlaying(e.data === 1);
          },
          onReady: () => {
            setDuration(player.getDuration());
            setVolume(player.getVolume() / 100);
            setMuted(player.isMuted());
          },
        },
      });

      ytPlayerRef.current = player;

      // Poll for time updates since YT API doesn't have a timeupdate event
      pollInterval = setInterval(() => {
        if (ytPlayerRef.current) {
          try {
            setCurrentTime(ytPlayerRef.current.getCurrentTime());
            const dur = ytPlayerRef.current.getDuration();
            if (dur > 0) setDuration(dur);
          } catch {
            /* player may be destroyed */
          }
        }
      }, 500);
    });

    return () => {
      cancelled = true;
      clearInterval(pollInterval);
      if (ytPlayerRef.current) {
        try {
          ytPlayerRef.current.destroy();
        } catch {
          /* noop */
        }
        ytPlayerRef.current = null;
      }
    };
  }, [lesson?.id, source]);

  // Fullscreen change listener
  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  // Reset state when lesson changes
  useEffect(() => {
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setShowControls(true);
  }, [lesson?.id]);

  // ---- Control Handlers ----

  const togglePlay = () => {
    if (source === "youtube" && ytPlayerRef.current) {
      if (playing) ytPlayerRef.current.pauseVideo();
      else ytPlayerRef.current.playVideo();
    } else if (videoRef.current) {
      if (playing) videoRef.current.pause();
      else videoRef.current.play();
    }
  };

  const toggleMute = () => {
    if (source === "youtube" && ytPlayerRef.current) {
      if (muted) ytPlayerRef.current.unMute();
      else ytPlayerRef.current.mute();
      setMuted(!muted);
    } else if (videoRef.current) {
      videoRef.current.muted = !muted;
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (source === "youtube" && ytPlayerRef.current) {
      ytPlayerRef.current.setVolume(val * 100);
      if (val > 0 && muted) {
        ytPlayerRef.current.unMute();
        setMuted(false);
      }
    } else if (videoRef.current) {
      videoRef.current.volume = val;
      if (val > 0 && muted) {
        videoRef.current.muted = false;
      }
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current || duration <= 0) return;
    const rect = progressRef.current.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const seekTime = ratio * duration;
    if (source === "youtube" && ytPlayerRef.current) {
      ytPlayerRef.current.seekTo(seekTime, true);
    } else if (videoRef.current) {
      videoRef.current.currentTime = seekTime;
    }
    setCurrentTime(seekTime);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current.requestFullscreen();
    }
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  // Google Drive: no custom controls
  if (source === "google_drive" && lesson) {
    return (
      <div className="relative aspect-video rounded-xl overflow-hidden bg-black shadow-2xl ring-1 ring-primary/10">
        <iframe
          key={lesson.id}
          className="h-full w-full border-0"
          src={`https://drive.google.com/file/d/${lesson.video_url!.replace("drive:", "")}/preview`}
          allow="autoplay"
          title={lesson.title}
        />
      </div>
    );
  }

  // No lesson or no video
  if (!lesson || !lesson.video_url) {
    return (
      <div className="relative aspect-video rounded-xl overflow-hidden bg-black shadow-2xl ring-1 ring-primary/10 flex items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Video className="h-10 w-10" />
          <span className="text-sm">
            {lesson ? "Nenhum video enviado para esta aula" : "Selecione uma aula"}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="group/player relative aspect-video rounded-xl overflow-hidden bg-black shadow-2xl ring-1 ring-primary/10"
      onMouseMove={resetHideTimer}
      onMouseLeave={() => {
        if (playing) setShowControls(false);
      }}
    >
      {/* Video Element */}
      {source === "minio" && (
        <video
          ref={videoRef}
          key={lesson.id}
          className="h-full w-full"
          src={videoStreamUrl(lesson.id)}
          onClick={togglePlay}
        />
      )}

      {source === "youtube" && (
        <div
          ref={ytContainerRef}
          className="h-full w-full pointer-events-none"
        />
      )}

      {/* Center Play Button (when paused) */}
      {!playing && (
        <div
          className="absolute inset-0 flex items-center justify-center cursor-pointer"
          onClick={togglePlay}
        >
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/90 text-primary-foreground transition-transform hover:scale-110">
            <Play className="h-8 w-8 ml-1" />
          </div>
        </div>
      )}

      {/* Clickable area for YouTube (to toggle play/pause) */}
      {source === "youtube" && playing && (
        <div
          className="absolute inset-0 cursor-pointer"
          onClick={togglePlay}
        />
      )}

      {/* Bottom Controls Overlay */}
      <div
        className={`absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent px-4 pb-4 pt-12 transition-opacity duration-300 ${
          showControls ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        {/* Progress Bar */}
        <div
          ref={progressRef}
          className="group/progress mb-3 h-1.5 w-full cursor-pointer rounded-full bg-white/20"
          onClick={handleSeek}
        >
          <div
            className="relative h-full rounded-full bg-primary"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute right-0 top-1/2 h-4 w-4 -translate-y-1/2 translate-x-1/2 scale-0 rounded-full bg-primary transition-transform group-hover/progress:scale-100" />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-4">
          <button onClick={togglePlay} className="text-white hover:text-primary transition-colors">
            {playing ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </button>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <button onClick={toggleMute} className="text-white hover:text-primary transition-colors">
              {muted || volume === 0 ? (
                <VolumeX className="h-5 w-5" />
              ) : (
                <Volume2 className="h-5 w-5" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={muted ? 0 : volume}
              onChange={handleVolumeChange}
              className="h-1 w-20 cursor-pointer appearance-none rounded-full bg-white/30 accent-primary [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
            />
          </div>

          {/* Time */}
          <span className="text-xs text-white/80 font-medium">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="flex-1" />

          {/* Fullscreen */}
          <button onClick={toggleFullscreen} className="text-white hover:text-primary transition-colors">
            {isFullscreen ? (
              <Minimize className="h-5 w-5" />
            ) : (
              <Maximize className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
