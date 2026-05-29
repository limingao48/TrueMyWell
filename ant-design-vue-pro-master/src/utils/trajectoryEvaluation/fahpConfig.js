/** FAHP 1~9 标度对应的三角模糊数 (l, m, u) — Chang 法常用取值 */
export const FUZZY_TRIANGLES_1_9 = {
  1: [1, 1, 1],
  2: [1, 2, 3],
  3: [2, 3, 4],
  4: [3, 4, 5],
  5: [4, 5, 6],
  6: [5, 6, 7],
  7: [6, 7, 8],
  8: [7, 8, 9],
  9: [8, 9, 9]
}

/** 随机一致性指标 RI */
export const RI_TABLE = {
  1: 0,
  2: 0,
  3: 0.58,
  4: 0.90,
  5: 1.12,
  6: 1.24,
  7: 1.32,
  8: 1.41,
  9: 1.45
}

export const FAHP_LINGUISTIC_OPTIONS = [
  { value: 1, label: '1 — 同等重要' },
  { value: 2, label: '2 — 介于同等与稍微' },
  { value: 3, label: '3 — 稍微重要' },
  { value: 4, label: '4 — 介于稍微与明显' },
  { value: 5, label: '5 — 明显重要' },
  { value: 6, label: '6 — 介于明显与强烈' },
  { value: 7, label: '7 — 强烈重要' },
  { value: 8, label: '8 — 介于强烈与极端' },
  { value: 9, label: '9 — 极端重要' }
]
