import type { ApiMeta } from "../../api";
import { Icons } from "../../icons/Icons";
import type { Theme } from "../../hooks/useTheme";
import { CapChip } from "../ui/CapChip";

type Props = {
  meta: ApiMeta | null;
  metaErr: string | null;
  theme: Theme;
  onToggleTheme: () => void;
  onRefresh: () => void;
  refreshing: boolean;
};

export function TopBar({ meta, metaErr, theme, onToggleTheme, onRefresh, refreshing }: Props) {
  const pending = meta === null && !metaErr;
  const containerRuntime = meta?.container_runtime === true;
  const gpuAvailable = meta?.gpu_available === true;

  const gpuStatus = !gpuAvailable ? "err" : "ok";
  const gpuLabel = gpuAvailable ? "on" : "off";

  return (
    <header className="topbar console__topbar">
      <div className="topbar__status">
        {metaErr ? (
          <span className="u-muted" style={{ fontSize: 12 }}>
            meta: {metaErr}
          </span>
        ) : (
          <>
            <CapChip
              label="Runtime"
              value={pending ? "…" : containerRuntime ? "container" : "host"}
              status={pending ? "none" : containerRuntime ? "ok" : "err"}
              title="Compose API container"
            />
            <CapChip label="GPU" value={pending ? "…" : gpuLabel} status={pending ? "none" : gpuStatus} />
            <div className="topbar__divider" />
            <CapChip label="API" value="compose" status="ok" />
          </>
        )}
      </div>
      <div className="topbar__actions">
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
