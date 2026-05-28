/**
 * 由录入分量计算二级指标原始值（比值、加权综合等）
 */
import { computeRatioFromSums } from './ratioIndicators'

/** 比值类：模拟值 / 参考值 */
export function resolveRatioSumValue (field, groupValues) {
  const [sim, ref] = field.sumInputs || []
  if (!sim || !ref) return NaN
  return computeRatioFromSums(groupValues[sim.key], groupValues[ref.key])
}

/**
 * 井眼清洁难度系数 K（水力说明）
 * K = (Q_min / Q_base) × (ΔP / ΔP_base)
 */
export function computeCleaningDifficultyK (groupValues) {
  const gv = groupValues || {}
  const qMin = Number(gv.K_Qmin)
  const dP = Number(gv.K_dP)
  const qBase = Number(gv.K_Qbase)
  const dPbase = Number(gv.K_dPbase)
  if (!Number.isFinite(qMin) || !Number.isFinite(dP) || !Number.isFinite(qBase) || !Number.isFinite(dPbase)) {
    return NaN
  }
  if (qBase <= 0 || dPbase <= 0) return NaN
  const k = (qMin / qBase) * (dP / dPbase)
  return Math.round(k * 10000) / 10000
}

export function resolveDerivedFormulaValue (field, groupValues) {
  if (field.compute === 'cleaningDifficultyK') {
    return computeCleaningDifficultyK(groupValues)
  }
  return NaN
}

/** 统一解析二级指标用于评分的原始值 */
export function resolveIndicatorRawValue (field, groupValues) {
  if (!field) return undefined
  const gv = groupValues || {}

  if (field.inputType === 'ratioSum') {
    return resolveRatioSumValue(field, gv)
  }
  if (field.inputType === 'derivedFormula') {
    return resolveDerivedFormulaValue(field, gv)
  }
  return gv[field.key]
}
