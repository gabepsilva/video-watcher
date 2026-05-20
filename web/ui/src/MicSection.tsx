import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiMeta } from "./api";
import { transcribeMic } from "./api";
import { GpuField } from "./GpuField";

type Props = {
  meta: ApiMeta | null;
};

export function MicSection({ meta }: Props) {
  const [model, setModel] = useState("base");
  const [language, setLanguage] = useState("");
  const [gpu, setGpu] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);

  useEffect(() => {
    if (meta?.gpu_available) {
      setGpu(true);
    } else {
      setGpu(false);
    }
  }, [meta?.gpu_available]);

  const pushLine = useCallback((t: string) => {
    setLines((prev) => [...prev, t]);
  }, []);

  async function startRecording() {
    setErr(null);
    chunksRef.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    const rec = new MediaRecorder(stream, { mimeType: mime });
    rec.ondataavailable = (ev) => {
      if (ev.data.size > 0) {
        chunksRef.current.push(ev.data);
      }
    };
    rec.onstop = () => {
      for (const t of stream.getTracks()) {
        t.stop();
      }
    };
    recRef.current = rec;
    rec.start();
    setRecording(true);
  }

  async function stopAndTranscribe() {
    const rec = recRef.current;
    if (!rec || rec.state === "inactive") {
      setRecording(false);
      return;
    }
    const mimeType = rec.mimeType;
    setBusy(true);
    setErr(null);
    await new Promise<void>((resolve) => {
      rec.addEventListener("stop", () => resolve(), { once: true });
      rec.stop();
    });
    setRecording(false);
    recRef.current = null;
    const blob = new Blob(chunksRef.current, { type: mimeType });
    chunksRef.current = [];
    if (blob.size < 256) {
      setBusy(false);
      setErr("Recording too short — speak for a second or two, then stop.");
      return;
    }
    try {
      const out = await transcribeMic(blob, {
        model,
        language,
        gpu,
      });
      pushLine(out.text || "(empty)");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  }

  const languages = meta?.popular_languages ?? ["en", "es", "fr", "de", "pt"];

  return (
    <section className="panel">
      <h2>Microphone (browser → API)</h2>
      <p className="muted">
        Records one take in the browser, then sends audio to <code>/api/mic/transcribe</code> (always native Whisper in the
        API process, not Docker). Press Record, speak, then Stop &amp; transcribe.
      </p>
      <div className="row">
        <label>
          Model
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {(meta?.whisper_models ?? ["base"]).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <label>
          Language (optional)
          <input
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            list="mic-lang"
            placeholder="en"
          />
          <datalist id="mic-lang">
            {languages.map((code) => (
              <option key={code} value={code} />
            ))}
          </datalist>
        </label>
        <GpuField meta={meta} checked={gpu} onChange={setGpu} />
      </div>
      <div className="row">
        <button type="button" onClick={() => void startRecording()} disabled={recording || busy}>
          Record
        </button>
        <button type="button" onClick={() => void stopAndTranscribe()} disabled={!recording || busy}>
          Stop &amp; transcribe
        </button>
      </div>
      {err ? <p className="error">{err}</p> : null}
      <h3>Phrases</h3>
      <ol>
        {lines.map((l, i) => (
          <li key={`${i}-${l.slice(0, 12)}`}>{l}</li>
        ))}
      </ol>
    </section>
  );
}
