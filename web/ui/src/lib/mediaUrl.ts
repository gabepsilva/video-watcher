/** API media URLs: inline for players, ``?download=1`` for save-to-disk links. */

export function mediaUrl(url: string, opts?: { download?: boolean }): string {
  if (!opts?.download) {
    return url;
  }
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}download=1`;
}
