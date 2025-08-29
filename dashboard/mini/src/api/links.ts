export interface ParsedLinks {
  next?: URL;
  prev?: URL;
}

export function parseLinkHeader(header: string): ParsedLinks {
  const result: ParsedLinks = {};
  if (!header) return result;
  const parts = header.split(',');
  for (const part of parts) {
    const [urlPart, ...rest] = part.split(';');
    if (!urlPart) continue;
    const urlMatch = urlPart.trim().match(/^<([^>]+)>$/);
    if (!urlMatch) continue;
    const urlStr = urlMatch[1];
    let rel: string | undefined;
    for (const seg of rest) {
      const relMatch = seg.trim().match(/^rel="?([^";]+)"?$/);
      if (relMatch) {
        rel = relMatch[1];
        break;
      }
    }
    if (!rel) continue;
    try {
      const url = new URL(urlStr, 'http://localhost');
      if (rel === 'next') result.next = url;
      else if (rel === 'prev') result.prev = url;
    } catch {
      // ignore invalid URLs
    }
  }
  return result;
}
