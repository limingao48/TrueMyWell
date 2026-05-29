/**
 * FAHP 模糊层次分析法（与评价 PPT 六步一致）
 * 1 行模糊求和 → 2 各行和再求和 → 3 总模糊数取倒数 → 4 模糊权重 w̃_i
 * 5 可能度 V(w̃_i≥w̃_j) → 6 min 归一化
 */
import { FUZZY_TRIANGLES_1_9, RI_TABLE } from './fahpConfig'

function triplet (scale) {
  const s = Math.max(1, Math.min(9, Math.round(Number(scale) || 1)))
  return [...FUZZY_TRIANGLES_1_9[s]]
}

function reciprocalTriplet ([l, m, u]) {
  return [1 / u, 1 / m, 1 / l]
}

function fuzzyAdd (a, b) {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
}

function fuzzyMultiply (a, b) {
  return [a[0] * b[0], a[1] * b[1], a[2] * b[2]]
}

/**
 * PPT 第5步：V(w̃_i ≥ w̃_j)
 * m_i≥m_j → 1；u_i<l_j → 0；否则 (u_i-l_j)/((u_i-l_j)+(m_j-m_i))
 */
function possibilityWeightGE (wi, wj) {
  const [, mi, ui] = wi
  const [lj, mj] = wj
  if (mi >= mj) return 1
  if (ui < lj) return 0
  const num = ui - lj
  const denom = num + (mj - mi)
  if (denom <= 1e-12) return 0
  return Math.max(0, Math.min(1, num / denom))
}

/** 第1~4步：行和 S̃_i、总 S̃_total、模糊权重 w̃_i = S̃_i ⊗ S̃_total^{-1} */
function computeFuzzyWeights (fuzzyMatrix) {
  const rowSums = fuzzyMatrix.map(row =>
    row.reduce((sum, cell) => fuzzyAdd(sum, cell), [0, 0, 0])
  )
  const sTotal = rowSums.reduce((sum, s) => fuzzyAdd(sum, s), [0, 0, 0])
  const sTotalInv = reciprocalTriplet(sTotal)
  const fuzzyWeights = rowSums.map(s => fuzzyMultiply(s, sTotalInv))
  return { rowSums, sTotal, sTotalInv, fuzzyWeights }
}

/** 三角模糊数质心（去模糊，用于可能度失效时的兜底） */
function fuzzyCentroid ([l, m, u]) {
  return (Number(l) + Number(m) + Number(u)) / 3
}

/**
 * 第5~6步：由模糊权重算归一化权重
 * 若某指标相对其它指标的可能度全为 0（模糊数不重叠），改用质心权重，避免算出 0
 */
function weightsFromFuzzyWeights (fuzzyWeights) {
  const n = fuzzyWeights.length
  const centroids = fuzzyWeights.map(fuzzyCentroid)

  const dPrime = fuzzyWeights.map((wi, i) => {
    let minV = 1
    for (let j = 0; j < n; j++) {
      if (i === j) continue
      minV = Math.min(minV, possibilityWeightGE(wi, fuzzyWeights[j]))
    }
    return minV
  })

  const sumD = dPrime.reduce((a, b) => a + b, 0)
  const hasZero = dPrime.some(d => d <= 1e-12)

  if (sumD > 1e-12 && !hasZero) {
    return dPrime.map(d => d / sumD)
  }

  const sumC = centroids.reduce((a, b) => a + b, 0)
  return centroids.map(c => (sumC > 0 ? c / sumC : 1 / n))
}

/**
 * 按指标在 criteriaKeys 中的顺序生成存储键（仅 i<j）：存 a_ij = 指标 i 相对 j 的重要性
 */
export function pairMatrixStorageKey (criteriaKeys, keyA, keyB) {
  const ia = criteriaKeys.indexOf(keyA)
  const ib = criteriaKeys.indexOf(keyB)
  if (ia < 0 || ib < 0 || ia === ib) return null
  return ia < ib ? `${keyA}_${keyB}` : `${keyB}_${keyA}`
}

/** 初始化上三角（按指标顺序，默认 1） */
export function createEmptyPairMatrix (criteriaKeys) {
  const keys = [...criteriaKeys]
  const matrix = {}
  for (let i = 0; i < keys.length; i++) {
    for (let j = i + 1; j < keys.length; j++) {
      matrix[`${keys[i]}_${keys[j]}`] = 1
    }
  }
  return matrix
}

/** 标度 k 的倒数（用于 a_ji = 1/a_ij 的显示与 crisp 一致性检验） */
export function reciprocalScaleValue (scale) {
  const s = Number(scale) || 1
  if (s <= 0) return 1
  return 1 / s
}

export function reciprocalScaleLabel (scale) {
  const s = Number(scale) || 1
  if (s === 1) return '1'
  const inv = reciprocalScaleValue(s)
  if (Math.abs(inv - 1) < 1e-6) return '1'
  if (Number.isInteger(s) && s >= 2 && s <= 9) return `1/${s}`
  return inv.toFixed(3)
}

/**
 * 读取「fromKey 相对 toKey」的重要性标度（1~9）
 * 存储约定：键 keys[i]_keys[j]（i<j）存 a_ij
 */
export function getPairImportance (pairMatrix, criteriaKeys, fromKey, toKey) {
  if (fromKey === toKey) return 1
  const ia = criteriaKeys.indexOf(fromKey)
  const ib = criteriaKeys.indexOf(toKey)
  if (ia < 0 || ib < 0) return 1
  const storageKey = ia < ib ? `${fromKey}_${toKey}` : `${toKey}_${fromKey}`
  const stored = pairMatrix[storageKey] != null ? Number(pairMatrix[storageKey]) : 1
  return ia < ib ? stored : reciprocalScaleValue(stored)
}

/** @deprecated 使用 getPairImportance */
export function getUpperPairValue (pairMatrix, criteriaKeys, rowKey, colKey) {
  return getPairImportance(pairMatrix, criteriaKeys, rowKey, colKey)
}

/** 写入 a_row,col（rowKey 在 criteriaKeys 中须排在 colKey 之前） */
export function setPairImportance (pairMatrix, criteriaKeys, rowKey, colKey, scale) {
  const ia = criteriaKeys.indexOf(rowKey)
  const ib = criteriaKeys.indexOf(colKey)
  if (ia < 0 || ib < 0 || ia >= ib) return { ...pairMatrix }
  return { ...pairMatrix, [`${rowKey}_${colKey}`]: scale }
}

/** 读取上三角存储标度（恒为 指标[lo] 相对 指标[hi]，lo<hi） */
export function getStoredUpperScale (pairMatrix, criteriaKeys, rowIdx, colIdx) {
  if (rowIdx === colIdx) return 1
  const lo = Math.min(rowIdx, colIdx)
  const hi = Math.max(rowIdx, colIdx)
  const key = `${criteriaKeys[lo]}_${criteriaKeys[hi]}`
  return pairMatrix[key] != null ? Number(pairMatrix[key]) : 1
}

/**
 * 矩阵单元 a[rowIdx, colIdx]：第 rowIdx 项相对第 colIdx 项的标度（下三角为倒数）
 */
export function getMatrixCellScale (pairMatrix, criteriaKeys, rowIdx, colIdx) {
  if (rowIdx === colIdx) return 1
  const stored = getStoredUpperScale(pairMatrix, criteriaKeys, rowIdx, colIdx)
  return rowIdx < colIdx ? stored : reciprocalScaleValue(stored)
}

/** 下三角展示文案（由上三角 stored 直接取倒数，不再二次换算） */
export function formatLowerCellLabel (storedUpperScale) {
  return reciprocalScaleLabel(storedUpperScale)
}

/** 上三角展示文案 */
export function formatUpperCellLabel (storedUpperScale) {
  const s = Number(storedUpperScale) || 1
  return String(Math.round(s))
}

/** 将旧版乱序键合并为按指标顺序的上三角存储 */
export function normalizePairMatrix (pairMatrix, criteriaKeys) {
  const next = createEmptyPairMatrix(criteriaKeys)
  for (let i = 0; i < criteriaKeys.length; i++) {
    for (let j = i + 1; j < criteriaKeys.length; j++) {
      const kOrdered = `${criteriaKeys[i]}_${criteriaKeys[j]}`
      const kReverse = `${criteriaKeys[j]}_${criteriaKeys[i]}`
      const v = pairMatrix[kOrdered] != null
        ? Number(pairMatrix[kOrdered])
        : (pairMatrix[kReverse] != null ? Number(pairMatrix[kReverse]) : 1)
      next[kOrdered] = v
    }
  }
  return next
}

/** 生成 crisp 判断矩阵（中值），用于预览：A[i][j]=a_ij, A[j][i]=1/A[i][j] */
export function buildCrispMatrixForDisplay (criteriaKeys, pairMatrix) {
  return buildCrispMatrix(criteriaKeys, pairMatrix)
}

function buildFuzzyMatrix (criteriaKeys, pairMatrix) {
  const n = criteriaKeys.length
  const fuzzy = Array(n).fill(null).map(() => Array(n).fill(null))
  for (let i = 0; i < n; i++) {
    fuzzy[i][i] = triplet(1)
  }
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const scale = getStoredUpperScale(pairMatrix, criteriaKeys, i, j)
      fuzzy[i][j] = triplet(scale)
      fuzzy[j][i] = reciprocalTriplet(fuzzy[i][j])
    }
  }
  return fuzzy
}

function buildCrispMatrix (criteriaKeys, pairMatrix) {
  const n = criteriaKeys.length
  const A = Array(n).fill(null).map(() => Array(n).fill(1))
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const m = triplet(getStoredUpperScale(pairMatrix, criteriaKeys, i, j))[1]
      A[i][j] = m
      A[j][i] = m > 0 ? 1 / m : 1
    }
  }
  return A
}

/** 标准 AHP：对去模糊（中值）矩阵做几何平均求权重 */
function computeCrispAhpWeights (criteriaKeys, pairMatrix) {
  const keys = [...criteriaKeys]
  const n = keys.length
  if (n === 0) return {}
  if (n === 1) return { [keys[0]]: 1 }
  const A = buildCrispMatrix(keys, pairMatrix)
  const w = geometricMeanWeights(A)
  const out = {}
  keys.forEach((key, i) => { out[key] = w[i] })
  return out
}

function geometricMeanWeights (A) {
  const n = A.length
  const gm = A.map(row => {
    const prod = row.reduce((p, v) => p * (Number(v) || 1), 1)
    return Math.pow(prod, 1 / n)
  })
  const sum = gm.reduce((a, b) => a + b, 0)
  return sum > 0 ? gm.map(v => v / sum) : gm.map(() => 1 / n)
}

/**
 * 由完整模糊判断矩阵计算 FAHP 权重（PPT 六步）
 */
export function computeFahpWeightsFromFuzzyMatrix (criteriaKeys, fuzzyMatrix) {
  const keys = [...criteriaKeys]
  const n = keys.length
  const emptyConsistency = { lambdaMax: n, ci: 0, cr: 0, ri: 0, acceptable: true }
  if (n === 0) {
    return { weights: {}, weightsCrisp: {}, consistency: emptyConsistency, detail: null }
  }
  if (n === 1) {
    const w = { [keys[0]]: 1 }
    return { weights: w, weightsCrisp: { ...w }, consistency: emptyConsistency, detail: null }
  }

  const { rowSums, sTotal, fuzzyWeights } = computeFuzzyWeights(fuzzyMatrix)
  const weightArr = weightsFromFuzzyWeights(fuzzyWeights)
  const weights = {}
  keys.forEach((key, i) => { weights[key] = weightArr[i] })

  const weightsCrisp = computeCrispAhpWeights(keys, buildCrispMatrixFromFuzzy(fuzzyMatrix))

  return {
    weights: normalizeWeightObject(weights, keys),
    weightsCrisp: normalizeWeightObject(weightsCrisp, keys),
    consistency: computeConsistencyFromFuzzy(fuzzyMatrix),
    detail: { rowSums, sTotal, fuzzyWeights, weightArr }
  }
}

/** 从模糊矩阵取中值构建 crisp 矩阵（一致性检验用） */
function buildCrispMatrixFromFuzzy (fuzzyMatrix) {
  return fuzzyMatrix.map(row => row.map(cell => cell[1]))
}

function computeConsistencyFromFuzzy (fuzzyMatrix) {
  const n = fuzzyMatrix.length
  if (n < 3) {
    return { lambdaMax: n, ci: 0, cr: 0, ri: 0, acceptable: true }
  }
  const A = buildCrispMatrixFromFuzzy(fuzzyMatrix)
  const w = geometricMeanWeights(A)
  let lambdaSum = 0
  for (let i = 0; i < n; i++) {
    const aw = A[i].reduce((s, aij, j) => s + aij * w[j], 0)
    lambdaSum += w[i] > 0 ? aw / w[i] : 0
  }
  const lambdaMax = lambdaSum / n
  const ci = (lambdaMax - n) / (n - 1)
  const ri = RI_TABLE[n] != null ? RI_TABLE[n] : 1.45
  const cr = ri > 0 ? ci / ri : 0
  return {
    lambdaMax: Math.round(lambdaMax * 1000) / 1000,
    ci: Math.round(ci * 1000) / 1000,
    cr: Math.round(cr * 1000) / 1000,
    ri,
    acceptable: cr <= 0.1
  }
}

/**
 * FAHP 权重（由 1~9 标度上三角矩阵构建模糊矩阵后按 PPT 六步计算）
 */
export function computeFahpWeights (criteriaKeys, pairMatrix) {
  const keys = [...criteriaKeys]
  if (keys.length === 0) {
    return {
      weights: {},
      weightsCrisp: {},
      consistency: { lambdaMax: 0, ci: 0, cr: 0, ri: 0, acceptable: true },
      detail: null
    }
  }
  const fuzzy = buildFuzzyMatrix(keys, pairMatrix)
  const result = computeFahpWeightsFromFuzzyMatrix(keys, fuzzy)
  return {
    weights: result.weights,
    weightsChang: { ...result.weights },
    weightsCrisp: result.weightsCrisp,
    consistency: result.consistency,
    detail: result.detail
  }
}

export function roundWeight (w, precision = 4) {
  const f = Math.pow(10, precision)
  const v = Number(w) || 0
  if (v <= 0) return 0
  const rounded = Math.round(v * f) / f
  if (rounded <= 0) return 1 / f
  return rounded
}

/** 归一化权重对象，保证每项为正且和为 1 */
export function normalizeWeightObject (weights, keys) {
  const n = keys.length
  if (!n) return {}
  const raw = keys.map(k => Math.max(Number(weights[k]) || 0, 0))
  const sum = raw.reduce((a, b) => a + b, 0)
  if (sum <= 0) {
    const equal = 1 / n
    return keys.reduce((o, k) => ({ ...o, [k]: equal }), {})
  }
  const minShare = 1 / (n * 1000)
  const boosted = raw.map(v => Math.max(v / sum, minShare))
  const boostSum = boosted.reduce((a, b) => a + b, 0)
  const out = {}
  keys.forEach((k, i) => {
    out[k] = boosted[i] / boostSum
  })
  return out
}
