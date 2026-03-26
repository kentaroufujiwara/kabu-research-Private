/** 億・兆に変換して表示 */
export function formatJpy(value: number | null | undefined): string {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${(value / 1e12).toFixed(1)}兆円`;
  if (abs >= 1e8) return `${(value / 1e8).toFixed(0)}億円`;
  if (abs >= 1e4) return `${(value / 1e4).toFixed(0)}万円`;
  return `${value.toLocaleString()}円`;
}

/** 株価（小数2桁） */
export function formatPrice(value: number | null | undefined): string {
  if (value == null) return "—";
  return `¥${value.toLocaleString("ja-JP", { minimumFractionDigits: 0, maximumFractionDigits: 1 })}`;
}

/** % 表示 */
export function formatPct(value: number | null | undefined, digits = 1): string {
  if (value == null) return "—";
  return `${value.toFixed(digits)}%`;
}

/** 倍率（PER/PBR など） */
export function formatMultiple(value: number | null | undefined, digits = 1): string {
  if (value == null) return "—";
  return `${value.toFixed(digits)}倍`;
}

/** 万人単位 */
export function formatEmployees(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toLocaleString()}人`;
}
