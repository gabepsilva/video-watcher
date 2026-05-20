import { useState } from "react";
import { mediaUrl } from "../../lib/mediaUrl";

type Props = {
  url: string;
  name: string;
  kind: "video" | "audio";
};

export function MediaPlayer({ url, name, kind }: Props) {
  const [err, setErr] = useState(false);
  const src = mediaUrl(url);

  if (err) {
    return (
      <p className="artifact-panel__hint u-muted">
        In-browser preview failed for <strong>{name}</strong> (codec or format may be unsupported, e.g. MKV).
        Use Download to play locally.
      </p>
    );
  }

  if (kind === "video") {
    return (
      <video
        className="artifact-panel__video"
        src={src}
        controls
        preload="metadata"
        playsInline
        onError={() => setErr(true)}
      />
    );
  }

  return (
    <audio
      className="artifact-panel__audio"
      src={src}
      controls
      preload="metadata"
      onError={() => setErr(true)}
    />
  );
}
