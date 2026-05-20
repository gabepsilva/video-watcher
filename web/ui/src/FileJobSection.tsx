import { type FormEvent, useState } from "react";
import type { ApiMeta } from "./api";
import { createJob } from "./api";
import { JobFormOptions } from "./JobFormOptions";

type Props = {
  meta: ApiMeta | null;
  useDocker: boolean;
  onJobStarted: (jobId: string) => void;
};

export function FileJobSection({ meta, useDocker, onJobStarted }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    if (!fileInput.files?.length) {
      setErr("Choose a media file.");
      return;
    }
    const fd = new FormData(form);
    fd.set("job_type", "file");
    const verboseEl = form.elements.namedItem("verbose") as HTMLInputElement | null;
    const summaryEl = form.elements.namedItem("summary") as HTMLInputElement | null;
    const gpuEl = form.elements.namedItem("gpu") as HTMLInputElement | null;
    fd.set("gpu", gpuEl?.checked ? "true" : "false");
    fd.set("use_docker", useDocker ? "true" : "false");
    fd.set("verbose", verboseEl?.checked ? "true" : "false");
    fd.set("summary", summaryEl?.checked ? "true" : "false");
    setBusy(true);
    try {
      const { job_id } = await createJob(fd);
      onJobStarted(job_id);
      form.reset();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  }

  const runtime = useDocker ? "Docker (video-watcher-docker)" : "native (.venv / python -m vw)";

  return (
    <section className="panel">
      <h2>File transcription</h2>
      <p className="muted">
        Uploads a media file and runs transcription via <strong>{runtime}</strong> (async job + downloads).
      </p>
      <form key={meta?.gpu_available === true ? "gpu-on" : "gpu-off"} onSubmit={onSubmit}>
        <label>
          Media file
          <input name="file" type="file" required />
        </label>
        <label>
          Model
          <select name="model" defaultValue="base">
            {(meta?.whisper_models ?? ["base"]).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <JobFormOptions meta={meta} languageListId="file-lang" formatsListId="file-fmt" />
        <label>
          Summary model
          <select name="summary_model" defaultValue="gemma-4-e4b">
            {(meta?.summary_models ?? ["gemma-4-e4b"]).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <div className="checks">
          <label>
            <input name="verbose" type="checkbox" /> Verbose (live text instead of progress bar)
          </label>
          <label>
            <input name="summary" type="checkbox" /> Summary (requires llama-cli)
          </label>
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Starting…" : "Start job"}
        </button>
      </form>
      {err ? <p className="error">{err}</p> : null}
    </section>
  );
}
