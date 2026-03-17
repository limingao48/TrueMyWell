<template>
  <page-header-wrapper>
    <template v-slot:content>
      对一条轨迹与多口邻井做防碰扫描，得到最小距离与风险提示。
    </template>
    <a-card :bordered="false" class="scan-form">
      <div class="algo-row">
        <label class="algo-label">待扫描轨迹：</label>
        <div class="algo-input">
          <a-select v-model="form.trajectoryId" placeholder="从已有设计选择或上传轨迹" class="algo-input-inner algo-input-full">
            <a-select-option value="design_1">最近设计：41-37YH3 靶点 (502.64, 2790.71, 2636.06)</a-select-option>
            <a-select-option value="design_2">设计：41-38YH1 靶点 (510, 2800, 2650)</a-select-option>
            <a-select-option value="upload">上传轨迹文件...</a-select-option>
          </a-select>
        </div>
      </div>
      <div class="algo-row">
        <label class="algo-label">邻井（多选）：</label>
        <div class="algo-input">
          <a-select
            v-model="form.neighborWellIds"
            mode="multiple"
            placeholder="从基础数据中选择邻井"
            class="algo-input-inner algo-input-full"
          >
            <a-select-option v-for="w in neighborWells" :key="w.id" :value="w.id">{{ w.name }} ({{ w.wellNo }})</a-select-option>
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
          :message="`最小距离：${scanResult.minDistance} m | 风险等级：${scanResult.riskLevel} | 最近点深度：${scanResult.nearestDepth} m`"
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

        <!-- 防碰 3D 可视化（可拖动旋转视角） -->
        <div class="viz-section">
          <a-divider orientation="left">防碰 3D 可视化（可拖动旋转视角）</a-divider>
          <div v-if="viz3dError" class="viz-error">{{ viz3dError }}</div>
          <div v-else ref="chart3dContainer" class="chart3d-container" />
        </div>
      </template>
    </a-card>
  </page-header-wrapper>
</template>

<script>
import * as echarts from 'echarts'
import 'echarts-gl'
import * as XLSXModule from 'xlsx'

const XLSX = XLSXModule.default || XLSXModule

// 邻井需含井口坐标用于轨迹 E,N,D 转换
const MOCK_NEIGHBOR_WELLS = [
  { id: 'n1', name: '41-37YH3', wellNo: '41-37YH3', wellheadE: 208, wellheadN: 2015, wellheadD: 0 },
  { id: 'n2', name: '41-37YH5', wellNo: '41-37YH5', wellheadE: 209, wellheadN: 2000, wellheadD: 0 },
  { id: 'n3', name: '41-38YH1', wellNo: '41-38YH1', wellheadE: 220, wellheadN: 2025, wellheadD: 0 }
]
// 待扫描轨迹 id -> 井号（用于从 public 拉取 xlsx）及井口
const DESIGN_TRAJECTORY_MAP = {
  design_1: { wellNo: '41-37YH3', wellheadE: 222, wellheadN: 2030, wellheadD: 0 },
  design_2: { wellNo: '41-38YH1', wellheadE: 220, wellheadN: 2025, wellheadD: 0 }
}
const MOCK_SCAN_RESULT = {
  minDistance: 12.5,
  riskLevel: '安全',
  nearestDepth: 1850,
  nearestPoint: { e: 350, n: 2100, d: 1850 },
  segments: [
    { segment: '0-500m', minDist: 120, risk: '安全' },
    { segment: '500-1000m', minDist: 85, risk: '安全' },
    { segment: '1000-1500m', minDist: 45, risk: '安全' },
    { segment: '1500-2000m', minDist: 15, risk: '预警' },
    { segment: '2000-2500m', minDist: 28, risk: '安全' }
  ]
}

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
  name: 'AnticollisionScan',
  data () {
    return {
      form: {
        trajectoryId: undefined,
        neighborWellIds: [],
        anticollisionMethod: 'SF',
        safeRadius: 10,
        minSafetyFactor: 1.2
      },
      neighborWells: MOCK_NEIGHBOR_WELLS,
      scanLoading: false,
      scanResult: null,
      viz3dError: '',
      chart3d: null,
      resultColumns: [
        { title: '井段', dataIndex: 'segment', key: 'segment' },
        { title: '最小距离(m)', dataIndex: 'minDist', key: 'minDist' },
        { title: '风险等级', dataIndex: 'risk', key: 'risk', scopedSlots: { customRender: 'risk' } }
      ]
    }
  },
  beforeDestroy () {
    if (this.chart3d) {
      this.chart3d.dispose()
      this.chart3d = null
    }
  },
  methods: {
    runScan () {
      if (!this.form.trajectoryId || !this.form.neighborWellIds.length) {
        this.$message.warning('请选择待扫描轨迹和至少一口邻井')
        return
      }
      this.scanLoading = true
      this.scanResult = null
      this.viz3dError = ''
      if (this.chart3d) {
        this.chart3d.dispose()
        this.chart3d = null
      }
      setTimeout(() => {
        this.scanResult = { ...MOCK_SCAN_RESULT }
        this.scanLoading = false
        this.$message.success('扫描完成')
        this.$nextTick(() => this.loadTrajectoriesAndRender3D())
      }, 1200)
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
    loadTrajectoriesAndRender3D () {
      const el = this.$refs.chart3dContainer
      if (!el) return
      this.viz3dError = ''
      const designInfo = DESIGN_TRAJECTORY_MAP[this.form.trajectoryId]
      if (!designInfo) {
        this.viz3dError = '当前选择的轨迹暂无轨迹文件，无法加载 3D。请选择「最近设计」或「设计：41-38YH1」或对接后端轨迹接口。'
        return
      }
      const neighborList = this.neighborWells.filter(w => this.form.neighborWellIds.includes(w.id))
      const loadDesign = this.fetchXlsx(designInfo.wellNo)
        .then(buf => this.parseExcelToPoints(buf, designInfo))
        .then(points => ({ wellNo: designInfo.wellNo + '（待扫描）', points }))
        .catch(() => null)
      const loadNeighbors = Promise.all(
        neighborList.map(w =>
          this.fetchXlsx(w.wellNo)
            .then(buf => this.parseExcelToPoints(buf, w))
            .then(points => ({ wellNo: w.wellNo, points }))
            .catch(() => null)
        )
      )
      Promise.all([loadDesign, loadNeighbors])
        .then(([designSeries, neighborResults]) => {
          const list = []
          if (designSeries && designSeries.points && designSeries.points.length) list.push(designSeries)
          neighborResults.forEach(r => { if (r && r.points && r.points.length) list.push(r) })
          if (!list.length) {
            this.viz3dError = '未加载到轨迹数据。请将对应井号 xlsx（如 41-37YH3.xlsx）放入 public 或 optimization 目录。'
            return
          }
          this.render3DChart(list)
        })
        .catch(() => {
          this.viz3dError = '加载轨迹文件失败'
        })
    },
    render3DChart (seriesList) {
      const el = this.$refs.chart3dContainer
      if (!el) return
      if (this.chart3d) this.chart3d.dispose()
      this.chart3d = echarts.init(el)
      const colors = ['#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#faad14', '#f5222d']
      const series = seriesList.map((item, i) => {
        const color = colors[i % colors.length]
        const data = item.points.map(p => [p[0], p[1], -p[2]])
        return {
          type: 'line3D',
          name: item.wellNo,
          data,
          lineStyle: { width: 3, color },
          itemStyle: { opacity: 0.8 }
        }
      })
      const option = {
        tooltip: {},
        legend: { data: seriesList.map(s => s.wellNo), bottom: 0 },
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
/* 与轨迹设计一致的左侧 label + 右侧输入 */
.scan-form .algo-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.scan-form .algo-label {
  flex-shrink: 0;
  min-width: 180px;
  margin: 0;
  font-weight: normal;
  color: rgba(0, 0, 0, 0.85);
}
.scan-form .algo-input {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.scan-form .algo-input-inner {
  width: 100%;
  max-width: 280px;
}
.scan-form .algo-input-inner.algo-input-full {
  max-width: none;
}
.viz-section { margin-top: 24px; }
.viz-error { color: #ff4d4f; padding: 12px; }
.chart3d-container { width: 100%; height: 500px; }
</style>
