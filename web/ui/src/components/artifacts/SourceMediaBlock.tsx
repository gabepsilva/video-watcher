import type { SourceMedia } from "../../api";
import { isAudioFile, isVideoFile } from "../../lib/artifactMedia";
import { mediaUrl } from "../../lib/mediaUrl";
import { Icons } from "../../icons/Icons";
import { MediaPlayer } from "./MediaPlayer";

type Props = {
  media: SourceMedia;
};

export function SourceMediaBlock({ media }: Props) {
  const video = isVideoFile(media.name);
  const audio = isAudioFile(media.name);

  return (
    <div className="artifact-panel artifact-panel--source">
      <div className="artifact-row artifact-row--header">
        <div className="artifact-row__fmt" data-fmt={video ? "mp4" : audio ? "wav" : "src"}>
          src
        </div>
        <div className="artifact-row__name">Source upload · {media.name}</div>
        <a className="btn btn--sm" href={mediaUrl(media.url, { download: true })} download={media.name}>
          <Icons.Download size={13} />
          Download
        </a>
      </div>
      <div className="artifact-panel__body">
        {video ? <MediaPlayer url={media.url} name={media.name} kind="video" /> : null}
        {audio ? <MediaPlayer url={media.url} name={media.name} kind="audio" /> : null}
        {!video && !audio ? (
          <p className="artifact-panel__hint u-muted">
            Preview not available for this format. Use download.
          </p>
        ) : null}
      </div>
    </div>
  );
}
