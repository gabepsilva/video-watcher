import type { ApiMeta } from "../api";
import { Icons } from "../icons/Icons";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHead } from "../components/ui/PageHead";
import { StateBadge } from "../components/ui/StateBadge";

type Props = {
  meta: ApiMeta | null;
  metaErr: string | null;
  onRefresh: () => void;
  refreshing: boolean;
};

function DiagRow({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status?: "ok" | "warn" | "err";
}) {
  return (
    <div className="diag-row">
      <div className="diag-row__key">{label}</div>
      <div className={`diag-row__val${status ? ` diag-row__val--${status}` : ""}`}>{value}</div>
      <div>
        {status === "ok" ? <StateBadge state="succeeded" /> : null}
        {status === "warn" ? (
          <span className="state-badge" style={{ background: "var(--amber-bg)", color: "var(--amber)" }}>
            <span className="dot" style={{ background: "var(--amber)" }} />
            warn
          </span>
        ) : null}
        {status === "err" ? <StateBadge state="failed" /> : null}
      </div>
    </div>
  );
}

export function DiagnosticsView({ meta, metaErr, onRefresh, refreshing }: Props) {
  const pending = meta === null && !metaErr;

  return (
    <div className="page">
      <PageHead
        title="Diagnostics"
        sub="Compose stack — Whisper runs in the API container via python -m vw."
        actions={
          <Button onClick={onRefresh} disabled={refreshing}>
            <Icons.Refresh size={13} stroke={1.8} />
            {refreshing ? "Refreshing…" : "Refresh probe"}
          </Button>
        }
      />

      {metaErr ? <p className="alert">{metaErr}</p> : null}

      <Card
        title={
          <span className="u-flex u-gap-2">
            <Icons.Cpu size={14} stroke={1.6} /> Hardware
          </span>
        }
        flush
      >
        <DiagRow
          label="GPU detected"
          status={pending ? undefined : meta?.gpu_available ? "ok" : "err"}
          value={pending ? "…" : meta?.gpu_available ? "yes" : "none"}
        />
        <DiagRow
          label="CUDA/ROCm in container"
          status={pending ? undefined : meta?.gpu_cuda_native ? "ok" : "warn"}
          value={pending ? "…" : meta?.gpu_cuda_native ? "available" : "CPU image — rebuild API with GPU base for --gpu"}
        />
        <DiagRow
          label="Container runtime"
          status={pending ? undefined : meta?.container_runtime ? "ok" : "err"}
          value={pending ? "…" : meta?.container_runtime ? "VIDEO_WATCHER_RUNTIME=container" : "not in compose"}
        />
      </Card>

      <Card
        title={
          <span className="u-flex u-gap-2">
            <Icons.Python size={14} stroke={1.6} /> Runtime
          </span>
        }
        flush
      >
        <DiagRow label="Subprocess Python" status="ok" value={meta?.subprocess_python ?? "…"} />
        <DiagRow
          label="PyTorch importable"
          status={pending ? undefined : meta?.subprocess_torch_import_ok ? "ok" : "err"}
          value={
            pending
              ? "…"
              : meta?.subprocess_torch_import_ok
                ? "import torch → ok"
                : "missing — docker compose build --no-cache api"
          }
        />
      </Card>

      <Card
        title={
          <span className="u-flex u-gap-2">
            <Icons.Box size={14} stroke={1.6} /> Models
          </span>
        }
        flush
      >
        <DiagRow label="Summary models" value={meta?.summary_models?.join(", ") ?? "…"} />
        <DiagRow label="Whisper sizes" value={meta?.whisper_models?.join(" · ") ?? "…"} />
        <DiagRow label="Output formats" value={meta?.output_formats?.join(" · ") ?? "…"} />
      </Card>

      <Card
        title="API"
        flush
      >
        <DiagRow label="Bind" status="ok" value="api:8765 · ui:80 · no auth" />
        <DiagRow label="Repo root" value={meta?.repo_root ?? "…"} />
      </Card>
    </div>
  );
}
