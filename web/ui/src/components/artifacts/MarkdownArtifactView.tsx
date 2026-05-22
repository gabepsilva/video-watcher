import { MarkdownPreview } from "./MarkdownPreview";

type Props = {
  id: string;
  content: string;
  editable: boolean;
  onChange?: (value: string) => void;
};

/** Markdown source + live preview (no toolbar). Read-only shows preview only. */
export function MarkdownArtifactView({ id, content, editable, onChange }: Props) {
  return (
    <div className={`artifact-md${editable ? "" : " artifact-md--readonly"}`}>
      {editable ? (
        <textarea
          id={id}
          className="artifact-editor artifact-editor--md artifact-md__source"
          value={content}
          onChange={(e) => onChange?.(e.target.value)}
          spellCheck={false}
          aria-label="Markdown source"
        />
      ) : null}
      <div className="artifact-md__preview" aria-live="polite">
        <MarkdownPreview content={content} />
      </div>
    </div>
  );
}
