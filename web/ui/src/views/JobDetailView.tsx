import { useEffect, useRef, useState } from "react";
import type { JobDetail } from "../api";
import { getJob } from "../api";
import { Icons } from "../icons/Icons";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateBadge } from "../components/ui/StateBadge";

type Props = {
  jobId: string;
  onBack: () => void;
};

function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "file";
}

export function JobDetailView({ jobId, onBack }: Props) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [streamLog, setStreamLog] = useState("");
  const streamRef = useRef("");

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const j = await getJob(jobId);
        if (!cancelled) setJob(j);
      } catch {
        if (!cancelled) setJob(null);
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
        if (msg.kind === "done") es.close();
      } catch {
        /* ignore malformed chunks */
      }
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, [jobId]);

  const state = job?.state ?? "…";

  return (
    <div className="page">
      <div className="job-detail__head">
        <div className="job-detail__title">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <Icons.ArrowLeft size={14} />
            Jobs
          </Button>
          <h1 className="page__title" style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 10 }}>
            {job?.kind === "youtube" ? "YouTube job" : "File job"}
            <StateBadge state={state} />
          </h1>
          <div className="job-detail__meta-row">
            <span>{jobId}</span>
            {job?.created_at ? <span>· {new Date(job.created_at).toLocaleString()}</span> : null}
          </div>
        </div>
      </div>

      {job?.error ? (
        <Card error title="Job failed" sub={job.exit_code != null ? `exit ${job.exit_code}` : undefined}>
          <p className="alert">{job.error}</p>
        </Card>
      ) : null}

      <Card
        title="Live log"
        sub={
          <span className="u-flex u-gap-2">
            <span className="dot dot--live" />
            streaming
          </span>
        }
        flush
      >
        <pre className="log-view log-view--plain">{streamLog || "…"}</pre>
      </Card>

      <Card title="Artifacts" sub={`${job?.artifacts?.length ?? 0} files`} flush>
        {job?.artifacts?.length ? (
          job.artifacts.map((a) => (
            <div key={a.name} className="artifact-row">
              <div className="artifact-row__fmt" data-fmt={extOf(a.name)}>
                {extOf(a.name)}
              </div>
              <div className="artifact-row__name">{a.name}</div>
              <a className="btn btn--sm" href={a.url} download>
                <Icons.Download size={13} />
                Download
              </a>
            </div>
          ))
        ) : (
          <div style={{ padding: 24, color: "var(--dim)", fontSize: 13 }}>No files yet (job may still be running).</div>
        )}
      </Card>

      <Card title="Log tail (poll)" flush>
        <pre className="log-view log-view--plain">{job?.log_tail?.join("\n") || "…"}</pre>
      </Card>
    </div>
  );
}
