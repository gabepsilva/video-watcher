import { useState } from "react";
import type { JobDetail } from "../../api";
import { Card } from "../ui/Card";
import { ArtifactPanel } from "./ArtifactPanel";
import { SourceMediaBlock } from "./SourceMediaBlock";

type Props = {
  jobId: string;
  job: JobDetail | null;
};

export function ArtifactsCard({ jobId, job }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const artifacts = job?.artifacts ?? [];
  const count = artifacts.length + (job?.source_media ? 1 : 0);

  function toggle(name: string) {
    setExpanded((prev) => (prev === name ? null : name));
  }

  return (
    <Card title="Artifacts" sub={`${count} item${count === 1 ? "" : "s"}`} flush>
      {job?.source_media ? <SourceMediaBlock media={job.source_media} /> : null}
      {artifacts.length > 0 ? (
        artifacts.map((a) => (
          <ArtifactPanel
            key={a.name}
            jobId={jobId}
            artifact={a}
            expanded={expanded === a.name}
            onToggle={() => toggle(a.name)}
          />
        ))
      ) : !job?.source_media ? (
        <div style={{ padding: 24, color: "var(--dim)", fontSize: 13 }}>
          No files yet (job may still be running).
        </div>
      ) : null}
    </Card>
  );
}
