import { useEffect, useState } from "react";
import type { Theme } from "./useTheme";

/** Reads `data-theme` on `<html>` (keeps Mermaid in sync with the console theme toggle). */
export function useDocumentTheme(): Theme {
  const read = (): Theme =>
    document.documentElement.dataset.theme === "dark" ? "dark" : "light";

  const [theme, setTheme] = useState<Theme>(read);

  useEffect(() => {
    const el = document.documentElement;
    const sync = () => setTheme(read());
    const obs = new MutationObserver(sync);
    obs.observe(el, { attributes: true, attributeFilter: ["data-theme"] });
    sync();
    return () => obs.disconnect();
  }, []);

  return theme;
}
