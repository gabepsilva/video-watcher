import type { JobSummary } from "../api";
import { Icons } from "../icons/Icons";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHead } from "../components/ui/PageHead";
import { StateBadge } from "../components/ui/StateBadge";

type Props = {
  jobs: JobSummary[];
  onOpenJob: (id: string) => void;
  onNewJob: () => void;
  historyOnly?: boolean;
};

function jobTitle(j: JobSummary): string {
  if (j.kind === "youtube") return `YouTube · ${j.id}`;
  return `File · ${j.id}`;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

function JobRow({ job, onClick }: { job: JobSummary; onClick: () => void }) {
  const Ico = job.kind === "youtube" ? Icons.Yt : Icons.File;
  return (
    <button type="button" className="job-row" onClick={onClick}>
      <span className="u-muted">
        <Ico size={16} stroke={1.5} />
      </span>
      <div className="job-row__ident">
        <div className="job-row__title-row">
          <span className="job-row__title">{jobTitle(job)}</span>
        </div>
        <div className="job-row__meta">
          <span className="job-row__id">{job.id}</span>
          <span className="job-row__sep">·</span>
          <span>{job.kind}</span>
        </div>
      </div>
      <span className="job-row__time">{formatTime(job.created_at)}</span>
      <StateBadge state={job.state} />
      <span className="u-muted">
        <Icons.Chev size={14} stroke={1.8} />
      </span>
    </button>
  );
}

function JobSection({
  title,
  sub,
  jobs,
  onOpenJob,
}: {
  title: string;
  sub: string;
  jobs: JobSummary[];
  onOpenJob: (id: string) => void;
}) {
  if (jobs.length === 0) return null;
  return (
    <Card title={title} sub={sub} flush>
      {jobs.map((j) => (
        <JobRow key={j.id} job={j} onClick={() => onOpenJob(j.id)} />
      ))}
    </Card>
  );
}

export function JobsView({ jobs, onOpenJob, onNewJob, historyOnly }: Props) {
  const running = jobs.filter((j) => j.state === "running");
  const queued = jobs.filter((j) => j.state === "queued");
  const recent = jobs.filter((j) => j.state !== "running" && j.state !== "queued");

  const list = historyOnly ? recent : jobs;
  const title = historyOnly ? "History" : "Jobs";
  const sub = historyOnly
    ? "Completed and failed transcriptions."
    : "One transcription runs at a time. Newer jobs queue when the worker is busy.";

  return (
    <div className="page">
      <PageHead
        title={title}
        sub={sub}
        actions={
          <Button onClick={onNewJob}>
            <Icons.Plus size={14} stroke={1.8} />
            New job
          </Button>
        }
      />

      {!historyOnly ? (
        <>
          <JobSection
            title="Active"
            sub={`${running.length} running · ${queued.length} queued`}
            jobs={[...running, ...queued]}
            onOpenJob={onOpenJob}
          />
          <Card title="Recent" sub={`${recent.length}`} flush>
            {recent.length > 0 ? (
              recent.map((j) => <JobRow key={j.id} job={j} onClick={() => onOpenJob(j.id)} />)
            ) : (
              <div style={{ padding: 24, color: "var(--dim)", fontSize: 13 }}>No completed jobs yet.</div>
            )}
          </Card>
        </>
      ) : (
        <Card title="All finished" sub={`${list.length}`} flush>
          {list.length > 0 ? (
            list.map((j) => <JobRow key={j.id} job={j} onClick={() => onOpenJob(j.id)} />)
          ) : (
            <div style={{ padding: 24, color: "var(--dim)", fontSize: 13 }}>No history yet.</div>
          )}
        </Card>
      )}
    </div>
  );
}
