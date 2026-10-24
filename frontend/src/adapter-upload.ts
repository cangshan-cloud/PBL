export type AdapterPreviewIdentity = { source_sha256: string };

const SHA256 = /^[0-9a-f]{64}$/;

export function prepareAdapterImportBody(body: FormData, preview: AdapterPreviewIdentity | null, previewInvalidated = false): FormData {
  body.delete("expected_source_sha256");
  if (body.get("normalize_cn_csv") !== "true") return body;
  if (previewInvalidated) throw new Error("文件已更换，请重新预览后再适配导入");
  if (!preview) return body;
  if (!SHA256.test(preview.source_sha256)) {
    throw new Error("适配预览缺少有效的原文件 SHA-256，请重新预览");
  }
  body.set("expected_source_sha256", preview.source_sha256);
  return body;
}
