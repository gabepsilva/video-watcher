import { useRef, useState } from "react";
import { Icons } from "../../icons/Icons";
import { Button } from "./Button";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

type Props = {
  file: File | null;
  onFile: (f: File | null) => void;
};

export function Dropzone({ file, onFile }: Props) {
  const inp = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  if (file) {
    return (
      <div className="dropzone dropzone--has-file">
        <div className="file-pill">
          <div className="file-pill__thumb">
            <Icons.File size={18} stroke={1.5} />
          </div>
          <div className="file-pill__meta">
            <div className="file-pill__name">{file.name}</div>
            <div className="file-pill__stats">
              {file.type || "media"} · {formatBytes(file.size)}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onFile(null)}>
            Change
          </Button>
        </div>
      </div>
    );
  }

  const pick = (f: File | undefined) => {
    if (f) onFile(f);
  };

  return (
    <div
      className={`dropzone${drag ? " dropzone--drag" : ""}`}
      role="button"
      tabIndex={0}
      onClick={() => inp.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && inp.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        pick(e.dataTransfer.files[0]);
      }}
    >
      <input
        ref={inp}
        type="file"
        hidden
        accept="audio/*,video/*"
        onChange={(e) => pick(e.target.files?.[0])}
      />
      <Icons.Upload size={28} />
      <div className="dropzone__title">Drop a media file here</div>
      <div className="dropzone__sub">
        or <span className="dropzone__browse">browse</span> · mp4, mkv, mp3, wav, m4a — anything ffmpeg can decode
      </div>
    </div>
  );
}
