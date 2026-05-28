/**
 * 井眼轨迹综合评价 — 指标体系与默认权重
 * 二级指标区间与分值映射可按 PPT 细则在 scoreRules 中调整
 */

export const GRADE_LABELS = ['优秀', '合格', '不合格']

export const BUCKLING_OPTIONS = [
  { value: 'none', label: '无', score: 10 },
  { value: 'slight_sine', label: '轻微正弦', score: 8 },
  { value: 'obvious_sine', label: '明显正弦', score: 4 },
  { value: 'slight_helix', label: '轻微螺旋', score: 2 },
  { value: 'severe_helix', label: '严重螺旋', score: 0 }
]

/** 默认一级权重（和为 1） */
export const DEFAULT_LEVEL1_WEIGHTS = {
  stability: 0.25,
  friction: 0.20,
  hydraulic: 0.20,
  anticollision: 0.15,
  control: 0.10,
  complexity: 0.10
}

/** 默认二级权重（各一级下和为 1） */
export const DEFAULT_LEVEL2_WEIGHTS = {
  stability: { dMW: 0.7, R: 0.3 },
  friction: { H: 0.5, T: 0.3, buckling: 0.2 },
  hydraulic: { M: 0.4, K: 0.6 },
  anticollision: { SFmin: 1.0 },
  control: { DLS: 0.6, Et: 0.4 },
  complexity: { Lr: 1.0 }
}

const STORAGE_KEY = 'trajectory_eval_weights_v1'

export function loadSavedWeights () {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

export function saveWeights (level1, level2, extra = {}) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    level1,
    level2,
    savedAt: Date.now(),
    ...extra
  }))
}

export function getDefaultWeights () {
  return {
    level1: { ...DEFAULT_LEVEL1_WEIGHTS },
    level2: JSON.parse(JSON.stringify(DEFAULT_LEVEL2_WEIGHTS))
  }
}

/**
 * @typedef {Object} IndicatorField
 * @property {string} key
 * @property {string} label
 * @property {string} unit
 * @property {'number'|'percent'|'select'} inputType
 * @property {number} min
 * @property {number} max
 * @property {string} hint
 * @property {'higher'|'lower'|'optimal'} scoreMode - 分值映射方向
 * @property {number[]} [thresholds] - 优/良/中/差四档边界 [t10,t8,t6,t4]，段内线性插值
 * @property {number[]} [scoreAnchors] - 各档边界对应 0~10 分（默认 [10,8,6,4]）；可与百分制 90/80/70/60 对应为 [9,8,7,6]
 * @property {{ x: number, score: number }} [worstAnchor] - 极差端点（如 ΔMW 在 0 处为 0 分）
 * @property {number} [bestScore] - 优于优档上限时的得分封顶（如 ΔMW≥0.15 最高 10 分）
 * @property {{ x: number, score: number }[]} [scoreBreakpoints] - 完全自定义锚点（优先级最高）
 * @property {number} [optimal] - optimal 模式理想值
 */

export const INDICATOR_TREE = [
  {
    key: 'stability',
    title: '井壁稳定性',
    level1WeightKey: 'stability',
    children: [
      {
        key: 'dMW',
        label: '安全密度窗口 ΔMW',
        unit: 'g/cm³',
        inputType: 'number',
        min: 0,
        max: 1,
        step: 0.01,
        hint: '取值范围 >0 g/cm³',
        scoreMode: 'higher',
        thresholds: [0.15, 0.12, 0.08, 0.05],
        scoreAnchors: [9, 8, 7, 6],
        worstAnchor: { x: 0, score: 0 },
        bestScore: 10
      },
      {
        key: 'R',
        label: '风险段占比 R',
        unit: '%',
        inputType: 'number',
        min: 0,
        max: 100,
        step: 0.1,
        hint: '按评分标准填百分比数值（0~100）',
        scoreMode: 'lower',
        thresholds: [5, 10, 15, 20]
      }
    ]
  },
  {
    key: 'friction',
    title: '摩阻扭矩与管柱屈曲',
    level1WeightKey: 'friction',
    children: [
      {
        key: 'H',
        label: '钩载比 H',
        unit: '',
        inputType: 'ratioSum',
        min: 0.3,
        max: 2.5,
        sumInputs: [
          { key: 'H_sim', label: '本井模拟最大钩载', unit: 'kN', min: 0, max: 1e8, step: 0.01 },
          { key: 'H_ref', label: '钻机额定钩载', unit: 'kN', min: 1e-6, max: 1e8, step: 0.01 }
        ],
        hint: '录入模拟钩载与参考钩载',
        scoreMode: 'lower',
        thresholds: [1.2, 1.4, 1.6, 1.8]
      },
      {
        key: 'T',
        label: '扭矩比 T',
        unit: '',
        inputType: 'ratioSum',
        min: 0.3,
        max: 2.5,
        sumInputs: [
          { key: 'T_sim', label: '本井模拟最大扭矩', unit: 'kN·m', min: 0, max: 1e8, step: 0.01 },
          { key: 'T_ref', label: '顶驱额定输出扭矩', unit: 'kN·m', min: 1e-6, max: 1e8, step: 0.01 }
        ],
        hint: '录入模拟扭矩与参考扭矩',
        scoreMode: 'lower',
        thresholds: [1.2, 1.4, 1.6, 1.8]
      },
      {
        key: 'buckling',
        label: '模拟屈曲状态',
        unit: '',
        inputType: 'select',
        hint: '下拉选择屈曲程度',
        scoreMode: 'buckling'
      }
    ]
  },
  {
    key: 'hydraulic',
    title: '水力能力与井眼清洁',
    level1WeightKey: 'hydraulic',
    children: [
      {
        key: 'M',
        label: 'ECD 裕度 M',
        unit: 'g/cm³',
        inputType: 'number',
        min: 0,
        step: 0.001,
        hint: '破裂压力梯度 - 当量循环密度 (g/cm³)',
        scoreMode: 'higher',
        thresholds: [0.05, 0.03, 0.01, 0.01],
        scoreBreakpoints: [
          { x: 0, score: 0 },
          { x: 0.01, score: 6 },
          { x: 0.03, score: 7.5 },
          { x: 0.05, score: 9 }
        ],
        bestScore: 10
      },
      {
        key: 'K',
        label: '清洁难度系数 K',
        unit: '',
        inputType: 'derivedFormula',
        compute: 'cleaningDifficultyK',
        min: 0,
        max: 10,
        formulaInputs: [
          { key: 'K_Qmin', label: '满足井眼清洁要求的最小排量', symbol: 'Q_min', unit: 'L/s', min: 0.01, max: 500, step: 0.01 },
          { key: 'K_dP', label: '系统循环压耗', symbol: 'ΔP', unit: 'MPa', min: 0.01, max: 80, step: 0.01 },
          { key: 'K_Qbase', label: '基准排量', symbol: 'Q_base', unit: 'L/s', min: 0.01, max: 500, step: 0.01 },
          { key: 'K_dPbase', label: '基准压耗', symbol: 'ΔP_base', unit: 'MPa', min: 0.01, max: 80, step: 0.01 }
        ],
        hint: '根据邻井实测设定基准排量Q_base、基准压耗ΔP_base，系统计算 K = (Q_min/Q_base)×(ΔP/ΔP_base)',
        scoreMode: 'lower',
        thresholds: [1.2, 1.5, 2.0, 2.5]
      }
    ]
  },
  {
    key: 'anticollision',
    title: '防碰风险',
    level1WeightKey: 'anticollision',
    children: [
      {
        key: 'SFmin',
        label: '最小分离系数 SFmin',
        unit: '',
        inputType: 'number',
        min: 0,
        step: 0.01,
        computed: true,
        hint: '根据所选井与同井场邻井自动执行 SF 法防碰扫描',
        scoreMode: 'higher',
        thresholds: [2.0, 1.5, 1.2, 1.0]
      }
    ]
  },
  {
    key: 'control',
    title: '轨迹控制能力',
    level1WeightKey: 'control',
    children: [
      {
        key: 'DLS',
        label: '最大全角变化率 DLS',
        unit: '°/30m',
        inputType: 'number',
        min: 0,
        max: 30,
        step: 0.1,
        computed: true,
        hint: '由井斜数据表测点自动计算最大狗腿度',
        scoreMode: 'lower',
        thresholds: [2, 3, 5, 7]
      },
      {
        key: 'Et',
        label: '中靶偏差 Et',
        unit: 'm',
        inputType: 'number',
        min: 0,
        max: 100,
        step: 0.1,
        computed: true,
        hint: '待钻井自动读取库中入靶偏差(m)',
        scoreMode: 'lower',
        thresholds: [10, 20, 30, 40]
      }
    ]
  },
  {
    key: 'complexity',
    title: '工程复杂度',
    level1WeightKey: 'complexity',
    children: [
      {
        key: 'Lr',
        label: '井身指数 Lr',
        unit: '',
        inputType: 'number',
        min: 0,
        step: 0.01,
        computed: true,
        hint: '自动计算 Lr = 测深 MD / 垂深 TVD',
        scoreMode: 'lower',
        thresholds: [1.1, 1.2, 1.3, 1.4]
      }
    ]
  }
]

export const LEVEL1_ORDER = INDICATOR_TREE.map(g => g.key)
