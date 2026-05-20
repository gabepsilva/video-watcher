import { useEffect, useRef, useState } from "react";
import type { JobDetail } from "./api";
import { getJob } from "./api";

type Props = {
  jobId: string | null;
};

export function JobMonitor({ jobId }: Props) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [streamLog, setStreamLog] = useState("");
  const streamRef = useRef("");

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setStreamLog("");
      streamRef.current = "";
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const j = await getJob(jobId);
        if (!cancelled) {
          setJob(j);
        }
      } catch {
        if (!cancelled) {
          setJob(null);
        }
      }
    };

    void poll();
    const id = window.setInterval(() => void poll(), 1000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      return;
    }
    streamRef.current = "";
    setStreamLog("");
    const es = new EventSource(`/api/jobs/${jobId}/events`);
    es.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as { kind: string; line?: string };
        if (msg.kind === "log" && msg.line) {
          streamRef.current += `${msg.line}\n`;
          setStreamLog(streamRef.current);
        }
        if (msg.kind === "done") {
          es.close();
        }
      } catch {
        /* ignore malformed chunks */
      }
    };
    es.onerror = () => {
      es.close();
    };
    return () => es.close();
  }, [jobId]);

  if (!jobId) {
    return (
      <section className="panel panel-muted">
        <h2>Job status</h2>
        <p>No active job. Start a file or YouTube transcription to see progress here.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Job status</h2>
      <p className="mono">
        <strong>id</strong> {job?.id ?? jobId} · <strong>state</strong> {job?.state ?? "…"}
      </p>
      {job?.error ? <p className="error">{job.error}</p> : null}
      <h3>Live log (SSE)</h3>
      <pre className="log">{streamLog || "…"}</pre>
      <h3>Artifacts</h3>
      {job?.artifacts?.length ? (
        <ul>
          {job.artifacts.map((a) => (
            <li key={a.name}>
              <a href={a.url} download>
                {a.name}
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">No files yet (job may still be running).</p>
      )}
      <h3>Log tail (poll)</h3>
      <pre className="log">{job?.log_tail?.join("\n") || "…"}</pre>
    </section>
  );
}
