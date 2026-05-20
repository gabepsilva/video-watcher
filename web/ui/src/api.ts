export type ApiMeta = {
  whisper_models: string[];
  summary_models: string[];
  output_formats: string[];
  popular_languages?: string[];
  format_presets?: string[];
  /** Absolute path the API uses for ``python -m vw`` jobs. */
  subprocess_python?: string;
  /** False if that interpreter cannot ``import torch`` (jobs will fail like the CLI would). */
  subprocess_torch_import_ok?: boolean;
  /** PyTorch reports CUDA for the job interpreter (native + mic). */
  gpu_available?: boolean;
  /** Native ``torch.cuda.is_available()`` on the job Python (mic + native jobs). */
  gpu_cuda_native?: boolean;
  /** Host has GPU devices for ``video-watcher-docker`` (e.g. AMD ``/dev/kfd``). */
  host_gpu_devices?: boolean;
  /** ``docker`` or ``podman`` daemon reachable. */
  docker_available?: boolean;
  docker_script?: string;
  repo_root?: string;
};

export type JobSummary = {
  id: string;
  kind: string;
  state: string;
  created_at: string;
  exit_code: number | null;
  error: string | null;
};

export type JobDetail = JobSummary & {
  artifacts: { name: string; url: string }[];
  log_tail: string[];
};

export async function getMeta(): Promise<ApiMeta> {
  const r = await fetch("/api/meta");
  if (!r.ok) {
    throw new Error(`GET /api/meta failed: ${r.status}`);
  }
  return r.json() as Promise<ApiMeta>;
}

export async function createJob(form: FormData): Promise<{ job_id: string }> {
  const r = await fetch("/api/jobs", { method: "POST", body: form });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`POST /api/jobs failed: ${r.status} ${t}`);
  }
  return r.json() as Promise<{ job_id: string }>;
}

export async function listJobs(): Promise<JobSummary[]> {
  const r = await fetch("/api/jobs");
  if (!r.ok) {
    throw new Error(`GET /api/jobs failed: ${r.status}`);
  }
  return r.json() as Promise<JobSummary[]>;
}

export async function getJob(id: string): Promise<JobDetail> {
  const r = await fetch(`/api/jobs/${id}`);
  if (!r.ok) {
    throw new Error(`GET /api/jobs/${id} failed: ${r.status}`);
  }
  return r.json() as Promise<JobDetail>;
}

export async function transcribeMic(
  blob: Blob,
  opts: { model: string; language: string; gpu: boolean },
): Promise<{ text: string; language?: string }> {
  const fd = new FormData();
  fd.append("audio", blob, "phrase.webm");
  fd.append("model", opts.model);
  if (opts.language.trim()) {
    fd.append("language", opts.language.trim());
  }
  fd.append("gpu", opts.gpu ? "true" : "false");
  const r = await fetch("/api/mic/transcribe", { method: "POST", body: fd });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`POST /api/mic/transcribe failed: ${r.status} ${t}`);
  }
  return r.json() as Promise<{ text: string; language?: string }>;
}
