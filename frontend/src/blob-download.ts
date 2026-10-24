type DownloadAnchor = {
  href: string;
  download: string;
  click(): void;
  remove(): void;
};

export type DownloadPort = {
  createAnchor(): DownloadAnchor;
  attach(anchor: DownloadAnchor): void;
  createObjectURL(blob: Blob): string;
  revokeObjectURL(url: string): void;
  defer(callback: () => void, delayMs: number): void;
};

const RELEASE_DELAY_MS = 30_000;

const browserDownloadPort: DownloadPort = {
  createAnchor: () => document.createElement("a"),
  attach: anchor => document.body.append(anchor as HTMLAnchorElement),
  createObjectURL: blob => URL.createObjectURL(blob),
  revokeObjectURL: url => URL.revokeObjectURL(url),
  defer: (callback, delayMs) => { window.setTimeout(callback, delayMs); },
};

export function saveBlobAsFile(blob: Blob, filename: string, port: DownloadPort = browserDownloadPort): void {
  const anchor = port.createAnchor();
  const url = port.createObjectURL(blob);
  anchor.href = url;
  anchor.download = filename;
  try {
    port.attach(anchor);
    anchor.click();
  } finally {
    anchor.remove();
    port.defer(() => port.revokeObjectURL(url), RELEASE_DELAY_MS);
  }
}
