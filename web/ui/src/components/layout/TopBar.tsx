import type { ApiMeta } from "../../api";
import { Icons } from "../../icons/Icons";
import type { Theme } from "../../hooks/useTheme";
import { CapChip } from "../ui/CapChip";

type Props = {
  meta: ApiMeta | null;
  metaErr: string | null;
  runtime: "native" | "docker";
  setRuntime: (r: "native" | "docker") => void;
  theme: Theme;
  onToggleTheme: () => void;
  onRefresh: () => void;
  refreshing: boolean;
};

export function TopBar({
  meta,
  metaErr,
  runtime,
  setRuntime,
  theme,
  onToggleTheme,
  onRefresh,
  refreshing,
}: Props) {
  const pending = meta === null && !metaErr;
  const gpuAvailable = meta?.gpu_available === true;
  const dockerAvailable = meta?.docker_available === true;
  const torchOk = meta?.subprocess_torch_import_ok === true;

  const gpuStatus = !gpuAvailable ? "err" : runtime === "native" && !meta?.gpu_cuda_native ? "warn" : "ok";
  const gpuLabel = !gpuAvailable
    ? "off"
    : meta?.gpu_cuda_native
      ? "CUDA/ROCm (native)"
      : "GPU (Docker)";

  return (
    <header className="topbar console__topbar">
      <div className="topbar__status">
        {metaErr ? (
          <span className="u-muted" style={{ fontSize: 12 }}>
            meta: {metaErr}
          </span>
        ) : (
          <>
            <CapChip label="GPU" value={pending ? "…" : gpuLabel} status={pending ? "none" : gpuStatus} />
            <CapChip
              label="Docker"
              value={pending ? "…" : dockerAvailable ? "ready" : "missing"}
              status={pending ? "none" : dockerAvailable ? "ok" : "err"}
            />
            <CapChip
              label="PyTorch"
              value={pending ? "…" : torchOk ? "ok" : "missing"}
              status={pending ? "none" : torchOk ? "ok" : "err"}
            />
            <div className="topbar__divider" />
            <CapChip label="API" value="127.0.0.1:8765" status="ok" />
          </>
        )}
      </div>
      <div className="topbar__actions">
        <div className="runtime-switch" role="group" aria-label="Runtime">
          <button
            type="button"
            className={`runtime-switch__btn${runtime === "native" ? " runtime-switch__btn--on" : ""}`}
            onClick={() => setRuntime("native")}
          >
            Native
          </button>
          <button
            type="button"
            className={`runtime-switch__btn${runtime === "docker" ? " runtime-switch__btn--on" : ""}`}
            onClick={() => setRuntime("docker")}
            disabled={pending || !dockerAvailable}
            title={dockerAvailable ? "Run inside video-watcher-docker" : "Docker not detected"}
          >
            Docker
          </button>
        </div>
        <button
          type="button"
          className="icon-btn"
          title="Refresh capabilities"
          aria-label="Refresh capabilities"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <Icons.Refresh size={15} stroke={1.6} />
        </button>
        <button
          type="button"
          className="icon-btn"
          title={theme === "dark" ? "Light theme" : "Dark theme"}
          onClick={onToggleTheme}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Icons.Sun size={15} stroke={1.6} /> : <Icons.Moon size={15} stroke={1.6} />}
        </button>
      </div>
    </header>
  );
}
