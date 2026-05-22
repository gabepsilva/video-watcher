/** Classify job files for preview / editor UI. */

const VIDEO = new Set(["mp4", "mkv", "webm", "mov", "avi", "m4v", "flv", "ts", "m2ts"]);
const AUDIO = new Set(["mp3", "wav", "flac", "ogg", "opus", "m4a", "aac", "wma"]);
const TEXT = new Set([
  "txt",
  "md",
  "markdown",
  "srt",
  "vtt",
  "json",
  "tsv",
  "csv",
  "log",
  "yml",
  "yaml",
]);

export function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

export function isVideoFile(name: string): boolean {
  return VIDEO.has(extOf(name));
}

export function isAudioFile(name: string): boolean {
  return AUDIO.has(extOf(name));
}

export function isMediaFile(name: string): boolean {
  return isVideoFile(name) || isAudioFile(name);
}

export function isTextFile(name: string): boolean {
  return TEXT.has(extOf(name));
}

export function isMarkdownFile(name: string): boolean {
  const ext = extOf(name);
  return ext === "md" || ext === "markdown";
}

export function textPreviewLabel(name: string): string {
  const ext = extOf(name);
  if (ext === "json") return "JSON";
  if (ext === "srt") return "SRT";
  if (ext === "vtt") return "VTT";
  if (ext === "md" || ext === "markdown") return "Markdown";
  if (ext === "tsv" || ext === "csv") return ext.toUpperCase();
  return "Text";
}
