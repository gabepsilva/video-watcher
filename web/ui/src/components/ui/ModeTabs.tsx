import type { ReactNode } from "react";

export type ComposerMode = "file" | "youtube";

type Tab = { id: ComposerMode; label: ReactNode };

type Props = {
  mode: ComposerMode;
  onMode: (m: ComposerMode) => void;
  tabs: Tab[];
};

export function ModeTabs({ mode, onMode, tabs }: Props) {
  return (
    <div className="mode-tabs" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          role="tab"
          className={`mode-tab${mode === t.id ? " mode-tab--on" : ""}`}
          onClick={() => onMode(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
