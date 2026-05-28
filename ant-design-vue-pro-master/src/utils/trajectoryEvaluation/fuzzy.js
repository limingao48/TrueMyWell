/**
 * 模糊隶属度函数与综合评判（严格按评价细则 PPT 公式）
 * 输入得分 x 为 0~100 分制
 */

const SCORES = [10, 8, 6, 4, 2]

/** 优良隶属度 i1(x) */
export function membershipExcellent (x) {
  if (x <= 80) return 0
  if (x <= 90) return 1 / (1 + 11.11 * Math.pow(x - 80, 2))
  if (x <= 100) return x / 100
  return 0
}

/** 合格隶属度 i2(x) */
export function membershipQualified (x) {
  return 1 / (1 + 0.04 * Math.pow(x - 75, 2))
}

/** 不合格隶属度 i3(x) */
export function membershipUnqualified (x) {
  if (x <= 60) return 1
  if (x <= 90) return 1 / (1 + 0.01 * Math.pow(x - 60, 2))
  if (x <= 100) return 1 - x / 100
  return 0
}

/** 单指标三个等级隶属度 */
export function indicatorMembershipVector (score100) {
  const x = Math.max(0, Math.min(100, Number(score100) || 0))
  return [
    membershipExcellent(x),
    membershipQualified(x),
    membershipUnqualified(x)
  ]
}

/**
 * 构建 6×3 模糊矩阵 R
 * @param {number[]} level1Scores100 - 六个一级指标 0~100 分
 */
export function buildFuzzyMatrix (level1Scores100) {
  return level1Scores100.map(s => indicatorMembershipVector(s))
}

/**
 * 综合隶属度 B = W × R
 * @param {number[]} weights - 长度 6，一级权重
 * @param {number[][]} matrixR - 6×3
 * @returns {number[]} [优秀, 合格, 不合格]
 */
export function compositeMembership (weights, matrixR) {
  const b = [0, 0, 0]
  for (let i = 0; i < 6; i++) {
    const w = Number(weights[i]) || 0
    const row = matrixR[i] || [0, 0, 0]
    for (let j = 0; j < 3; j++) {
      b[j] += w * row[j]
    }
  }
  return b
}

export function resolveFinalGrade (membershipVector) {
  const labels = ['优秀', '合格', '不合格']
  let maxIdx = 0
  let maxVal = membershipVector[0]
  for (let j = 1; j < 3; j++) {
    if (membershipVector[j] > maxVal) {
      maxVal = membershipVector[j]
      maxIdx = j
    }
  }
  return { grade: labels[maxIdx], index: maxIdx, value: maxVal }
}

function clampScore (s) {
  return Math.max(0, Math.min(10, s))
}

function roundScore (s) {
  return Math.round(s * 100) / 100
}

/**
 * 按阈值锚点线性插值（段内渐变；段外沿端点切线外推后限制在 0~10）
 * @param {number} v
 * @param {{ x: number, score: number }[]} breakpoints 按 x 升序
 */
export function interpolateScoreFromBreakpoints (v, breakpoints) {
  if (!Number.isFinite(v) || !breakpoints || !breakpoints.length) return NaN
  const pts = [...breakpoints].sort((a, b) => a.x - b.x)
  const n = pts.length

  if (v <= pts[0].x) {
    if (n === 1) return clampScore(pts[0].score)
    const dx = pts[1].x - pts[0].x
    if (Math.abs(dx) < 1e-12) return clampScore(pts[0].score)
    const slope = (pts[1].score - pts[0].score) / dx
    return clampScore(pts[0].score + slope * (v - pts[0].x))
  }

  for (let i = 0; i < n - 1; i++) {
    const a = pts[i]
    const b = pts[i + 1]
    if (v <= b.x) {
      const dx = b.x - a.x
      if (Math.abs(dx) < 1e-12) return clampScore(b.score)
      const t = (v - a.x) / dx
      return clampScore(a.score + t * (b.score - a.score))
    }
  }

  const a = pts[n - 2]
  const b = pts[n - 1]
  const dx = b.x - a.x
  if (Math.abs(dx) < 1e-12) return clampScore(b.score)
  const slope = (b.score - a.score) / dx
  return clampScore(b.score + slope * (v - b.x))
}

/** 由 scoreMode、thresholds、scoreAnchors 生成插值锚点 */
export function buildScoreBreakpoints (field) {
  if (field.scoreBreakpoints && field.scoreBreakpoints.length) {
    return field.scoreBreakpoints
  }
  const anchors = field.scoreAnchors || SCORES
  const [t10, t8, t6, t4] = field.thresholds || []
  if (field.scoreMode === 'higher') {
    const pts = [
      { x: t4, score: anchors[3] != null ? anchors[3] : SCORES[3] },
      { x: t6, score: anchors[2] != null ? anchors[2] : SCORES[2] },
      { x: t8, score: anchors[1] != null ? anchors[1] : SCORES[1] },
      { x: t10, score: anchors[0] != null ? anchors[0] : SCORES[0] }
    ]
    if (field.worstAnchor) pts.unshift(field.worstAnchor)
    return pts
  }
  if (field.scoreMode === 'lower' || field.scoreMode === 'optimal') {
    const pts = [
      { x: t10, score: anchors[0] != null ? anchors[0] : SCORES[0] },
      { x: t8, score: anchors[1] != null ? anchors[1] : SCORES[1] },
      { x: t6, score: anchors[2] != null ? anchors[2] : SCORES[2] },
      { x: t4, score: anchors[3] != null ? anchors[3] : SCORES[3] }
    ]
    if (field.worstAnchor) pts.push(field.worstAnchor)
    return pts
  }
  return []
}

/**
 * 二级指标原始值 → 0~10 分（连续渐变；屈曲状态仍为分档固定分）
 */
export function mapValueToScore (field, rawValue, bucklingMap) {
  if (field.scoreMode === 'buckling') {
    const opt = (bucklingMap || []).find(o => o.value === rawValue)
    return opt ? opt.score : 0
  }
  const v = Number(rawValue)
  if (!Number.isFinite(v)) return NaN

  let x = v
  if (field.scoreMode === 'optimal') {
    const ideal = field.optimal != null ? field.optimal : 1
    x = Math.abs(v - ideal)
  } else if (field.scoreMode !== 'higher' && field.scoreMode !== 'lower') {
    return NaN
  }

  const breakpoints = buildScoreBreakpoints(field)
  let score = interpolateScoreFromBreakpoints(x, breakpoints)
  if (!Number.isFinite(score)) return NaN

  const [t10] = field.thresholds || []
  if (field.scoreMode === 'higher' && Number.isFinite(t10) && v >= t10) {
    const floor = (field.scoreAnchors && field.scoreAnchors[0]) != null
      ? field.scoreAnchors[0]
      : SCORES[0]
    score = Math.max(score, floor)
    if (field.bestScore != null) score = Math.min(field.bestScore, score)
  }

  return roundScore(score)
}

export function level1ScoreFromChildren (childScores, childWeights) {
  let sum = 0
  const keys = Object.keys(childWeights)
  keys.forEach(k => {
    const s = childScores[k]
    const w = Number(childWeights[k]) || 0
    if (Number.isFinite(s)) sum += s * w
  })
  return sum
}

export function toScore100 (score10) {
  return Math.max(0, Math.min(100, (Number(score10) || 0) * 10))
}

export function validateWeightSum (weights, tolerance = 0.001) {
  const sum = Object.values(weights).reduce((a, b) => a + (Number(b) || 0), 0)
  return Math.abs(sum - 1) <= tolerance
}
