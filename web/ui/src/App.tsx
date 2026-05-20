import { useEffect, useState } from "react";
import type { ApiMeta } from "./api";
import { getMeta } from "./api";
import { FileJobSection } from "./FileJobSection";
import { JobMonitor } from "./JobMonitor";
import { MicSection } from "./MicSection";
import { YoutubeJobSection } from "./YoutubeJobSection";

export function App() {
  const [meta, setMeta] = useState<ApiMeta | null>(null);
  const [metaErr, setMetaErr] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [useDocker, setUseDocker] = useState(false);

  function loadMeta() {
    setMetaErr(null);
    void getMeta()
      .then(setMeta)
      .catch((e: unknown) => setMetaErr(e instanceof Error ? e.message : String(e)));
  }

  useEffect(() => {
    loadMeta();
  }, []);

  const metaPending = meta === null && !metaErr;
  const dockerAvailable = meta?.docker_available === true;
  const gpuAvailable = meta?.gpu_available === true;

  return (
    <div className="layout">
      <header>
        <h1>video-watcher</h1>
        <p>
          Local web console for file transcription, YouTube, and browser microphone phrases. API binds to{" "}
          <code>127.0.0.1:8765</code> by default; this UI proxies <code>/api</code> in dev.
        </p>
        {metaErr ? <p className="error">Could not load /api/meta: {metaErr}</p> : null}
        {meta ? (
          <p className="muted small capabilities">
            Capabilities:{" "}
            <span className={gpuAvailable ? "cap-ok" : "cap-no"}>GPU {gpuAvailable ? "yes" : "no"}</span>
            {" · "}
            <span className={dockerAvailable ? "cap-ok" : "cap-no"}>
              Docker {dockerAvailable ? "yes" : "no"}
            </span>
            {" · "}
            <span>PyTorch {meta.subprocess_torch_import_ok ? "ok" : "missing"}</span>
            <button type="button" className="linkish" onClick={loadMeta}>
              Refresh
            </button>
          </p>
        ) : null}
        {meta && meta.subprocess_torch_import_ok === false ? (
          <p className="error">
            Native jobs need PyTorch in <code>{meta.subprocess_python}</code>. Run <code>./install-local</code>, use{" "}
            <code>./video-watcher-web</code>, or enable <strong>Run jobs in Docker</strong> below.
          </p>
        ) : null}
        <div className="panel panel-runtime">
          <label className={`check-inline${metaPending || !dockerAvailable ? " muted" : ""}`}>
            <input
              type="checkbox"
              checked={useDocker}
              disabled={metaPending || !dockerAvailable}
              onChange={(e) => setUseDocker(e.target.checked)}
            />
            Run file / YouTube jobs in Docker
            {metaPending
              ? " (checking…)"
              : !dockerAvailable
                ? " (docker/podman not available)"
                : ""}
          </label>
          {useDocker ? (
            <p className="muted small">
              Uses <code>video-watcher-docker</code> on the API host (GPU image when detected). First run may build the
              image.
            </p>
          ) : null}
        </div>
      </header>

      <FileJobSection meta={meta} useDocker={useDocker} onJobStarted={setJobId} />
      <YoutubeJobSection meta={meta} useDocker={useDocker} onJobStarted={setJobId} />
      <MicSection meta={meta} />
      <JobMonitor jobId={jobId} />
    </div>
  );
}
