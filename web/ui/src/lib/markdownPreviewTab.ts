const STORAGE_PREFIX = "vw-md-preview:";
const PREVIEW_REQUEST = "vw-md-preview-request";
const PREVIEW_DATA = "vw-md-preview-data";

export type MarkdownPreviewPayload = {
  content: string;
  title?: string;
};

function storageKey(key: string): string {
  return `${STORAGE_PREFIX}${key}`;
}

function savePreviewPayload(key: string, payload: MarkdownPreviewPayload): void {
  const raw = JSON.stringify(payload);
  sessionStorage.setItem(storageKey(key), raw);
}

/** Read without removing (StrictMode remount + tab refresh). */
export function peekMarkdownPreviewPayload(key: string): MarkdownPreviewPayload | null {
  const raw = sessionStorage.getItem(storageKey(key));
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as MarkdownPreviewPayload;
    if (typeof parsed.content !== "string") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function listenForPreviewRequests(
  key: string,
  payload: MarkdownPreviewPayload,
): () => void {
  const origin = window.location.origin;
  const onMessage = (event: MessageEvent) => {
    if (event.origin !== origin) {
      return;
    }
    if (event.data?.type !== PREVIEW_REQUEST || event.data.key !== key) {
      return;
    }
    const source = event.source;
    if (source && "postMessage" in source) {
      (source as Window).postMessage({ type: PREVIEW_DATA, key, payload }, origin);
    }
  };
  window.addEventListener("message", onMessage);
  const stop = window.setTimeout(() => window.removeEventListener("message", onMessage), 60_000);
  return () => {
    window.clearTimeout(stop);
    window.removeEventListener("message", onMessage);
  };
}

/** Open rendered markdown in a new tab (no console chrome). */
export function openMarkdownPreviewTab(content: string, title?: string): void {
  const key = crypto.randomUUID();
  const payload: MarkdownPreviewPayload = { content, title };
  savePreviewPayload(key, payload);

  const stopListening = listenForPreviewRequests(key, payload);

  const url = new URL("/preview", window.location.origin);
  url.searchParams.set("k", key);
  // Do not use noopener — preview tab requests payload via window.opener.postMessage.
  const child = window.open(url.toString(), "_blank");
  if (!child) {
    stopListening();
  }
}

export function requestMarkdownPreviewFromOpener(
  key: string,
  onPayload: (payload: MarkdownPreviewPayload) => void,
  onMissing: () => void,
): () => void {
  const origin = window.location.origin;
  let settled = false;

  const deliver = (payload: MarkdownPreviewPayload) => {
    if (settled) {
      return;
    }
    settled = true;
    onPayload(payload);
  };

  const onMessage = (event: MessageEvent) => {
    if (event.origin !== origin) {
      return;
    }
    if (event.data?.type !== PREVIEW_DATA || event.data.key !== key) {
      return;
    }
    const payload = event.data.payload as MarkdownPreviewPayload;
    if (typeof payload?.content === "string") {
      deliver(payload);
    }
  };

  window.addEventListener("message", onMessage);

  if (window.opener && !window.opener.closed) {
    window.opener.postMessage({ type: PREVIEW_REQUEST, key }, origin);
  }

  const storageTimer = window.setTimeout(() => {
    const payload = peekMarkdownPreviewPayload(key);
    if (payload) {
      deliver(payload);
    }
  }, 300);

  const giveUpTimer = window.setTimeout(() => {
    if (settled) {
      return;
    }
    settled = true;
    onMissing();
  }, 1200);

  return () => {
    window.clearTimeout(storageTimer);
    window.clearTimeout(giveUpTimer);
    window.removeEventListener("message", onMessage);
  };
}

/** Fetch saved artifact markdown when preview is opened with ?job=&file= only. */
export async function fetchJobArtifactMarkdown(jobId: string, name: string): Promise<string> {
  const url = `/api/jobs/${encodeURIComponent(jobId)}/files/${encodeURIComponent(name)}`;
  const r = await fetch(url);
  if (!r.ok) {
    throw new Error(`GET ${url} failed: ${r.status}`);
  }
  return r.text();
}
