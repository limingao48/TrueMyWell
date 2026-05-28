import {
  INDICATOR_TREE,
  LEVEL1_ORDER,
  BUCKLING_OPTIONS,
  getDefaultWeights
} from './config'
import {
  mapValueToScore,
  level1ScoreFromChildren,
  toScore100,
  buildFuzzyMatrix,
  compositeMembership,
  resolveFinalGrade,
  indicatorMembershipVector
} from './fuzzy'
import { resolveIndicatorRawValue } from './indicatorComputed'

function valueInNumericRange (field, n) {
  if (!Number.isFinite(n)) return false
  const lo = field.min != null ? Number(field.min) : -Infinity
  if (field.minExclusive) {
    if (n <= lo) return false
  } else if (n < lo) {
    return false
  }
  if (field.max != null && Number.isFinite(Number(field.max)) && n > Number(field.max)) {
    return false
  }
  return true
}

function numericRangeHint (field) {
  const unit = field.unit ? ` ${field.unit}` : ''
  if (field.minExclusive) {
    const lo = field.min != null ? field.min : 0
    if (field.max != null && Number.isFinite(Number(field.max))) {
      return `须在 (${lo}, ${field.max}]${unit} 范围内`
    }
    return `须大于 ${lo}${unit}`
  }
  if (field.min != null && field.max != null && Number.isFinite(Number(field.max))) {
    return `须在 ${field.min}~${field.max}${unit} 范围内`
  }
  if (field.min != null) {
    return `须 ≥ ${field.min}${unit}`
  }
  return '须为有效数值'
}

/**
 * 校验单指标输入
 * @param {Object} field
 * @param {*} value - 普通指标取值；ratioSum 时可省略，改传 groupValues
 * @param {Object} [groupValues] - 同一一级下的 formValues 片段
 */
export function validateIndicatorInput (field, value, groupValues = null) {
  if (field.inputType === 'select') {
    return value ? null : `请选择${field.label}`
  }

  if (field.inputType === 'ratioSum' || field.inputType === 'derivedFormula') {
    const gv = groupValues || {}
    const parts = field.inputType === 'ratioSum'
      ? (field.sumInputs || [])
      : (field.formulaInputs || [])
    for (const s of parts) {
      const n = Number(gv[s.key])
      if (!Number.isFinite(n)) return `请填写${s.label}`
      if (n < s.min || n > s.max) {
        return `${s.label} 须在 ${s.min}~${s.max} ${s.unit || ''} 范围内`
      }
    }
    const computed = resolveIndicatorRawValue(field, gv)
    if (!Number.isFinite(computed)) {
      return field.inputType === 'ratioSum'
        ? `${field.label}：参考值须大于 0`
        : `${field.label} 计算无效，请检查分项取值`
    }
    if (!valueInNumericRange(field, computed)) {
      return `${field.label} = ${computed.toFixed(4)}，${numericRangeHint(field)}`
    }
    return null
  }

  const n = Number(value)
  if (!Number.isFinite(n)) return `${field.label} 须为有效数值`
  if (field.key === 'R' && n > 0 && n <= 1) {
    return `${field.label} 请按百分比填写 0~100（8% 填 8，勿填 0.08）；若表示 ${(n * 100).toFixed(0)}% 请填 ${n * 100}`
  }
  if (!valueInNumericRange(field, n)) {
    return `${field.label} ${numericRangeHint(field)}`
  }
  return null
}

/**
 * 全流程评价
 * @param {Object} formValues - { stability: { dMW, R }, ... }
 * @param {{ level1: Object, level2: Object }} weights
 */
export function runTrajectoryEvaluation (formValues, weights) {
  const w1 = weights.level1
  const w2 = weights.level2
  const level1WeightsArr = LEVEL1_ORDER.map(k => Number(w1[k]) || 0)

  const secondaryResults = []
  const level1Results = []
  const level1Scores100 = []

  INDICATOR_TREE.forEach(group => {
    const groupKey = group.key
    const vals = formValues[groupKey] || {}
    const childScores = {}
    const childDetails = []

    group.children.forEach(field => {
      const raw = resolveIndicatorRawValue(field, vals)
      const err = validateIndicatorInput(field, raw, vals)
      const score10 = err ? NaN : mapValueToScore(field, raw, BUCKLING_OPTIONS)
      childScores[field.key] = score10
      const rawDisplay = (field.inputType === 'ratioSum' || field.inputType === 'derivedFormula') && Number.isFinite(raw)
        ? Number(raw.toFixed(4))
        : raw
      childDetails.push({
        groupKey,
        groupTitle: group.title,
        key: field.key,
        label: field.label,
        unit: field.unit,
        rawValue: rawDisplay,
        score10,
        error: err
      })
      secondaryResults.push(childDetails[childDetails.length - 1])
    })

    const hasError = childDetails.some(c => c.error || !Number.isFinite(c.score10))
    const score10 = hasError ? NaN : level1ScoreFromChildren(childScores, w2[groupKey] || {})
    const score100 = toScore100(score10)
    const membership = Number.isFinite(score100)
      ? indicatorMembershipVector(score100)
      : [0, 0, 0]

    level1Results.push({
      key: groupKey,
      title: group.title,
      weight: Number(w1[groupKey]) || 0,
      score10,
      score100,
      membership,
      membershipLabels: ['优秀', '合格', '不合格'],
      children: childDetails,
      hasError
    })
    level1Scores100.push(score100)
  })

  const matrixR = buildFuzzyMatrix(level1Scores100.map(s => (Number.isFinite(s) ? s : 0)))
  const composite = compositeMembership(level1WeightsArr, matrixR)
  const final = resolveFinalGrade(composite)

  return {
    secondaryResults,
    level1Results,
    matrixR,
    compositeMembership: {
      excellent: composite[0],
      qualified: composite[1],
      unqualified: composite[2],
      vector: composite
    },
    finalGrade: final.grade,
    finalGradeDetail: final
  }
}

export { getDefaultWeights, INDICATOR_TREE, LEVEL1_ORDER, BUCKLING_OPTIONS }
