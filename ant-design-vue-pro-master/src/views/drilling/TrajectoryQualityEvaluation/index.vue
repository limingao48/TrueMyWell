<template>
  <div class="trajectory-quality-eval">
    <a-alert
      type="info"
      show-icon
      style="margin-bottom: 16px"
      message="流程：选择井场与待钻井（自动计算 SFmin、DLS、Et、Lr）→ 设置权重（直接填写或 FAHP）→ 补录其余指标 → 综合评价"
    />

    <!-- 选井 -->
    <a-card title="1. 选择评价对象" size="small" class="section-card">
      <div class="algo-row">
        <label class="algo-label">井场：</label>
        <a-select
          v-model="siteId"
          placeholder="请选择井场"
          class="algo-input-inner"
          allow-clear
          @change="onSiteChange"
        >
          <a-select-option v-for="s in siteList" :key="s.id" :value="s.id">{{ s.name }}</a-select-option>
        </a-select>
      </div>
      <div class="algo-row">
        <label class="algo-label">待评价井（待钻井）：</label>
        <a-select
          v-model="wellId"
          placeholder="请先选择井场，再选待钻井"
          class="algo-input-inner"
          :disabled="!siteId"
          allow-clear
          @change="onWellChange"
        >
          <a-select-option v-for="w in wellOptions" :key="w.key" :value="w.key">
            {{ w.label }}
          </a-select-option>
        </a-select>
        <a-button
          v-if="wellId"
          size="small"
          style="margin-left: 8px"
          :loading="metricsLoading"
          icon="reload"
          @click="loadDerivedMetrics"
        >
          重新计算井数据指标
        </a-button>
      </div>
      <a-alert
        v-if="derivedNotes.length"
        type="info"
        show-icon
        style="margin-top: 8px"
      >
        <template slot="message">
          <div v-for="(line, idx) in derivedNotes" :key="idx">{{ line }}</div>
        </template>
      </a-alert>
    </a-card>

    <!-- 权重 -->
    <a-card title="2. 权重设置" size="small" class="section-card weight-card">
      <a-radio-group v-model="weightMode" button-style="solid" class="weight-mode-switch" @change="onWeightModeChange">
        <a-radio-button value="manual">直接设置权重</a-radio-button>
        <a-radio-button value="fahp">FAHP 模糊层次分析</a-radio-button>
      </a-radio-group>

      <div class="weight-actions">
        <span :class="['weight-sum', level1SumOk ? 'ok' : 'err']">
          一级权重合计：{{ level1Sum.toFixed(4) }} {{ level1SumOk ? '✓' : '（须为 1）' }}
        </span>
        <template v-if="weightMode === 'manual'">
          <a-button size="small" @click="resetDefaultWeights">恢复默认权重</a-button>
        </template>
        <template v-else>
          <a-button size="small" type="primary" :loading="fahpComputing" @click="applyFahpWeights">
            计算并应用 FAHP 权重
          </a-button>
          <a-button size="small" @click="resetFahpMatrices">重置判断矩阵</a-button>
        </template>
        <!-- 暂不使用：保存权重为默认模板
        <a-button size="small" type="primary" ghost @click="saveWeightTemplate">保存为默认模板</a-button>
        -->
      </div>

      <!-- FAHP：模糊判断矩阵 -->
      <template v-if="weightMode === 'fahp'">
        <a-alert
          type="info"
          show-icon
          style="margin-bottom: 12px"
          message="填写 Saaty 1~9 标度矩阵；权重按 PPT 六步 FAHP（行和→总倒数→模糊权重→可能度→归一化）计算。CR≤0.1 为通过。"
        />
        <div class="fahp-section-title">一级指标判断矩阵</div>
        <fahp-matrix-panel
          v-model="fahpLevel1Matrix"
          :criteria="fahpLevel1Criteria"
          :consistency="fahpLevel1Consistency"
          @change="onFahpMatrixChange"
        />
        <a-collapse :bordered="false" class="level2-collapse fahp-l2-collapse">
          <a-collapse-panel
            v-for="g in indicatorTree"
            :key="'fahp-' + g.key"
            :header="g.title + ' — 二级判断矩阵'"
          >
            <fahp-matrix-panel
              v-if="g.children.length >= 2"
              v-model="fahpLevel2Matrices[g.key]"
              :criteria="fahpLevel2Criteria(g)"
              :consistency="fahpLevel2Consistency[g.key]"
              @change="onFahpMatrixChange"
            />
            <div v-else class="fahp-single-hint">仅一项二级指标，权重为 1。</div>
          </a-collapse-panel>
        </a-collapse>
        <a-divider>当前 FAHP 权重结果</a-divider>
      </template>

      <div class="weight-result-label">一级权重</div>
      <a-row :gutter="16" class="level1-weights">
        <a-col v-for="g in indicatorTree" :key="g.key" :span="8" :xl="4">
          <div class="weight-item">
            <span class="weight-label">{{ g.title }}</span>
            <a-input-number
              v-model="level1Weights[g.key]"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="4"
              :disabled="weightMode === 'fahp'"
              style="width: 100%"
            />
          </div>
        </a-col>
      </a-row>

      <a-collapse :bordered="false" class="level2-collapse">
        <a-collapse-panel v-for="g in indicatorTree" :key="g.key" :header="g.title + ' — 二级权重'">
          <span slot="extra" :class="level2SumOk[g.key] ? 'sum-ok' : 'sum-err'">
            合计 {{ (level2Sums[g.key] || 0).toFixed(4) }}
          </span>
          <a-row :gutter="12">
            <a-col v-for="c in g.children" :key="c.key" :span="8">
              <div class="weight-item">
                <span class="weight-label">{{ c.label }}</span>
                <a-input-number
                  v-model="level2Weights[g.key][c.key]"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :precision="4"
                  :disabled="weightMode === 'fahp'"
                  style="width: 100%"
                />
              </div>
            </a-col>
          </a-row>
        </a-collapse-panel>
      </a-collapse>
    </a-card>

    <!-- 指标录入 -->
    <a-card title="3. 二级指标录入" size="small" class="section-card indicator-entry-card">
      <div
        v-for="g in indicatorTree"
        :key="g.key"
        class="indicator-group"
      >
        <div class="indicator-group-title">{{ g.title }}</div>
        <div
          v-for="field in g.children"
          :key="field.key"
          class="indicator-row"
          :class="{ 'indicator-row--error': fieldErrors[g.key] && fieldErrors[g.key][field.key] }"
        >
          <div class="indicator-row-label">{{ fieldLabel(field) }}</div>
          <div class="indicator-row-body">
            <template v-if="field.computed">
              <div class="computed-field">
                <template v-if="metricsLoading">
                  <a-spin size="small" />
                  <span class="computed-desc">正在根据井数据计算…</span>
                </template>
                <template v-else-if="hasComputedValue(g.key, field.key)">
                  <span class="computed-value">{{ formatComputedDisplay(g.key, field) }}</span>
                  <a-tag color="blue" class="auto-tag">自动计算</a-tag>
                </template>
                <template v-else>
                  <span class="computed-pending">—</span>
                </template>
                <div class="computed-desc">{{ field.hint }}</div>
                <div
                  v-if="fieldErrors[g.key] && fieldErrors[g.key][field.key]"
                  class="computed-error"
                >
                  {{ fieldErrors[g.key][field.key] }}
                </div>
              </div>
            </template>
            <template v-else-if="field.inputType === 'ratioSum' || field.inputType === 'derivedFormula'">
              <div class="ratio-sum-block">
                <div
                  v-for="s in (field.sumInputs || field.formulaInputs)"
                  :key="s.key"
                  class="ratio-sum-row"
                >
                  <span class="ratio-sum-label">
                    {{ s.label }}{{ s.symbol ? ` ${s.symbol}` : '' }}{{ s.unit ? `（${s.unit}）` : '' }}
                  </span>
                  <a-input-number
                    v-model="formValues[g.key][s.key]"
                    :min="s.min"
                    :max="s.max"
                    :step="s.step || 1"
                    class="indicator-control ratio-sum-input"
                    :placeholder="`≥ ${s.min}`"
                  />
                </div>
                <div v-if="formatComputedPreview(g.key, field)" class="ratio-preview">
                  {{ field.label }} = {{ formatComputedPreview(g.key, field) }}
                </div>
              </div>
              <div v-if="field.hint" class="manual-hint">{{ field.hint }}</div>
            </template>
            <template v-else>
              <a-select
                v-if="field.inputType === 'select'"
                v-model="formValues[g.key][field.key]"
                placeholder="请选择屈曲状态"
                class="indicator-control"
                allow-clear
              >
                <a-select-option v-for="o in bucklingOptions" :key="o.value" :value="o.value">
                  {{ o.label }}（{{ o.score }} 分）
                </a-select-option>
              </a-select>
              <a-input-number
                v-else
                v-model="formValues[g.key][field.key]"
                :min="field.min"
                :max="numberInputMax(field)"
                :step="field.step || 0.01"
                class="indicator-control"
                :placeholder="numberInputPlaceholder(field)"
              />
              <div v-if="field.hint" class="manual-hint">{{ field.hint }}</div>
              <div
                v-if="fieldErrors[g.key] && fieldErrors[g.key][field.key]"
                class="computed-error"
              >
                {{ fieldErrors[g.key][field.key] }}
              </div>
            </template>
          </div>
        </div>
      </div>
      <div class="calc-row">
        <a-button type="primary" size="large" icon="calculator" :loading="calculating" @click="runEvaluation">
          执行综合评价
        </a-button>
      </div>
    </a-card>

    <!-- 结果 -->
    <template v-if="result">
      <a-card title="4. 评价结果" size="small" class="section-card">
        <a-alert
          :type="result.finalGrade === '优秀' ? 'success' : result.finalGrade === '合格' ? 'warning' : 'error'"
          show-icon
          style="margin-bottom: 16px"
        >
          <template slot="message">
            <span class="final-grade">最终等级：<strong>{{ result.finalGrade }}</strong></span>
            <span style="margin-left: 24px">
              综合隶属度 — 优秀 {{ formatMu(result.compositeMembership.excellent) }} /
              合格 {{ formatMu(result.compositeMembership.qualified) }} /
              不合格 {{ formatMu(result.compositeMembership.unqualified) }}
            </span>
          </template>
        </a-alert>

        <a-table
          :columns="secondaryColumns"
          :data-source="result.secondaryResults"
          :pagination="false"
          size="small"
          row-key="rowKey"
          bordered
          style="margin-bottom: 16px"
        />

        <a-table
          :columns="level1Columns"
          :data-source="level1TableData"
          :pagination="false"
          size="small"
          row-key="key"
          bordered
          style="margin-bottom: 16px"
        />

        <a-row :gutter="16">
          <a-col :span="12">
            <div class="chart-title">一级指标得分（0~100）</div>
            <div ref="scoreBarChart" class="result-chart" />
          </a-col>
          <a-col :span="12">
            <div class="chart-title">一级指标隶属度（雷达）</div>
            <div ref="membershipRadarChart" class="result-chart" />
          </a-col>
        </a-row>
        <div class="chart-title" style="margin-top: 16px">综合隶属度</div>
        <div ref="compositeBarChart" class="result-chart composite-chart" />

        <div style="margin-top: 16px">
          <a-button icon="download" @click="exportExcel">导出评价结果 Excel</a-button>
        </div>
      </a-card>
    </template>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import * as XLSXModule from 'xlsx'
import { drillingAPI } from '@/api'
import {
  INDICATOR_TREE,
  LEVEL1_ORDER,
  BUCKLING_OPTIONS,
  getDefaultWeights,
  loadSavedWeights
  // saveWeights — 暂不使用「保存为默认模板」
} from '@/utils/trajectoryEvaluation/config'
import { validateIndicatorInput, runTrajectoryEvaluation } from '@/utils/trajectoryEvaluation/evaluate'
import { resolveIndicatorRawValue } from '@/utils/trajectoryEvaluation/indicatorComputed'
import { validateWeightSum } from '@/utils/trajectoryEvaluation/fuzzy'
import {
  fetchDerivedMetricsForWell,
  findWellInList,
  wellSelectionKey
} from '@/utils/trajectoryEvaluation/wellDerivedMetrics'
import {
  createEmptyPairMatrix,
  computeFahpWeights,
  roundWeight,
  normalizeWeightObject,
  normalizePairMatrix
} from '@/utils/trajectoryEvaluation/fahp'
import FahpMatrixPanel from './FahpMatrixPanel.vue'

const XLSX = XLSXModule.default || XLSXModule

function emptyFormValues () {
  const v = {}
  INDICATOR_TREE.forEach(g => {
    v[g.key] = {}
    g.children.forEach(c => {
      if (c.inputType === 'ratioSum' && c.sumInputs) {
        c.sumInputs.forEach(s => {
          v[g.key][s.key] = undefined
        })
      } else if (c.inputType === 'derivedFormula' && c.formulaInputs) {
        c.formulaInputs.forEach(s => {
          v[g.key][s.key] = undefined
        })
      } else {
        v[g.key][c.key] = c.inputType === 'select' ? undefined : undefined
      }
    })
  })
  return v
}

function initFahpMatrices () {
  const level2 = {}
  INDICATOR_TREE.forEach(g => {
    if (g.children.length >= 2) {
      level2[g.key] = createEmptyPairMatrix(g.children.map(c => c.key))
    }
  })
  return {
    level1: createEmptyPairMatrix(LEVEL1_ORDER),
    level2
  }
}

export default {
  name: 'TrajectoryQualityEvaluation',
  components: { FahpMatrixPanel },
  data () {
    const defaults = getDefaultWeights()
    const saved = loadSavedWeights()
    const weights = saved || defaults
    const fahpInit = initFahpMatrices()
    return {
      weightMode: (saved && saved.weightMode) || 'manual',
      siteList: [],
      wellList: [],
      neighborWellList: [],
      siteId: undefined,
      wellId: undefined,
      indicatorTree: INDICATOR_TREE,
      bucklingOptions: BUCKLING_OPTIONS,
      level1Weights: { ...weights.level1 },
      level2Weights: JSON.parse(JSON.stringify(weights.level2)),
      fahpLevel1Matrix: normalizePairMatrix(
        (saved && saved.fahpLevel1Matrix) ? saved.fahpLevel1Matrix : fahpInit.level1,
        LEVEL1_ORDER
      ),
      fahpLevel2Matrices: (() => {
        const raw = (saved && saved.fahpLevel2Matrices)
          ? JSON.parse(JSON.stringify(saved.fahpLevel2Matrices))
          : fahpInit.level2
        const out = {}
        INDICATOR_TREE.forEach(g => {
          if (g.children.length >= 2) {
            const keys = g.children.map(c => c.key)
            out[g.key] = normalizePairMatrix(raw[g.key] || {}, keys)
          }
        })
        return out
      })(),
      fahpLevel1Consistency: null,
      fahpLevel2Consistency: {},
      fahpComputing: false,
      formValues: emptyFormValues(),
      fieldErrors: {},
      computedLocked: {},
      metricsLoading: false,
      derivedNotes: [],
      calculating: false,
      result: null,
      scoreBarChart: null,
      membershipRadarChart: null,
      compositeBarChart: null,
      secondaryColumns: [
        { title: '一级指标', dataIndex: 'groupTitle', key: 'groupTitle', width: 140 },
        { title: '二级指标', dataIndex: 'label', key: 'label', width: 160 },
        { title: '录入值', dataIndex: 'rawValue', key: 'rawValue', width: 100 },
        { title: '得分(0~10)', dataIndex: 'score10', key: 'score10', width: 90, customRender: (t) => (Number.isFinite(t) ? Number(t).toFixed(2) : '-') },
        { title: '备注', dataIndex: 'error', key: 'error' }
      ],
      level1Columns: [
        { title: '一级指标', dataIndex: 'title', key: 'title' },
        { title: '权重', dataIndex: 'weight', key: 'weight', width: 80 },
        { title: '得分(0~10)', dataIndex: 'score10', key: 'score10', width: 100 },
        { title: '得分(0~100)', dataIndex: 'score100', key: 'score100', width: 100 },
        { title: '优秀隶属度', dataIndex: 'muE', key: 'muE', width: 100 },
        { title: '合格隶属度', dataIndex: 'muQ', key: 'muQ', width: 100 },
        { title: '不合格隶属度', dataIndex: 'muU', key: 'muU', width: 100 }
      ]
    }
  },
  computed: {
    wellOptions () {
      if (!this.siteId) return []
      return this.wellList
        .filter(w => w.type === 'planned' && String(w.siteId) === String(this.siteId))
        .map(w => ({
          key: wellSelectionKey(w),
          id: w.id,
          label: `${w.wellNo || w.id} - ${w.name || '未命名'}`
        }))
    },
    level1Sum () {
      return Object.values(this.level1Weights).reduce((a, b) => a + (Number(b) || 0), 0)
    },
    level1SumOk () {
      return validateWeightSum(this.level1Weights)
    },
    level2Sums () {
      const s = {}
      INDICATOR_TREE.forEach(g => {
        const w = this.level2Weights[g.key] || {}
        s[g.key] = Object.values(w).reduce((a, b) => a + (Number(b) || 0), 0)
      })
      return s
    },
    level2SumOk () {
      const ok = {}
      INDICATOR_TREE.forEach(g => {
        ok[g.key] = validateWeightSum(this.level2Weights[g.key] || {})
      })
      return ok
    },
    fahpLevel1Criteria () {
      return this.indicatorTree.map(g => ({
        key: g.key,
        title: g.title
      }))
    },
    level1TableData () {
      if (!this.result) return []
      return this.result.level1Results.map(r => ({
        key: r.key,
        title: r.title,
        weight: r.weight,
        score10: Number.isFinite(r.score10) ? r.score10.toFixed(2) : '-',
        score100: Number.isFinite(r.score100) ? r.score100.toFixed(2) : '-',
        muE: this.formatMu(r.membership[0]),
        muQ: this.formatMu(r.membership[1]),
        muU: this.formatMu(r.membership[2])
      }))
    }
  },
  watch: {
    wellId (val) {
      if (val) this.loadDerivedMetrics()
      else {
        this.derivedNotes = []
        this.computedLocked = {}
      }
    }
  },
  created () {
    this.loadSiteList()
    if (this.weightMode === 'fahp') {
      this.applyFahpWeights(false)
    }
  },
  beforeDestroy () {
    this.disposeCharts()
  },
  methods: {
    normalizeListResponse (res) {
      if (Array.isArray(res)) return res
      if (res && Array.isArray(res.data)) return res.data
      return []
    },
    async loadSiteList () {
      try {
        const res = await drillingAPI.getSiteList()
        this.siteList = this.normalizeListResponse(res)
      } catch (e) {
        this.$message.error('加载井场失败')
      }
    },
    onWellChange () {
      this.result = null
    },
    hasComputedValue (groupKey, fieldKey) {
      const v = this.formValues[groupKey] && this.formValues[groupKey][fieldKey]
      return v != null && Number.isFinite(Number(v))
    },
    formatComputedDisplay (groupKey, field) {
      const v = this.formValues[groupKey][field.key]
      const n = Number(v)
      const text = Number.isInteger(n) ? String(n) : n.toFixed(2)
      return field.unit ? `${text} ${field.unit}` : text
    },
    clearComputedIndicators () {
      const locked = {}
      INDICATOR_TREE.forEach(g => {
        locked[g.key] = {}
        g.children.forEach(f => {
          if (f.computed) {
            this.formValues[g.key][f.key] = undefined
            locked[g.key][f.key] = false
          }
        })
      })
      this.computedLocked = locked
    },
    applyDerivedValues (values) {
      const locked = { ...this.computedLocked }
      INDICATOR_TREE.forEach(g => {
        if (!locked[g.key]) locked[g.key] = {}
        const gv = values[g.key] || {}
        g.children.forEach(f => {
          if (!f.computed) return
          const v = gv[f.key]
          if (v != null && Number.isFinite(Number(v))) {
            this.formValues[g.key][f.key] = Number(v)
            locked[g.key][f.key] = true
          } else {
            locked[g.key][f.key] = false
          }
        })
      })
      this.computedLocked = locked
    },
    async loadDerivedMetrics () {
      if (!this.siteId || !this.wellId) return
      const wellMeta = findWellInList(this.wellList, this.wellId)
      if (!wellMeta) {
        this.derivedNotes = ['未在井列表中找到所选井，请重新选择井场']
        return
      }
      this.metricsLoading = true
      this.clearComputedIndicators()
      try {
        const { values, notes } = await fetchDerivedMetricsForWell({
          siteId: this.siteId,
          wellMeta,
          wellList: this.wellList,
          neighborWellList: this.neighborWellList
        })
        this.applyDerivedValues(values)
        this.derivedNotes = notes
      } catch (e) {
        this.derivedNotes = ['自动计算失败：' + (e.message || '未知错误')]
      } finally {
        this.metricsLoading = false
      }
    },
    async onSiteChange () {
      this.wellId = undefined
      this.derivedNotes = []
      this.computedLocked = {}
      this.result = null
      this.wellList = []
      this.neighborWellList = []
      if (!this.siteId) return
      try {
        const [existingRes, pendingRes] = await Promise.all([
          drillingAPI.getWellsBySite(this.siteId),
          drillingAPI.getPendingDrillWellsBySite(this.siteId)
        ])
        this.neighborWellList = this.normalizeListResponse(existingRes).map(w => ({
          id: w.id,
          siteId: w.siteId,
          wellNo: w.wellNo,
          name: w.name,
          type: 'existing'
        }))
        this.wellList = this.normalizeListResponse(pendingRes).map(w => ({
          id: w.id,
          siteId: w.siteId,
          wellNo: w.wellNo || `待钻-${w.id}`,
          name: w.name,
          type: 'planned',
          wellheadE: w.wellheadE,
          wellheadN: w.wellheadN,
          wellheadD: w.wellheadD,
          targetE: w.targetE,
          targetN: w.targetN,
          targetD: w.targetD,
          finalDeviation: w.finalDeviation != null
            ? Number(w.finalDeviation)
            : (w.final_deviation != null ? Number(w.final_deviation) : undefined)
        }))
        if (!this.wellList.length) {
          this.$message.info('该井场暂无待钻井，请先在轨迹设计中保存待钻井')
        }
      } catch (e) {
        this.$message.error('加载井列表失败')
      }
    },
    fahpLevel2Criteria (group) {
      return group.children.map(c => ({
        key: c.key,
        title: c.label
      }))
    },
    applyWeightObject (target, weights, keys) {
      const normalized = normalizeWeightObject(weights, keys)
      keys.forEach(k => {
        this.$set(target, k, roundWeight(normalized[k]))
      })
      const rounded = normalizeWeightObject(target, keys)
      keys.forEach(k => {
        this.$set(target, k, roundWeight(rounded[k]))
      })
    },
    onWeightModeChange () {
      if (this.weightMode === 'fahp') {
        this.applyFahpWeights(false)
      }
    },
    onFahpMatrixChange () {
      // 矩阵变更后仅更新一致性展示，不自动改权重，避免输入过程中频繁跳动
      this.refreshFahpConsistency()
    },
    refreshFahpConsistency () {
      const r1 = computeFahpWeights(LEVEL1_ORDER, this.fahpLevel1Matrix)
      this.fahpLevel1Consistency = r1.consistency
      const l2c = {}
      INDICATOR_TREE.forEach(g => {
        if (g.children.length >= 2) {
          const keys = g.children.map(c => c.key)
          l2c[g.key] = computeFahpWeights(keys, this.fahpLevel2Matrices[g.key] || {}).consistency
        }
      })
      this.fahpLevel2Consistency = l2c
    },
    applyFahpWeights (showMsg = true) {
      this.fahpComputing = true
      try {
        this.fahpLevel1Matrix = normalizePairMatrix(this.fahpLevel1Matrix, LEVEL1_ORDER)
        INDICATOR_TREE.forEach(g => {
          if (g.children.length >= 2) {
            const keys = g.children.map(c => c.key)
            this.$set(
              this.fahpLevel2Matrices,
              g.key,
              normalizePairMatrix(this.fahpLevel2Matrices[g.key] || {}, keys)
            )
          }
        })
        const r1 = computeFahpWeights(LEVEL1_ORDER, this.fahpLevel1Matrix)
        this.fahpLevel1Consistency = r1.consistency
        this.applyWeightObject(this.level1Weights, r1.weights, LEVEL1_ORDER)

        const l2c = {}
        INDICATOR_TREE.forEach(g => {
          const childKeys = g.children.map(c => c.key)
          if (childKeys.length < 2) {
            if (childKeys.length === 1) {
              this.$set(this.level2Weights[g.key], childKeys[0], 1)
            }
            return
          }
          const matrix = this.fahpLevel2Matrices[g.key] || createEmptyPairMatrix(childKeys)
          const r2 = computeFahpWeights(childKeys, matrix)
          l2c[g.key] = r2.consistency
          this.applyWeightObject(this.level2Weights[g.key], r2.weights, childKeys)
        })
        this.fahpLevel2Consistency = l2c

        const badCr = []
        if (!r1.consistency.acceptable) badCr.push('一级指标')
        INDICATOR_TREE.forEach(g => {
          const c = l2c[g.key]
          if (c && !c.acceptable) badCr.push(g.title)
        })
        if (showMsg) {
          if (badCr.length) {
            this.$message.warning(`FAHP 权重已应用，但 ${badCr.join('、')} 的 CR>0.1，建议调整判断矩阵`)
          } else {
            this.$message.success('FAHP 权重已计算并应用')
          }
        }
      } catch (e) {
        this.$message.error('FAHP 计算失败：' + (e.message || '未知错误'))
      } finally {
        this.fahpComputing = false
      }
    },
    resetFahpMatrices () {
      const init = initFahpMatrices()
      this.fahpLevel1Matrix = init.level1
      this.fahpLevel2Matrices = init.level2
      this.fahpLevel1Consistency = null
      this.fahpLevel2Consistency = {}
      this.applyFahpWeights()
    },
    resetDefaultWeights () {
      const d = getDefaultWeights()
      this.level1Weights = { ...d.level1 }
      this.level2Weights = JSON.parse(JSON.stringify(d.level2))
      this.weightMode = 'manual'
      this.$message.success('已恢复内置默认权重')
    },
    // 暂不使用：保存权重为默认模板
    // saveWeightTemplate () {
    //   if (!this.level1SumOk) {
    //     this.$message.warning('一级权重之和须为 1')
    //     return
    //   }
    //   const bad = INDICATOR_TREE.find(g => !this.level2SumOk[g.key])
    //   if (bad) {
    //     this.$message.warning(`${bad.title} 的二级权重之和须为 1`)
    //     return
    //   }
    //   if (this.weightMode === 'fahp') {
    //     this.applyFahpWeights(false)
    //   }
    //   saveWeights(this.level1Weights, this.level2Weights, {
    //     weightMode: this.weightMode,
    //     fahpLevel1Matrix: this.fahpLevel1Matrix,
    //     fahpLevel2Matrices: this.fahpLevel2Matrices
    //   })
    //   this.$message.success('权重模板已保存，下次打开将自动加载')
    // },
    validateForm () {
      const errors = {}
      let hasErr = false
      INDICATOR_TREE.forEach(g => {
        errors[g.key] = {}
        g.children.forEach(field => {
          const gv = this.formValues[g.key]
          const msg = validateIndicatorInput(
            field,
            (field.inputType === 'ratioSum' || field.inputType === 'derivedFormula') ? undefined : gv[field.key],
            gv
          )
          if (msg) {
            errors[g.key][field.key] = msg
            hasErr = true
          }
        })
      })
      this.fieldErrors = errors
      return !hasErr
    },
    runEvaluation () {
      if (!this.wellId) {
        this.$message.warning('请选择待钻井')
        return
      }
      if (this.weightMode === 'fahp') {
        this.applyFahpWeights(false)
      }
      if (!this.level1SumOk) {
        this.$message.warning('一级指标权重之和须等于 1')
        return
      }
      const badL2 = INDICATOR_TREE.find(g => !this.level2SumOk[g.key])
      if (badL2) {
        this.$message.warning(`「${badL2.title}」下二级权重之和须等于 1`)
        return
      }
      if (!this.validateForm()) {
        this.$message.warning('请修正标红的指标录入项')
        return
      }
      this.calculating = true
      try {
        const res = runTrajectoryEvaluation(this.formValues, {
          level1: this.level1Weights,
          level2: this.level2Weights
        })
        res.secondaryResults = res.secondaryResults.map((r, i) => ({
          ...r,
          rowKey: `${r.groupKey}-${r.key}-${i}`
        }))
        this.result = res
        this.$nextTick(() => this.renderResultCharts())
        this.$message.success('评价完成')
      } catch (e) {
        this.$message.error('计算失败：' + (e.message || '未知错误'))
      } finally {
        this.calculating = false
      }
    },
    formatMu (v) {
      return (Number(v) || 0).toFixed(4)
    },
    fieldLabel (field) {
      const unit = field.unit ? ` (${field.unit})` : ''
      return `${field.label}${unit}`
    },
    formatComputedPreview (groupKey, field) {
      const v = resolveIndicatorRawValue(field, this.formValues[groupKey] || {})
      if (!Number.isFinite(v)) return ''
      return v.toFixed(4)
    },
    numberInputMax (field) {
      return field.max != null && Number.isFinite(Number(field.max)) ? field.max : undefined
    },
    numberInputPlaceholder (field) {
      if (field.minExclusive) {
        return `> ${field.min != null ? field.min : 0}`
      }
      if (field.max != null && Number.isFinite(Number(field.max))) {
        return `${field.min} ~ ${field.max}`
      }
      return field.min != null ? `≥ ${field.min}` : '请输入数值'
    },
    disposeCharts () {
      ;['scoreBarChart', 'membershipRadarChart', 'compositeBarChart'].forEach(ref => {
        if (this[ref]) {
          this[ref].dispose()
          this[ref] = null
        }
      })
    },
    renderResultCharts () {
      if (!this.result) return
      this.disposeCharts()
      const titles = this.result.level1Results.map(r => r.title)
      const scores = this.result.level1Results.map(r => r.score100)

      const barEl = this.$refs.scoreBarChart
      if (barEl) {
        this.scoreBarChart = echarts.init(barEl)
        this.scoreBarChart.setOption({
          tooltip: { trigger: 'axis' },
          grid: { left: 48, right: 16, top: 24, bottom: 80 },
          xAxis: { type: 'category', data: titles, axisLabel: { rotate: 30, fontSize: 10 } },
          yAxis: { type: 'value', name: '分', max: 100 },
          series: [{ type: 'bar', data: scores, itemStyle: { color: '#1890ff' } }]
        })
      }

      const radarEl = this.$refs.membershipRadarChart
      if (radarEl) {
        this.membershipRadarChart = echarts.init(radarEl)
        const muE = this.result.level1Results.map(r => r.membership[0])
        const muQ = this.result.level1Results.map(r => r.membership[1])
        const muU = this.result.level1Results.map(r => r.membership[2])
        this.membershipRadarChart.setOption({
          tooltip: {},
          legend: { bottom: 0, data: ['优秀', '合格', '不合格'] },
          radar: {
            indicator: titles.map(t => ({ name: t, max: 1 }))
          },
          series: [{
            type: 'radar',
            data: [
              { name: '优秀', value: muE },
              { name: '合格', value: muQ },
              { name: '不合格', value: muU }
            ]
          }]
        })
      }

      const compEl = this.$refs.compositeBarChart
      if (compEl) {
        this.compositeBarChart = echarts.init(compEl)
        const cm = this.result.compositeMembership.vector
        this.compositeBarChart.setOption({
          tooltip: { trigger: 'axis' },
          grid: { left: 48, right: 16, top: 24, bottom: 40 },
          xAxis: { type: 'category', data: ['优秀', '合格', '不合格'] },
          yAxis: { type: 'value', name: '隶属度', max: 1 },
          series: [{
            type: 'bar',
            data: cm,
            itemStyle: {
              color: (p) => (['#52c41a', '#faad14', '#f5222d'][p.dataIndex])
            }
          }]
        })
      }
    },
    exportExcel () {
      if (!this.result || !XLSX) {
        this.$message.warning('无结果可导出')
        return
      }
      const well = this.wellOptions.find(w => w.key === this.wellId)
      const rows = [
        ['井眼轨迹综合评价结果'],
        ['井场ID', this.siteId],
        ['待评价井', well ? well.label : this.wellId],
        ['最终等级', this.result.finalGrade],
        ['综合隶属度-优秀', this.result.compositeMembership.excellent],
        ['综合隶属度-合格', this.result.compositeMembership.qualified],
        ['综合隶属度-不合格', this.result.compositeMembership.unqualified],
        [],
        ['一级指标', '一级权重', '得分0-10', '得分0-100', '优秀隶属度', '合格隶属度', '不合格隶属度']
      ]
      this.result.level1Results.forEach(r => {
        rows.push([r.title, r.weight, r.score10, r.score100, r.membership[0], r.membership[1], r.membership[2]])
      })
      rows.push([])
      rows.push(['二级指标', '一级指标', '录入值', '得分0-10'])
      this.result.secondaryResults.forEach(r => {
        rows.push([r.label, r.groupTitle, r.rawValue, r.score10])
      })
      const ws = XLSX.utils.aoa_to_sheet(rows)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '评价结果')
      const name = `井眼轨迹综合评价_${well ? well.label : this.wellId}_${Date.now()}.xlsx`
      XLSX.writeFile(wb, name.replace(/[/\\?*|:]/g, '_'))
      this.$message.success('已导出')
    }
  }
}
</script>

<style lang="less" scoped>
.trajectory-quality-eval {
  .section-card {
    margin-bottom: 16px;
  }
  .algo-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    max-width: 520px;
  }
  .algo-label {
    flex-shrink: 0;
    width: 100px;
    margin-right: 8px;
  }
  .algo-input-inner {
    flex: 1;
    max-width: 360px;
  }
  .weight-mode-switch {
    margin-bottom: 12px;
  }
  .weight-actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 12px;
  }
  .fahp-section-title,
  .weight-result-label {
    font-weight: 600;
    font-size: 13px;
    margin: 12px 0 8px;
    color: rgba(0, 0, 0, 0.85);
  }
  .fahp-single-hint {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    padding: 4px 0;
  }
  .fahp-l2-collapse {
    margin-top: 8px;
  }
  .weight-sum.ok { color: #52c41a; }
  .weight-sum.err { color: #f5222d; }
  .sum-ok { color: #52c41a; font-size: 12px; }
  .sum-err { color: #f5222d; font-size: 12px; }
  .level1-weights { margin-bottom: 8px; }
  .weight-item {
    margin-bottom: 8px;
  }
  .weight-label {
    display: block;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.65);
    margin-bottom: 4px;
  }
  &.indicator-entry-card {
    ::v-deep .ant-card-body {
      padding-top: 12px;
    }
  }
  .indicator-group {
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    background: #fafafa;
    padding: 12px 16px 4px;
    margin-bottom: 16px;
  }
  .indicator-group-title {
    font-weight: 600;
    font-size: 14px;
    color: rgba(0, 0, 0, 0.85);
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8e8e8;
  }
  .indicator-row {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 8px 16px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    &:last-child {
      border-bottom: none;
    }
    &--error .indicator-row-label {
      color: #f5222d;
    }
  }
  .indicator-row-label {
    flex: 0 0 220px;
    max-width: 100%;
    font-size: 13px;
    line-height: 32px;
    color: rgba(0, 0, 0, 0.85);
  }
  .indicator-row-body {
    flex: 1;
    min-width: 200px;
  }
  .computed-field {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .computed-value {
    font-size: 16px;
    font-weight: 600;
    color: #1890ff;
    line-height: 32px;
  }
  .computed-pending {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.25);
    line-height: 32px;
  }
  .computed-desc,
  .manual-hint {
    flex: 1 1 100%;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    line-height: 1.5;
    margin-top: 2px;
  }
  .computed-error {
    flex: 1 1 100%;
    font-size: 12px;
    color: #f5222d;
    line-height: 1.4;
  }
  .ratio-sum-block {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ratio-sum-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
  }
  .ratio-sum-label {
    flex: 0 0 140px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.65);
    line-height: 32px;
  }
  .ratio-sum-input {
    min-width: 160px;
  }
  .ratio-preview {
    font-size: 13px;
    font-weight: 600;
    color: #1890ff;
    line-height: 1.5;
  }
  .composite-weight {
    margin-left: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.35);
    font-weight: normal;
  }
  .auto-tag {
    margin: 0;
  }
  .indicator-control {
    width: 100% !important;
    max-width: 280px;
  }
  ::v-deep .indicator-control.ant-input-number {
    width: 100% !important;
    max-width: 280px;
  }
  ::v-deep .indicator-control.ant-select {
    width: 100% !important;
    max-width: 280px;
  }
  .calc-row {
    text-align: center;
    margin-top: 8px;
  }
  .final-grade {
    font-size: 16px;
  }
  .chart-title {
    font-weight: 500;
    margin-bottom: 8px;
  }
  .result-chart {
    width: 100%;
    height: 280px;
  }
  .composite-chart {
    height: 220px;
    max-width: 480px;
  }
}
</style>
