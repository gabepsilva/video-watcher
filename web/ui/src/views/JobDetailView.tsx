import { useEffect, useRef, useState } from "react";
import type { JobDetail } from "../api";
import { getJob } from "../api";
import { ArtifactsCard } from "../components/artifacts/ArtifactsCard";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateBadge } from "../components/ui/StateBadge";
import { Icons } from "../icons/Icons";

type Props = {
  jobId: string;
  onBack: () => void;
};

export function JobDetailView({ jobId, onBack }: Props) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [streamLog, setStreamLog] = useState("");
  const streamRef = useRef("");
  const logElRef = useRef<HTMLPreElement>(null);

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

  useEffect(() => {
    const el = logElRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [streamLog]);

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
        <pre ref={logElRef} className="log-view log-view--plain">
          {streamLog || "…"}
        </pre>
      </Card>

      <ArtifactsCard jobId={jobId} job={job} />
    </div>
  );
}
