import { type FormEvent, useState } from "react";
import type { ApiMeta } from "./api";
import { createJob } from "./api";
import { JobFormOptions } from "./JobFormOptions";

type Props = {
  meta: ApiMeta | null;
  useDocker: boolean;
  onJobStarted: (jobId: string) => void;
};

export function YoutubeJobSection({ meta, useDocker, onJobStarted }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    const form = e.currentTarget;
    const fd = new FormData(form);
    fd.set("job_type", "youtube");
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

  const runtime = useDocker ? "Docker" : "native";

  return (
    <section className="panel">
      <h2>YouTube</h2>
      <p className="muted">
        Runs <code>--yt</code> via <strong>{runtime}</strong> (captions / transcript API / Whisper fallback).
      </p>
      <form key={meta?.gpu_available === true ? "gpu-on" : "gpu-off"} onSubmit={onSubmit}>
        <label>
          YouTube URL
          <input name="youtube_url" type="url" required placeholder="https://www.youtube.com/watch?v=…" />
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
        <JobFormOptions
          meta={meta}
          languageListId="yt-lang"
          formatsListId="yt-fmt"
          languagePlaceholder="subtitle / transcript preference"
        />
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
            <input name="verbose" type="checkbox" /> Verbose
          </label>
          <label>
            <input name="summary" type="checkbox" /> Summary
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
