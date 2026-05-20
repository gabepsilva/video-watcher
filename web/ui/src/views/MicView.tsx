import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiMeta } from "../api";
import { transcribeMic } from "../api";
import { Icons } from "../icons/Icons";
import { Card } from "../components/ui/Card";
import { Field, FieldLabel, FieldRow, SelectInput, TextInput } from "../components/ui/Field";
import { PageHead } from "../components/ui/PageHead";

type Phrase = { idx: number; text: string; at: string };

type Props = {
  meta: ApiMeta | null;
};

function Waveform({ live }: { live: boolean }) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!live) return;
    const id = window.setInterval(() => setTick((t) => t + 1), 60);
    return () => window.clearInterval(id);
  }, [live]);

  const bars = Array.from({ length: 48 }, (_, i) => {
    if (!live) return 4 + (Math.sin(i * 0.6) + 1) * 1.5;
    const phase = (i / 48) * Math.PI * 2 + tick * 0.4;
    const base =
      (Math.sin(phase) + Math.sin(phase * 2.3 + 1.1) + Math.sin(phase * 0.7 + 2.2)) / 3;
    return 4 + Math.abs(base) * 36 + (i % 3) * 1.5;
  });

  return (
    <div className={`waveform${live ? " waveform--live" : ""}`} aria-hidden>
      {bars.map((h, i) => (
        <div key={i} className="waveform__bar" style={{ height: `${h}px` }} />
      ))}
    </div>
  );
}

function mmss(s: number): string {
  const m = Math.floor(s / 60);
  const r = (s % 60).toFixed(1);
  return `${String(m).padStart(2, "0")}:${String(r).padStart(4, "0")}`;
}

export function MicView({ meta }: Props) {
  const [model, setModel] = useState("base");
  const [language, setLanguage] = useState("");
  const [gpu, setGpu] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const models = meta?.whisper_models ?? ["base"];
  const languages = meta?.popular_languages ?? ["en", "es", "fr", "de", "pt"];
  const gpuAvailable = meta?.gpu_available === true;

  useEffect(() => {
    setGpu(gpuAvailable);
  }, [gpuAvailable]);

  useEffect(() => {
    if (recording) {
      const start = Date.now();
      timerRef.current = window.setInterval(() => setElapsed((Date.now() - start) / 1000), 100);
    } else if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [recording]);

  const addPhrase = useCallback((text: string) => {
    setPhrases((prev) => [
      ...prev,
      { idx: prev.length + 1, text, at: new Date().toTimeString().slice(0, 8) },
    ]);
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
      if (ev.data.size > 0) chunksRef.current.push(ev.data);
    };
    rec.onstop = () => {
      for (const t of stream.getTracks()) t.stop();
    };
    recRef.current = rec;
    rec.start();
    setRecording(true);
    setElapsed(0);
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
      const out = await transcribeMic(blob, { model, language, gpu });
      addPhrase(out.text || "(empty)");
      setElapsed(0);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <PageHead
        title="Microphone"
        sub={
          <>
            Browser phrase capture → uploaded to the API → transcribed in the API container. Not the CLI{" "}
            <code className="u-mono">vw --mic</code> live VAD mode.
          </>
        }
      />

      <Card flush>
        <div className="mic__stage">
          <div className={`mic__time${recording ? "" : " mic__time--idle"}`}>{mmss(elapsed)}</div>
          <Waveform live={recording} />
          <button
            type="button"
            className={`mic__btn${recording ? " mic__btn--recording" : ""}`}
            onClick={() => void (recording ? stopAndTranscribe() : startRecording())}
            disabled={busy}
            aria-label={recording ? "Stop and transcribe" : "Record"}
          >
            {recording ? <Icons.Stop size={26} stroke={2} /> : <Icons.Mic size={28} stroke={1.8} />}
          </button>
          <div className="mic__status">
            {busy ? (
              <span style={{ color: "var(--teal)" }}>
                <span className="dot dot--live" style={{ marginRight: 6, verticalAlign: "middle" }} />
                transcribing…
              </span>
            ) : recording ? (
              "recording — click to stop & transcribe"
            ) : (
              "click to record a phrase"
            )}
          </div>
        </div>

        <div className="card__body">
          <FieldRow>
            <Field>
              <FieldLabel label="Model" />
              <SelectInput value={model} onChange={(e) => setModel(e.target.value)}>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field>
              <FieldLabel label="Language" hint="optional" />
              <TextInput
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
            </Field>
          </FieldRow>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={gpu && gpuAvailable}
              disabled={!gpuAvailable}
              onChange={(e) => setGpu(e.target.checked)}
            />
            <span>
              <div className="checkbox-row__lbl">GPU</div>
                <div className="checkbox-row__sub">
                  {gpuAvailable ? "Host GPU passed into Docker" : "Unavailable without Docker + GPU"}
                </div>
            </span>
          </label>
        </div>
      </Card>

      {err ? <p className="alert">{err}</p> : null}

      <Card title="Phrases" sub={`${phrases.length} captured`} flush>
        <div className="phrase-list">
          {phrases.length === 0 ? (
            <div style={{ padding: 24, color: "var(--dim)", fontSize: 13 }}>No phrases yet.</div>
          ) : (
            phrases.map((p) => (
              <div key={`${p.idx}-${p.at}`} className="phrase-item">
                <span className="phrase-item__idx">{p.idx}</span>
                <div className="phrase-item__body">{p.text}</div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
