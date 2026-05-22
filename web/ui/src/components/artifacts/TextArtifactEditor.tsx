import { useCallback, useEffect, useState } from "react";
import { fetchArtifactText, saveArtifactText } from "../../api";
import { isMarkdownFile, textPreviewLabel } from "../../lib/artifactMedia";
import { openMarkdownPreviewTab } from "../../lib/markdownPreviewTab";
import { MarkdownArtifactView } from "./MarkdownArtifactView";
import { Button } from "../ui/Button";

const MAX_EDIT_CHARS = 5 * 1024 * 1024;

type Props = {
  jobId: string;
  name: string;
  url: string;
  editable: boolean;
  expanded: boolean;
};

export function TextArtifactEditor({ jobId, name, url, editable, expanded }: Props) {
  const [content, setContent] = useState("");
  const [saved, setSaved] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const markdown = isMarkdownFile(name);
  const label = textPreviewLabel(name);

  const loadText = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const text = await fetchArtifactText(url);
      if (text.length > MAX_EDIT_CHARS) {
        throw new Error("File is too large to preview in the browser (max 5 MB).");
      }
      setContent(text);
      setSaved(text);
      setLoaded(true);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    if (!expanded) {
      setLoaded(false);
      setContent("");
      setSaved("");
      setErr(null);
      return;
    }
    if (!loaded && !loading) {
      void loadText();
    }
  }, [expanded, loaded, loading, loadText]);

  const dirty = editable && content !== saved;

  async function onSave() {
    setSaving(true);
    setErr(null);
    try {
      await saveArtifactText(jobId, name, content);
      setSaved(content);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setSaving(false);
    }
  }

  if (!expanded) {
    return null;
  }

  return (
    <>
      <label className="artifact-editor__label" htmlFor={`preview-${name}`}>
        {label} {editable ? "editor" : "preview"}
      </label>
      {loading ? <p className="artifact-panel__hint u-muted">Loading…</p> : null}
      {err ? <p className="alert">{err}</p> : null}
      {!loading && !err && markdown ? (
        <MarkdownArtifactView
          id={`preview-${name}`}
          content={content}
          editable={editable}
          onChange={editable ? setContent : undefined}
        />
      ) : null}
      {!loading && !err && !markdown ? (
        <textarea
          id={`preview-${name}`}
          className="artifact-editor"
          value={content}
          readOnly={!editable}
          onChange={(e) => editable && setContent(e.target.value)}
          spellCheck={false}
        />
      ) : null}
      {markdown && !loading && !err ? (
        <div className="artifact-editor__actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openMarkdownPreviewTab(content, name)}
          >
            Open rendered view
          </Button>
          {editable ? (
            <>
              <Button
                variant="primary"
                size="sm"
                disabled={saving || !dirty}
                onClick={() => void onSave()}
              >
                {saving ? "Saving…" : "Save"}
              </Button>
              {dirty ? (
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={saving}
                  onClick={() => {
                    setContent(saved);
                    setErr(null);
                  }}
                >
                  Revert
                </Button>
              ) : null}
              <span className="artifact-panel__hint u-muted">
                {dirty ? "Unsaved changes" : "Saved"}
              </span>
            </>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
