import mermaid from "mermaid";

import type { Theme } from "../hooks/useTheme";

let configured: Theme | null = null;

export function configureMermaid(theme: Theme): void {
  if (configured === theme) {
    return;
  }
  mermaid.initialize({
    startOnLoad: false,
    theme: theme === "dark" ? "dark" : "default",
    securityLevel: "strict",
    fontFamily: "var(--font-sans)",
  });
  configured = theme;
}
