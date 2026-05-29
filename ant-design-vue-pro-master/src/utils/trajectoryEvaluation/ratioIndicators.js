/**
 * 由模拟值与参考值计算无量纲比值（钩载比 H、扭矩比 T 等）
 */

export function computeRatioFromSums (simulated, reference) {
  const a = Number(simulated)
  const r = Number(reference)
  if (!Number.isFinite(a) || !Number.isFinite(r) || r <= 0) return NaN
  return a / r
}

export { resolveIndicatorRawValue, resolveRatioSumValue } from './indicatorComputed'
