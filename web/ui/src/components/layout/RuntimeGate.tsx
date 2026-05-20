import type { ReactNode } from "react";
import type { ApiMeta } from "../../api";
import { Callout } from "../ui/Callout";

type Props = {
  meta: ApiMeta | null;
  metaErr: string | null;
  children: ReactNode;
};

/** Blocks the console when the API is not running in the Compose container stack. */
export function RuntimeGate({ meta, metaErr, children }: Props) {
  if (metaErr) {
    return (
      <div className="page">
        <Callout variant="err" title="API unreachable">
          {metaErr}
        </Callout>
      </div>
    );
  }

  if (meta && meta.container_runtime !== true) {
    return (
      <div className="page">
        <Callout variant="err" title="Docker Compose required">
          This console runs only in containers. From the repository root run{" "}
          <code className="u-mono">docker compose up --build</code>, then open{" "}
          <code className="u-mono">http://127.0.0.1:8080</code>.
        </Callout>
      </div>
    );
  }

  if (meta && meta.subprocess_torch_import_ok === false) {
    return (
      <div className="page">
        <Callout variant="err" title="Whisper not ready">
          PyTorch/Whisper is missing in the API container. Rebuild with{" "}
          <code className="u-mono">docker compose build --no-cache api</code>.
        </Callout>
      </div>
    );
  }

  return children;
}
