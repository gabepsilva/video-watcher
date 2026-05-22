import { useEffect, useState } from "react";

import { MarkdownPreview } from "../components/artifacts/MarkdownPreview";
import { useTheme } from "../hooks/useTheme";
import {
  fetchJobArtifactMarkdown,
  requestMarkdownPreviewFromOpener,
} from "../lib/markdownPreviewTab";

const MISSING_MSG =
  "Preview expired or missing. Open again from the job artifact editor. " +
  "Use the same host in both tabs (e.g. always 127.0.0.1:5173, not localhost).";

export function MarkdownPreviewPage() {
  useTheme();
  const [content, setContent] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const key = params.get("k");

    if (key) {
      const apply = (payload: { content: string; title?: string }) => {
        setContent(payload.content);
        if (payload.title) {
          document.title = payload.title;
        }
      };

      return requestMarkdownPreviewFromOpener(key, apply, () => setErr(MISSING_MSG));
    }

    const jobId = params.get("job");
    const file = params.get("file");
    if (jobId && file) {
      void fetchJobArtifactMarkdown(jobId, file)
        .then((text) => {
          setContent(text);
          document.title = file;
        })
        .catch((ex: unknown) => {
          setErr(ex instanceof Error ? ex.message : String(ex));
        });
      return;
    }

    setErr("Missing preview parameters.");
  }, []);

  if (err) {
    return (
      <main className="md-preview">
        <p className="md-preview__err">{err}</p>
      </main>
    );
  }

  if (content === null) {
    return (
      <main className="md-preview">
        <p className="md-preview__hint">Loading…</p>
      </main>
    );
  }

  return (
    <main className="md-preview">
      <article className="md-preview__article">
        <MarkdownPreview content={content} />
      </article>
    </main>
  );
}
