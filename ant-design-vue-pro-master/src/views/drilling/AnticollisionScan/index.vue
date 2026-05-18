<template>
  <page-header-wrapper>
    <template v-slot:content>
      对井轨迹进行多维度评估，包括防碰扫描等评估项。
    </template>

    <!-- 评估标签页 -->
    <a-card :bordered="false" class="evaluation-tabs">
      <a-tabs v-model:activeKey="activeTab" class="evaluation-tabs-inner">
        <a-tab-pane key="anticollision" tab="防碰扫描">
          <a-card :bordered="false" class="scan-form">
            <div class="algo-row">
              <label class="algo-label">井场：</label>
              <div class="algo-input">
                <a-select v-model="form.siteId" placeholder="请选择井场" class="algo-input-inner" @change="onSiteChange">
                  <a-select-option v-for="site in siteList" :key="site.id" :value="site.id">{{ site.name }}</a-select-option>
                </a-select>
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label">待扫描轨迹（待钻井）：</label>
              <div class="algo-input">
                <a-select v-model="form.trajectoryId" placeholder="请先选择井场" class="algo-input-inner algo-input-full" :disabled="!form.siteId">
                  <a-select-option v-for="well in availableWells" :key="well.id" :value="well.id">{{ well.wellNo }} - {{ well.name }}</a-select-option>
                </a-select>
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label">邻井（多选）：</label>
              <div class="algo-input">
                <a-select
                  v-model="form.neighborWellIds"
                  mode="multiple"
                  placeholder="请先选择井场"
                  class="algo-input-inner algo-input-full"
                  :disabled="!form.siteId"
                >
                  <a-select-option v-for="w in neighborWellOptions" :key="w.id" :value="w.id">{{ w.name }} ({{ w.wellNo }})</a-select-option>
                </a-select>
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label">防碰分析方法：</label>
              <div class="algo-input">
                <a-select v-model="form.anticollisionMethod" placeholder="请选择" class="algo-input-inner">
                  <a-select-option value="CTC">CTC 井眼中心距法</a-select-option>
                  <a-select-option value="SF">SF 分离系数法</a-select-option>
                </a-select>
              </div>
            </div>
            <div v-if="form.anticollisionMethod === 'CTC'" class="algo-row">
              <label class="algo-label">最小安全半径(m)：</label>
              <div class="algo-input">
                <a-input-number v-model="form.safeRadius" :min="1" :max="50" class="algo-input-inner" placeholder="如 10" />
              </div>
            </div>
            <div v-else class="algo-row">
              <label class="algo-label">最小 SF：</label>
              <div class="algo-input">
                <a-input-number
                  v-model="form.minSafetyFactor"
                  :min="1"
                  :max="3"
                  :step="0.1"
                  class="algo-input-inner"
                  placeholder="如 1.2"
                />
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label"></label>
              <div class="algo-input">
                <a-button type="primary" :loading="scanLoading" icon="search" @click="runScan">执行扫描</a-button>
              </div>
            </div>

            <a-divider v-if="scanResult">扫描结果</a-divider>
            <template v-if="scanResult">
              <a-alert
                :message="resultAlertMessage"
                :type="scanResult.riskLevel === '安全' ? 'success' : scanResult.riskLevel === '预警' ? 'warning' : 'error'"
                show-icon
                style="margin-bottom: 16px"
              />
              <a-table
                :columns="resultColumns"
                :data-source="scanResult.segments"
                :pagination="false"
                size="small"
                row-key="segment"
              >
                <span slot="risk" slot-scope="text">
                  <a-tag :color="text === '安全' ? 'green' : text === '预警' ? 'orange' : 'red'">{{ text }}</a-tag>
                </span>
              </a-table>
              <div style="margin-top: 16px">
                <a-button icon="file-pdf" @click="exportReport">导出防碰扫描报告</a-button>
              </div>

              <div class="viz-section">
                <a-divider orientation="left">防碰 3D 可视化（可拖动旋转视角）</a-divider>
                <div v-if="viz3dError" class="viz-error">{{ viz3dError }}</div>
                <div v-else ref="chart3dContainer" class="chart3d-container" />
              </div>
            </template>
          </a-card>
        </a-tab-pane>
        <a-tab-pane key="trajectory" tab="轨迹质量评估">
          <a-card :bordered="false" class="quality-form">
            <div class="algo-row">
              <label class="algo-label">待评估轨迹：</label>
              <div class="algo-input">
                <a-select v-model="qualityForm.trajectoryId" placeholder="请选择轨迹" class="algo-input-inner algo-input-full">
                  <a-select-option v-for="well in availableWells" :key="well.id" :value="well.id">{{ well.wellNo }} - {{ well.name }}</a-select-option>
                </a-select>
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label"></label>
              <div class="algo-input">
                <a-button type="primary" :loading="qualityLoading" icon="check-circle" @click="runQualityEvaluation">执行评估</a-button>
              </div>
            </div>
            <a-divider v-if="qualityResult">评估结果</a-divider>
            <template v-if="qualityResult">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="总狗腿度">
                  <a-tag :color="qualityResult.doglegScore >= 80 ? 'green' : qualityResult.doglegScore >= 60 ? 'orange' : 'red'">
                    {{ qualityResult.doglegScore }}分
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="井眼平滑度">
                  <a-tag :color="qualityResult.smoothScore >= 80 ? 'green' : qualityResult.smoothScore >= 60 ? 'orange' : 'red'">
                    {{ qualityResult.smoothScore }}分
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="靶点命中率">
                  <a-tag :color="qualityResult.targetScore >= 80 ? 'green' : qualityResult.targetScore >= 60 ? 'orange' : 'red'">
                    {{ qualityResult.targetScore }}分
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="综合评分">
                  <a-tag :color="qualityResult.totalScore >= 80 ? 'green' : qualityResult.totalScore >= 60 ? 'orange' : 'red'">
                    {{ qualityResult.totalScore }}分
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </template>
          </a-card>
        </a-tab-pane>
        <a-tab-pane key="economic" tab="经济效益评估">
          <a-card :bordered="false" class="economic-form">
            <div class="algo-row">
              <label class="algo-label">待评估轨迹：</label>
              <div class="algo-input">
                <a-select v-model="economicForm.trajectoryId" placeholder="请选择轨迹" class="algo-input-inner algo-input-full">
                  <a-select-option v-for="well in availableWells" :key="well.id" :value="well.id">{{ well.wellNo }} - {{ well.name }}</a-select-option>
                </a-select>
              </div>
            </div>
            <div class="algo-row">
              <label class="algo-label"></label>
              <div class="algo-input">
                <a-button type="primary" :loading="economicLoading" icon="dollar" @click="runEconomicEvaluation">执行评估</a-button>
              </div>
            </div>
            <a-divider v-if="economicResult">评估结果</a-divider>
            <template v-if="economicResult">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="预估钻井成本">¥ {{ economicResult.cost.toLocaleString() }}</a-descriptions-item>
                <a-descriptions-item label="预期产量">{{ economicResult.production }} 吨/日</a-descriptions-item>
                <a-descriptions-item label="投资回报率">{{ economicResult.roi }}%</a-descriptions-item>
                <a-descriptions-item label="回收期">{{ economicResult.paybackPeriod }} 月</a-descriptions-item>
              </a-descriptions>
            </template>
          </a-card>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </page-header-wrapper>
</template>

<script>
import * as echarts from 'echarts'
import 'echarts-gl'
import * as XLSXModule from 'xlsx'
import { drillingAPI } from '@/api'

const XLSX = XLSXModule.default || XLSXModule

function minimumCurvatureToEND (rows, wellhead) {
  const [x0, y0, z0] = wellhead
  const out = [[x0, y0, z0]]
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
    out.push([prev[0] + dE, prev[1] + dN, prev[2] + dD])
  }
  return out
}

export default {
  name: 'TrajectoryEvaluation',
  data () {
    return {
      activeTab: 'anticollision',
      siteList: [],
      wellList: [],
      form: {
        siteId: undefined,
        trajectoryId: undefined,
        neighborWellIds: [],
        anticollisionMethod: 'SF',
        safeRadius: 10,
        minSafetyFactor: 1.2
      },
      qualityForm: {
        trajectoryId: undefined
      },
      economicForm: {
        trajectoryId: undefined
      },
      scanLoading: false,
      scanResult: null,
      viz3dError: '',
      chart3d: null,
      qualityLoading: false,
      qualityResult: null,
      economicLoading: false,
      economicResult: null,
      resultColumns: [
        { title: '井段', dataIndex: 'segment', key: 'segment' },
        { title: '最小距离(m)', dataIndex: 'minDist', key: 'minDist' },
        { title: '最小SF', dataIndex: 'minSF', key: 'minSF' },
        { title: '风险等级', dataIndex: 'risk', key: 'risk', scopedSlots: { customRender: 'risk' } }
      ]
    }
  },
  computed: {
    availableWells () {
      if (!this.form.siteId) return []
      return this.wellList.filter(w => w.siteId === this.form.siteId && w.type === 'planned')
    },
    neighborWellOptions () {
      if (!this.form.siteId) return []
      return this.wellList.filter(w => w.siteId === this.form.siteId && w.type === 'existing')
    },
    resultAlertMessage () {
      if (!this.scanResult) return ''
      if (this.form.anticollisionMethod === 'CTC') {
        return `最小井眼中心距：${this.scanResult.minDistance} m | 风险等级：${this.scanResult.riskLevel} | 最近点深度：${this.scanResult.nearestDepth} m`
      } else {
        return `最小SF：${this.scanResult.minSafetyFactor} | 风险等级：${this.scanResult.riskLevel} | 最近点深度：${this.scanResult.nearestDepth} m`
      }
    }
  },
  created () {
    this.loadSiteList()
  },
  beforeDestroy () {
    if (this.chart3d) {
      this.chart3d.dispose()
      this.chart3d = null
    }
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
        console.error('加载井场列表失败:', e)
        this.$message.error('加载井场失败：' + (e.message || '未知错误'))
      }
    },
    async loadWellsBySite (siteId) {
      try {
        const [existingRes, pendingRes] = await Promise.all([
          drillingAPI.getWellsBySite(siteId),
          drillingAPI.getPendingDrillWellsBySite(siteId)
        ])
        const existingWells = this.normalizeListResponse(existingRes).map(w => ({
          id: w.id,
          siteId: w.siteId,
          wellNo: w.wellNo,
          name: w.name,
          wellheadE: w.wellheadE,
          wellheadN: w.wellheadN,
          wellheadD: w.wellheadD,
          type: 'existing'
        }))
        const pendingWells = this.normalizeListResponse(pendingRes).map(w => ({
          id: w.id,
          siteId: w.siteId,
          wellNo: w.wellNo,
          name: w.name,
          wellheadE: w.wellheadE,
          wellheadN: w.wellheadN,
          wellheadD: w.wellheadD,
          type: 'planned'
        }))
        this.wellList = [...existingWells, ...pendingWells]
      } catch (e) {
        console.error('加载井列表失败:', e)
        this.$message.error('加载井列表失败：' + (e.message || '未知错误'))
      }
    },
    onSiteChange () {
      this.form.trajectoryId = undefined
      this.form.neighborWellIds = []
      this.scanResult = null
      if (this.form.siteId) {
        this.loadWellsBySite(this.form.siteId)
      }
    },
    async runScan () {
      if (!this.form.siteId || !this.form.trajectoryId || !this.form.neighborWellIds.length) {
        this.$message.warning('请选择井场、待扫描轨迹和至少一口邻井')
        return
      }
      this.scanLoading = true
      this.scanResult = null
      this.viz3dError = ''
      if (this.chart3d) {
        this.chart3d.dispose()
        this.chart3d = null
      }
      try {
        const params = {
          siteId: this.form.siteId,
          trajectoryId: this.form.trajectoryId,
          neighborWellIds: this.form.neighborWellIds.map(id => Number(id)),
          anticollisionMethod: this.form.anticollisionMethod,
          safeRadius: this.form.safeRadius,
          minSafetyFactor: this.form.minSafetyFactor
        }
        const res = await drillingAPI.anticollisionScan(params)
        console.log('扫描结果:', res)
        if (res) {
          this.scanResult = res.data || res
          this.$message.success('扫描完成')
          this.$nextTick(() => this.renderTrajectoryChart())
        } else {
          this.$message.error('扫描结果为空')
        }
      } catch (e) {
        console.error('防碰扫描失败:', e)
        this.$message.error('防碰扫描失败: ' + (e.message || '未知错误'))
      } finally {
        this.scanLoading = false
      }
    },
    runQualityEvaluation () {
      if (!this.qualityForm.trajectoryId) {
        this.$message.warning('请选择待评估轨迹')
        return
      }
      this.qualityLoading = true
      setTimeout(() => {
        this.qualityResult = {
          doglegScore: 85,
          smoothScore: 92,
          targetScore: 88,
          totalScore: 88
        }
        this.qualityLoading = false
        this.$message.success('评估完成')
      }, 1000)
    },
    runEconomicEvaluation () {
      if (!this.economicForm.trajectoryId) {
        this.$message.warning('请选择待评估轨迹')
        return
      }
      this.economicLoading = true
      setTimeout(() => {
        this.economicResult = {
          cost: 12500000,
          production: 500,
          roi: 28.5,
          paybackPeriod: 36
        }
        this.economicLoading = false
        this.$message.success('评估完成')
      }, 1000)
    },
    exportReport () {
      this.$message.success('防碰扫描报告导出中（模拟 PDF/Word）')
    },
    parseExcelToPoints (buf, wellhead) {
      if (!XLSX || typeof XLSX.read !== 'function') return null
      const wb = XLSX.read(new Uint8Array(buf), { type: 'array' })
      const sheet = wb.Sheets[wb.SheetNames[0]]
      const json = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
      if (!json || !json.length) return null
      const rows = []
      for (let i = 0; i < json.length; i++) {
        const r = json[i]
        const md = Number(r[0])
        const inc = Number(r[1])
        const azi = Number(r[2])
        if (Number.isNaN(md) && Number.isNaN(inc) && Number.isNaN(azi)) continue
        rows.push({ md: md || 0, inclination: inc || 0, azimuth: azi || 0 })
      }
      if (!rows.length) return null
      const head = [wellhead.wellheadE, wellhead.wellheadN, wellhead.wellheadD]
      return minimumCurvatureToEND(rows, head)
    },
    fetchXlsx (wellNo) {
      const urls = [`/optimization/${wellNo}.xlsx`, `/${wellNo}.xlsx`]
      let p = Promise.reject(new Error('404'))
      urls.forEach(url => {
        p = p.catch(() => fetch(url).then(res => (res.ok ? res.arrayBuffer() : Promise.reject(new Error('404')))))
      })
      return p
    },
    renderTrajectoryChart () {
      const el = this.$refs.chart3dContainer
      if (!el) return
      if (!this.scanResult || !this.scanResult.trajectories) {
        this.viz3dError = '没有轨迹数据'
        return
      }
      this.viz3dError = ''
      if (this.chart3d) this.chart3d.dispose()
      this.chart3d = echarts.init(el)

      const trajectories = this.scanResult.trajectories
      const colors = ['#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#faad14', '#f5222d']

      const series = trajectories.map((traj, i) => {
        const color = colors[i % colors.length]
        const points = traj.trajectory_points || []
        const data = points.map(p => [p.x || p.e || 0, p.y || p.n || 0, -(p.z || p.d || 0)])
        return {
          type: 'line3D',
          name: traj.wellName || traj.wellNo || '井' + (i + 1),
          data,
          lineStyle: { width: i === 0 ? 4 : 2, color, opacity: i === 0 ? 1 : 0.7 },
          itemStyle: { opacity: 0.8 }
        }
      })

      const legendData = trajectories.map(t => t.wellName || t.wellNo || '井' + (trajectories.indexOf(t) + 1))
      const option = {
        tooltip: {},
        legend: { data: legendData, bottom: 0 },
        backgroundColor: '#fff',
        xAxis3D: { type: 'value', name: 'E' },
        yAxis3D: { type: 'value', name: 'N' },
        zAxis3D: { type: 'value', name: 'D' },
        grid3D: {
          viewControl: { autoRotate: false, rotateSensitivity: 1, zoomSensitivity: 1 },
          axisPointer: { show: true }
        },
        series
      }
      this.chart3d.setOption(option)
    }
  }
}
</script>

<style lang="less" scoped>
.evaluation-tabs {
  margin-top: 16px;
}
.evaluation-tabs-inner {
  margin-top: -16px;
}
.scan-form .algo-row,
.quality-form .algo-row,
.economic-form .algo-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.scan-form .algo-label,
.quality-form .algo-label,
.economic-form .algo-label {
  flex-shrink: 0;
  min-width: 180px;
  margin: 0;
  font-weight: normal;
  color: rgba(0, 0, 0, 0.85);
}
.scan-form .algo-input,
.quality-form .algo-input,
.economic-form .algo-input {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.scan-form .algo-input-inner,
.quality-form .algo-input-inner,
.economic-form .algo-input-inner {
  width: 100%;
  max-width: 280px;
}
.scan-form .algo-input-inner.algo-input-full,
.quality-form .algo-input-inner.algo-input-full,
.economic-form .algo-input-inner.algo-input-full {
  max-width: none;
}
.viz-section { margin-top: 24px; }
.viz-error { color: #ff4d4f; padding: 12px; }
.chart3d-container { width: 100%; height: 500px; }
</style>
