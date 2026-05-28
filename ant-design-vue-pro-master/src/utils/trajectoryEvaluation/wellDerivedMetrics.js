/**
 * 根据所选井的轨迹、井口/靶点、邻井防碰扫描等数据，自动计算部分二级指标
 */
import * as XLSXModule from 'xlsx'
import { drillingAPI } from '@/api'

const XLSX = XLSXModule.default || XLSXModule

const EXCEL_COLUMNS = {
  md: ['测深(m)', '测深（m）', '测深', 'MD', 'md'],
  inclination: ['井斜角(°)', '井斜角（°）', '井斜角', '井斜', 'inclination'],
  azimuth: ['网格方位(°)', '网格方位（°）', '网格方位', '方位', 'azimuth']
}

function findColumnIndex (headers, aliases) {
  const lower = (v) => (v && String(v).trim().toLowerCase())
  for (let i = 0; i < headers.length; i++) {
    const h = lower(headers[i])
    if (aliases.some(a => lower(a) === h)) return i
  }
  return -1
}

function parseSurveyFromExcelBuffer (buffer, wellhead) {
  if (!XLSX || typeof XLSX.read !== 'function' || !buffer) return { rows: [], points: [] }
  const wb = XLSX.read(new Uint8Array(buffer), { type: 'array' })
  const sheet = wb.Sheets[wb.SheetNames[0]]
  const json = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
  if (!json || !json.length) return { rows: [], points: [] }

  let headerRowIdx = 0
  let mdIdx = -1
  let incIdx = -1
  let aziIdx = -1
  for (let i = 0; i < Math.min(json.length, 20); i++) {
    const row = json[i]
    const md = findColumnIndex(row, EXCEL_COLUMNS.md)
    const inc = findColumnIndex(row, EXCEL_COLUMNS.inclination)
    const azi = findColumnIndex(row, EXCEL_COLUMNS.azimuth)
    if (md >= 0 && inc >= 0 && azi >= 0) {
      headerRowIdx = i
      mdIdx = md
      incIdx = inc
      aziIdx = azi
      break
    }
  }
  if (mdIdx < 0) {
    mdIdx = 0
    incIdx = 1
    aziIdx = 2
  }

  const rows = []
  for (let i = headerRowIdx + 1; i < json.length; i++) {
    const r = json[i]
    const md = Number(r[mdIdx])
    const inclination = Number(r[incIdx])
    const azimuth = Number(r[aziIdx])
    if (!Number.isFinite(md) && !Number.isFinite(inclination) && !Number.isFinite(azimuth)) continue
    rows.push({
      md: Number.isFinite(md) ? md : 0,
      inclination: Number.isFinite(inclination) ? inclination : 0,
      azimuth: Number.isFinite(azimuth) ? azimuth : 0
    })
  }

  const wh = [
    Number(wellhead && wellhead.e) || 0,
    Number(wellhead && wellhead.n) || 0,
    Number(wellhead && wellhead.d) || 0
  ]
  const points = surveyRowsToPoints(rows, wh)
  return { rows, points }
}

function surveyRowsToPoints (rows, wellhead) {
  const [x0, y0, z0] = wellhead
  const out = [{ x: x0, y: y0, z: z0 }]
  const toRad = v => (v * Math.PI) / 180
  for (let i = 1; i < rows.length; i++) {
    const p1 = rows[i - 1]
    const p2 = rows[i]
    const md1 = p1.md
    const md2 = p2.md
    const dmd = md2 - md1
    if (dmd <= 0) continue
    const inc1 = toRad(p1.inclination)
    const inc2 = toRad(p2.inclination)
    const az1 = toRad(p1.azimuth)
    const az2 = toRad(p2.azimuth)
    let cosDogleg = Math.cos(inc1) * Math.cos(inc2) + Math.sin(inc1) * Math.sin(inc2) * Math.cos(az2 - az1)
    cosDogleg = Math.max(-1, Math.min(1, cosDogleg))
    const dogleg = Math.acos(cosDogleg)
    const rf = dogleg < 1e-12 ? 1 : (2 / dogleg) * Math.tan(dogleg / 2)
    const dN = 0.5 * dmd * (Math.sin(inc1) * Math.cos(az1) + Math.sin(inc2) * Math.cos(az2)) * rf
    const dE = 0.5 * dmd * (Math.sin(inc1) * Math.sin(az1) + Math.sin(inc2) * Math.sin(az2)) * rf
    const dD = 0.5 * dmd * (Math.cos(inc1) + Math.cos(inc2)) * rf
    const prev = out[out.length - 1]
    out.push({ x: prev.x + dE, y: prev.y + dN, z: prev.z + dD })
  }
  return out
}

/** 最大狗腿度 °/30m */
export function computeMaxDLS (surveyRows) {
  if (!surveyRows || surveyRows.length < 2) return null
  const toRad = v => (v * Math.PI) / 180
  let maxDls = 0
  for (let i = 1; i < surveyRows.length; i++) {
    const p1 = surveyRows[i - 1]
    const p2 = surveyRows[i]
    const dmd = p2.md - p1.md
    if (dmd <= 1e-6) continue
    const inc1 = toRad(p1.inclination)
    const inc2 = toRad(p2.inclination)
    const az1 = toRad(p1.azimuth)
    const az2 = toRad(p2.azimuth)
    let cosDl = Math.cos(inc1) * Math.cos(inc2) + Math.sin(inc1) * Math.sin(inc2) * Math.cos(az2 - az1)
    cosDl = Math.max(-1, Math.min(1, cosDl))
    const doglegRad = Math.acos(cosDl)
    const dls = (doglegRad * 180 / Math.PI) * (30 / dmd)
    if (Number.isFinite(dls)) maxDls = Math.max(maxDls, dls)
  }
  return maxDls > 0 ? Math.round(maxDls * 100) / 100 : null
}

/** 下拉选项唯一键：避免已钻井与待钻井 id 相同导致匹配错误 */
export function wellSelectionKey (well) {
  if (!well || well.id == null || well.id === '') return ''
  const type = well.type === 'planned' ? 'planned' : 'existing'
  return `${type}:${well.id}`
}

export function parseWellSelectionKey (key) {
  if (key == null || key === '') return null
  const s = String(key)
  const idx = s.indexOf(':')
  if (idx > 0) {
    return { type: s.slice(0, idx), id: s.slice(idx + 1) }
  }
  return { type: null, id: s }
}

/** 按 type:id 或纯 id（优先待钻井）在井列表中查找 */
export function findWellInList (wellList, selectionKey) {
  const parsed = parseWellSelectionKey(selectionKey)
  if (!parsed || !wellList || !wellList.length) return null
  const matches = wellList.filter(w => String(w.id) === String(parsed.id))
  if (!matches.length) return null
  if (parsed.type) {
    return matches.find(w => w.type === parsed.type) || null
  }
  return matches.find(w => w.type === 'planned') || matches[0]
}

/** 入靶偏差：库字段 finalDeviation；设计接口有时为 final_deviation */
export function readFinalDeviation (source) {
  if (!source) return null
  const v = source.finalDeviation != null
    ? source.finalDeviation
    : source.final_deviation
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n * 100) / 100 : null
}

function pickNum (source, ...keys) {
  if (!source) return null
  for (const k of keys) {
    if (source[k] == null) continue
    const n = Number(source[k])
    if (Number.isFinite(n)) return n
  }
  return null
}

/** 解包 getById 等单条接口响应（兼容 { data: entity }） */
export function normalizeWellDetail (res) {
  if (!res) return null
  if (res.data != null && typeof res.data === 'object' && !Array.isArray(res.data)) {
    return res.data
  }
  return res
}

/**
 * 中靶偏差 Et
 * - 待钻井：仅用库中「入靶偏差(m)」finalDeviation，不用轨迹末点距离替代
 * - 已钻井：有 finalDeviation 用之，否则轨迹末点与靶点空间距离
 */
export function computeTargetDeviation (meta, points) {
  const fromDesign = readFinalDeviation(meta)
  if (meta && meta.type === 'planned') {
    return fromDesign
  }
  if (fromDesign != null) return fromDesign

  const te = pickNum(meta, 'targetE', 'target_e')
  const tn = pickNum(meta, 'targetN', 'target_n')
  const td = pickNum(meta, 'targetD', 'target_d')
  if (te == null || tn == null || td == null) return null
  if (!points || !points.length) return null
  const last = points[points.length - 1]
  const de = last.x - te
  const dn = last.y - tn
  const dd = last.z - td
  const dist = Math.sqrt(de * de + dn * dn + dd * dd)
  return Math.round(dist * 100) / 100
}

/**
 * 井身指数 Lr = 测深 MD / 垂深 TVD
 * TVD = |靶点垂深 − 井口垂深|（起点、靶点 D）
 */
export function computeWellComplexityIndex (surveyRows, meta, points) {
  if (!surveyRows || !surveyRows.length) return null
  const md = Number(surveyRows[surveyRows.length - 1].md)
  if (!Number.isFinite(md) || md <= 0) return null

  const whD = pickNum(meta, 'wellheadD', 'wellhead_d')
  const tgD = pickNum(meta, 'targetD', 'target_d')
  let tvd = null
  if (whD != null && tgD != null) {
    tvd = Math.abs(tgD - whD)
  } else if (whD != null && points && points.length) {
    const lastZ = Number(points[points.length - 1].z)
    if (Number.isFinite(lastZ)) {
      tvd = Math.abs(lastZ - whD)
    }
  }
  if (!Number.isFinite(tvd) || tvd <= 0) return null

  const lr = md / tvd
  return Math.round(lr * 100) / 100
}

async function loadWellTrajectoryBuffer (wellMeta) {
  if (wellMeta.type === 'planned') {
    const buf = await drillingAPI.downloadPendingDrillWellTrajectoryExcel(wellMeta.id)
    return buf
  }
  if (wellMeta.wellNo) {
    return drillingAPI.getWellTrajectoryExcel(wellMeta.wellNo)
  }
  return null
}

async function loadWellDetail (wellMeta) {
  if (wellMeta.type === 'planned') {
    return drillingAPI.getPendingDrillWellById(wellMeta.id)
  }
  return drillingAPI.getWellById(wellMeta.id)
}

function buildMetaFromDetail (detail, wellMeta) {
  const d = normalizeWellDetail(detail) || {}
  const base = { ...(wellMeta || {}) }
  const fd = readFinalDeviation(d) ?? readFinalDeviation(base)
  const meta = {
    ...base,
    type: base.type || wellMeta.type,
    wellheadE: pickNum(d, 'wellheadE', 'wellhead_e') ?? pickNum(base, 'wellheadE'),
    wellheadN: pickNum(d, 'wellheadN', 'wellhead_n') ?? pickNum(base, 'wellheadN'),
    wellheadD: pickNum(d, 'wellheadD', 'wellhead_d') ?? pickNum(base, 'wellheadD'),
    targetE: pickNum(d, 'targetE', 'target_e') ?? pickNum(base, 'targetE'),
    targetN: pickNum(d, 'targetN', 'target_n') ?? pickNum(base, 'targetN'),
    targetD: pickNum(d, 'targetD', 'target_d') ?? pickNum(base, 'targetD')
  }
  if (fd != null) meta.finalDeviation = fd
  return meta
}

async function computeMinSeparationFactor (siteId, wellId, neighborWellList) {
  const neighborIds = (neighborWellList || [])
    .filter(w => String(w.siteId) === String(siteId) && w.type === 'existing')
    .map(w => Number(w.id))
    .filter(id => Number.isFinite(id))
  if (!neighborIds.length) return { value: null, note: '当前井场无其它邻井，无法自动计算 SFmin' }
  try {
    const res = await drillingAPI.anticollisionScan({
      siteId: Number(siteId),
      trajectoryId: Number(wellId),
      neighborWellIds: neighborIds,
      anticollisionMethod: 'SF',
      minSafetyFactor: 1.2
    })
    const data = res && res.data ? res.data : res
    const sf = data && data.minSafetyFactor != null ? Number(data.minSafetyFactor) : null
    if (!Number.isFinite(sf)) {
      return { value: null, note: '防碰扫描未返回有效 SF' }
    }
    return {
      value: Math.round(sf * 100) / 100,
      note: `已对 ${neighborIds.length} 口邻井执行 SF 法防碰扫描`
    }
  } catch (e) {
    return { value: null, note: '防碰扫描失败：' + (e.message || '未知错误') }
  }
}

/**
 * @param {Object} params
 * @param {number} params.siteId
 * @param {Object} params.wellMeta - { id, type, wellNo, siteId }
 * @param {Array} params.wellList - 待评价井（待钻井）列表
 * @param {Array} [params.neighborWellList] - 同井场已钻井，用于 SFmin 邻井防碰
 */
export async function fetchDerivedMetricsForWell ({ siteId, wellMeta, wellList, neighborWellList = [] }) {
  const notes = []
  const values = {
    anticollision: { SFmin: undefined },
    control: { DLS: undefined, Et: undefined },
    complexity: { Lr: undefined }
  }

  if (!wellMeta || !wellMeta.id) {
    return { values, notes: ['请先选择待评价井'] }
  }

  let detail = null
  try {
    detail = await loadWellDetail(wellMeta)
  } catch (e) {
    notes.push('获取井详情失败，将使用井列表中的入靶偏差等字段')
  }

  const meta = buildMetaFromDetail(detail, wellMeta)
  if (readFinalDeviation(meta) == null) {
    const listItem = findWellInList(wellList, wellSelectionKey(wellMeta)) || wellMeta
    const fd = readFinalDeviation(listItem)
    if (fd != null) {
      meta.finalDeviation = fd
      notes.push(`已从井列表读取入靶偏差 ${fd} m`)
    }
  }
  const wellhead = { e: meta.wellheadE, n: meta.wellheadN, d: meta.wellheadD }

  let buffer = null
  try {
    buffer = await loadWellTrajectoryBuffer(wellMeta)
  } catch (e) {
    notes.push('未获取到井斜数据表，DLS/Lr 无法自动计算')
  }

  let surveyRows = []
  let points = []
  if (buffer) {
    const parsed = parseSurveyFromExcelBuffer(buffer, wellhead)
    surveyRows = parsed.rows
    points = parsed.points
    if (!surveyRows.length) {
      notes.push('井斜数据表无有效测点')
    }
  }

  const dls = computeMaxDLS(surveyRows)
  if (dls != null) {
    values.control.DLS = dls
    notes.push(`最大狗腿度 DLS = ${dls} °/30m（由井斜数据表计算）`)
  }

  const et = computeTargetDeviation(meta, points)
  const hasDesignEt = readFinalDeviation(meta) != null
  if (et != null) {
    values.control.Et = et
    notes.push(wellMeta.type === 'planned' || hasDesignEt
      ? `中靶偏差 Et = ${et} m（待钻井入靶偏差 finalDeviation）`
      : `中靶偏差 Et = ${et} m（轨迹末点与靶点空间距离）`)
  } else if (wellMeta.type === 'planned') {
    notes.push('该待钻井未保存入靶偏差(m)，请在轨迹设计保存或基础数据中确认 finalDeviation')
  } else if (wellMeta.type === 'existing') {
    notes.push('该井无靶点/入靶偏差数据，Et 请手动填写')
  } else {
    notes.push('缺少靶点或轨迹，Et 无法自动计算')
  }

  const lr = computeWellComplexityIndex(surveyRows, meta, points)
  if (lr != null) {
    values.complexity.Lr = lr
    const whD = pickNum(meta, 'wellheadD', 'wellhead_d')
    const tgD = pickNum(meta, 'targetD', 'target_d')
    const md = surveyRows[surveyRows.length - 1].md
    const tvd = tgD != null && whD != null ? Math.abs(tgD - whD) : null
    if (tvd != null) {
      notes.push(`井身指数 Lr = ${lr}（MD=${md} m / TVD=${Math.round(tvd * 100) / 100} m）`)
    } else {
      notes.push(`井身指数 Lr = ${lr}（测深/垂深）`)
    }
  } else if (surveyRows.length) {
    notes.push('缺少井口/靶点垂深或垂深为 0，Lr 无法自动计算')
  }

  const sfResult = await computeMinSeparationFactor(siteId, wellMeta.id, neighborWellList)
  if (sfResult.value != null) {
    values.anticollision.SFmin = sfResult.value
  }
  notes.push(sfResult.note)

  return { values, notes }
}

export function isComputedIndicator (field) {
  return field && field.computed === true
}
