import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { MarkdownPreviewPage } from "./views/MarkdownPreviewPage";
import "./styles/index.scss";

const el = document.getElementById("root");
if (!el) {
  throw new Error("missing #root");
}

const isMarkdownPreview =
  window.location.pathname === "/preview" || window.location.pathname.endsWith("/preview");

createRoot(el).render(
  <StrictMode>{isMarkdownPreview ? <MarkdownPreviewPage /> : <App />}</StrictMode>,
);
