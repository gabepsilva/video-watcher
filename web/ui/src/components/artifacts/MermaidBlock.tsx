import mermaid from "mermaid";
import { useLayoutEffect, useId, useRef, useState } from "react";

import { useDocumentTheme } from "../../hooks/useDocumentTheme";
import { configureMermaid } from "../../lib/mermaidConfig";

type Props = {
  source: string;
};

/** Renders a ```mermaid fenced block as SVG (re-runs when source or theme changes). */
export function MermaidBlock({ source }: Props) {
  const reactId = useId().replace(/:/g, "");
  const containerRef = useRef<HTMLDivElement>(null);
  const theme = useDocumentTheme();
  const [error, setError] = useState<string | null>(null);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) {
      return;
    }

    let cancelled = false;
    configureMermaid(theme);
    setError(null);
    el.innerHTML = "";

    mermaid
      .render(`vw-mmd-${reactId}`, source)
      .then(({ svg }) => {
        if (!cancelled) {
          el.innerHTML = svg;
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [source, theme, reactId]);

  if (error) {
    return (
      <div className="artifact-md__mermaid artifact-md__mermaid--error">
        <p className="artifact-md__mermaid-err">{error}</p>
        <pre>
          <code>{source}</code>
        </pre>
      </div>
    );
  }

  return <div ref={containerRef} className="artifact-md__mermaid" />;
}
