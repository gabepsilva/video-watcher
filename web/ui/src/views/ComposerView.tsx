import { type FormEvent, useState } from "react";
import type { ApiMeta } from "../api";
import { createJob } from "../api";
import { Icons } from "../icons/Icons";
import { Button } from "../components/ui/Button";
import { Dropzone } from "../components/ui/Dropzone";
import { FormatChips } from "../components/ui/FormatChips";
import { Field, FieldHelp, FieldLabel, FieldRow, SelectInput, TextInput } from "../components/ui/Field";
import { ModeTabs, type ComposerMode } from "../components/ui/ModeTabs";
import { PageHead } from "../components/ui/PageHead";

type Props = {
  meta: ApiMeta | null;
  onJobStarted: (jobId: string) => void;
};

function parseFormats(selected: string[]): string {
  if (selected.length === 0 || selected.length >= 4) return "all";
  return selected.join(",");
}

export function ComposerView({ meta, onJobStarted }: Props) {
  const [mode, setMode] = useState<ComposerMode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [formats, setFormats] = useState<string[]>(["srt", "vtt", "txt"]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const models = meta?.whisper_models ?? ["base"];
  const summaryModels = meta?.summary_models ?? ["gemma-4-e4b"];
  const languages = meta?.popular_languages ?? ["en", "es", "fr", "de", "pt"];
  const formatPresets = meta?.format_presets ?? ["all", "srt", "vtt", "txt", "srt,vtt,txt"];
  const chipOptions = ["srt", "vtt", "txt", "json"];
  const gpuAvailable = meta?.gpu_available === true;
  const gpuDefault = meta?.gpu_available === true;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    const form = e.currentTarget;
    const fd = new FormData(form);
    fd.set("job_type", mode);
    if (mode === "file") {
      if (!file) {
        setErr("Choose a media file.");
        return;
      }
      fd.set("file", file);
    } else {
      fd.set("youtube_url", url.trim());
    }
    fd.set("formats", parseFormats(formats));
    const gpuEl = form.elements.namedItem("gpu") as HTMLInputElement | null;
    const verboseEl = form.elements.namedItem("verbose") as HTMLInputElement | null;
    const summaryEl = form.elements.namedItem("summary") as HTMLInputElement | null;
    fd.set("gpu", gpuEl?.checked ? "true" : "false");
    fd.set("verbose", verboseEl?.checked ? "true" : "false");
    fd.set("summary", summaryEl?.checked ? "true" : "false");

    setBusy(true);
    try {
      const { job_id } = await createJob(fd);
      onJobStarted(job_id);
      form.reset();
      setFile(null);
      setUrl("");
      setFormats(["srt", "vtt", "txt"]);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  }

  const canSubmit = (mode === "file" && file) || (mode === "youtube" && url.trim().length > 0);

  return (
    <div className="page">
      <PageHead
        title="New transcription"
        sub="File upload or YouTube URL — Whisper runs in the API container (docker compose)."
      />

      <ModeTabs
        mode={mode}
        onMode={setMode}
        tabs={[
          { id: "file", label: (<><Icons.File size={14} /> File</>) },
          { id: "youtube", label: (<><Icons.Yt size={14} /> YouTube</>) },
        ]}
      />

      <form key={gpuDefault ? "gpu-on" : "gpu-off"} onSubmit={onSubmit}>
        <section className="card">
          <div className="card__body card__body--stack">
            {mode === "file" ? (
              <Dropzone file={file} onFile={setFile} />
            ) : (
              <Field>
                <FieldLabel label="YouTube URL" hint="watch · shorts · youtu.be" htmlFor="yt-url" />
                <TextInput
                  id="yt-url"
                  mono
                  placeholder="https://youtube.com/watch?v=…"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
                <FieldHelp>Captions download first when available — falls back to audio + Whisper.</FieldHelp>
              </Field>
            )}

            <FieldRow>
              <Field>
                <FieldLabel label="Model" />
                <SelectInput name="model" defaultValue="base">
                  {models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </SelectInput>
              </Field>
              <Field>
                <FieldLabel label="Language" hint="optional ISO" />
                <TextInput name="language" list="composer-lang" placeholder="en" />
                <datalist id="composer-lang">
                  {languages.map((code) => (
                    <option key={code} value={code} />
                  ))}
                </datalist>
              </Field>
            </FieldRow>

            <Field>
              <FieldLabel label="Formats" />
              <FormatChips value={formats} onChange={setFormats} options={chipOptions} />
              <FieldHelp>Suggested: {formatPresets.join(", ")}</FieldHelp>
            </Field>

            <details className="disclosure">
              <summary>
                <Icons.Chev size={14} className="disclosure__chev" />
                Advanced options
              </summary>
              <div className="disclosure__body">
                <Field>
                  <FieldLabel label="Summary model" />
                  <SelectInput name="summary_model" defaultValue={summaryModels[0]}>
                    {summaryModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </SelectInput>
                </Field>
                <label className="checkbox-row">
                  <input name="gpu" type="checkbox" defaultChecked={gpuDefault} disabled={!gpuAvailable} />
                  <span>
                    <div className="checkbox-row__lbl">GPU</div>
                    <div className="checkbox-row__sub">
                      {gpuAvailable ? "Use CUDA/ROCm when available" : "No GPU detected on host"}
                    </div>
                  </span>
                </label>
                <label className="checkbox-row">
                  <input name="verbose" type="checkbox" />
                  <span>
                    <div className="checkbox-row__lbl">Verbose</div>
                    <div className="checkbox-row__sub">Live text instead of progress bar</div>
                  </span>
                </label>
                <label className="checkbox-row">
                  <input name="summary" type="checkbox" />
                  <span>
                    <div className="checkbox-row__lbl">Summary</div>
                    <div className="checkbox-row__sub">Requires llama-cli after transcription</div>
                  </span>
                </label>
              </div>
            </details>
          </div>

          <div className="submit-bar">
            <div className="submit-bar__summary">
              <span>
                Runtime: <b>Docker</b>
              </span>
            </div>
            <Button type="submit" variant="primary" disabled={busy || !canSubmit}>
              {busy ? "Starting…" : "Start job"}
            </Button>
          </div>
        </section>
      </form>

      {err ? <p className="alert">{err}</p> : null}
    </div>
  );
}
