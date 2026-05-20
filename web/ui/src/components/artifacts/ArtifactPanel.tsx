import type { JobArtifact } from "../../api";
import { extOf, isAudioFile, isTextFile, isVideoFile } from "../../lib/artifactMedia";
import { mediaUrl } from "../../lib/mediaUrl";
import { Icons } from "../../icons/Icons";
import { MediaPlayer } from "./MediaPlayer";
import { TextArtifactEditor } from "./TextArtifactEditor";

type Props = {
  jobId: string;
  artifact: JobArtifact;
  expanded: boolean;
  onToggle: () => void;
};

export function ArtifactPanel({ jobId, artifact, expanded, onToggle }: Props) {
  const ext = extOf(artifact.name);
  const video = isVideoFile(artifact.name);
  const audio = isAudioFile(artifact.name);
  const text = isTextFile(artifact.name);
  const showFallback = expanded && !video && !audio && !text;

  return (
    <div className={`artifact-panel${expanded ? " artifact-panel--open" : ""}`}>
      <div className="artifact-row artifact-row--header">
        <button type="button" className="artifact-row__toggle" onClick={onToggle} aria-expanded={expanded}>
          <Icons.Chev
            size={14}
            stroke={1.8}
            className={`artifact-row__chev${expanded ? " artifact-row__chev--open" : ""}`}
          />
        </button>
        <div className="artifact-row__fmt" data-fmt={ext}>
          {ext || "file"}
        </div>
        <div className="artifact-row__name">{artifact.name}</div>
        <a className="btn btn--sm" href={mediaUrl(artifact.url, { download: true })} download={artifact.name}>
          <Icons.Download size={13} />
          Download
        </a>
      </div>

      {expanded ? (
        <div className="artifact-panel__body">
          {video ? <MediaPlayer url={artifact.url} name={artifact.name} kind="video" /> : null}
          {audio ? <MediaPlayer url={artifact.url} name={artifact.name} kind="audio" /> : null}
          {text ? (
            <TextArtifactEditor
              jobId={jobId}
              name={artifact.name}
              url={artifact.url}
              editable={artifact.editable}
              expanded={expanded}
            />
          ) : null}
          {showFallback ? (
            <p className="artifact-panel__hint u-muted">
              No in-browser preview for this format. Download to open locally.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
