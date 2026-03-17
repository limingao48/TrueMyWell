<template>
  <page-header-wrapper>
    <template v-slot:content>
      先管理井场，进入井场后对该井场下的井进行增删查；新增井需输入井口坐标并导入 Excel（测深(m)、井斜角(°)、网格方位(°)）。
    </template>
    <a-card :bordered="false">
      <!-- 井场列表（未进入某井场时） -->
      <div v-if="!currentSiteId">
        <div class="section-title">井场管理</div>
        <a-form layout="inline" style="margin-bottom: 16px">
          <a-form-item label="井场名称">
            <a-input v-model="siteQuery.name" placeholder="井场名称" allow-clear style="width: 160px" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="searchSites">查询</a-button>
            <a-button style="margin-left: 8px" @click="siteQuery = {}">重置</a-button>
            <a-button type="primary" icon="plus" style="margin-left: 8px" @click="openSiteModal()">新增井场</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="siteColumns"
          :data-source="filteredSiteList"
          :pagination="{ pageSize: 10, showSizeChanger: true }"
          row-key="id"
        >
          <span slot="action" slot-scope="text, record">
            <a @click="openSiteModal(record)">编辑</a>
            <a-divider type="vertical" />
            <a-popconfirm title="确定删除该井场？其下井数据将一并移除。" @confirm="deleteSite(record)">
              <a class="danger">删除</a>
            </a-popconfirm>
            <a-divider type="vertical" />
            <a @click="enterSite(record)">进入</a>
          </span>
        </a-table>
      </div>

      <!-- 已进入某井场：井列表、井口坐标、轨迹文件 -->
      <div v-else>
        <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
          <a-button type="link" style="padding-left: 0" @click="exitSite">
            <a-icon type="arrow-left" /> 返回井场列表
          </a-button>
          <a-button type="primary" icon="line-chart" :loading="vizLoading" @click="toggleVisualization">
            {{ showVisualization ? '收起可视化' : '井轨迹 3D 可视化' }}
          </a-button>
        </div>
        <div class="section-title">{{ currentSiteName }} — 井管理</div>
        <a-tabs default-active-key="wells">
          <a-tab-pane key="wells" tab="井列表">
            <a-form layout="inline" style="margin-bottom: 16px">
              <a-form-item label="井号">
                <a-input v-model="wellQuery.wellNo" placeholder="井号" allow-clear style="width: 140px" />
              </a-form-item>
              <a-form-item>
                <a-button type="primary" @click="searchWells">查询</a-button>
                <a-button style="margin-left: 8px" @click="wellQuery = {}">重置</a-button>
                <a-button type="primary" icon="plus" style="margin-left: 8px" @click="openAddWellDrawer()">新增井</a-button>
              </a-form-item>
            </a-form>
            <a-table
              :columns="wellColumns"
              :data-source="filteredWellList"
              :pagination="{ pageSize: 10, showSizeChanger: true }"
              row-key="id"
            >
              <span slot="action" slot-scope="text, record">
                <a @click="openEditWellModal(record)">编辑</a>
                <a-divider type="vertical" />
                <a-popconfirm title="确定删除？可能影响已有设计与扫描记录。" @confirm="deleteWell(record)">
                  <a class="danger">删除</a>
                </a-popconfirm>
              </span>
            </a-table>
          </a-tab-pane>

          <a-tab-pane key="neighbor" tab="井轨迹文件">
            <a-upload
              :before-upload="beforeUploadTrajectory"
              accept=".xlsx,.xls"
              style="margin-bottom: 16px"
            >
              <a-button icon="upload">上传轨迹文件</a-button>
            </a-upload>
            <a-table
              :columns="neighborFileColumns"
              :data-source="filteredNeighborFileList"
              :pagination="{ pageSize: 10 }"
              row-key="id"
            >
              <span slot="wellNo" slot-scope="text, record">{{ record.wellNo || '-' }}</span>
              <span slot="action" slot-scope="text, record">
                <a @click="downloadTrajectory(record)">下载</a>
                <a-divider type="vertical" />
                <a @click="openLinkWellModal(record)">关联井</a>
                <a-divider type="vertical" />
                <a-popconfirm title="确定删除该轨迹文件？" @confirm="deleteTrajectory(record)">
                  <a class="danger">删除</a>
                </a-popconfirm>
              </span>
            </a-table>
          </a-tab-pane>
        </a-tabs>

        <!-- 井轨迹 3D 可视化（当前页下方） -->
        <div v-if="showVisualization" class="viz-section">
          <a-divider orientation="left">井轨迹 3D 可视化（可拖动旋转视角）</a-divider>
          <div v-if="vizError" class="viz-error">{{ vizError }}</div>
          <div v-else ref="chart3dContainer" class="chart3d-container" />
        </div>
      </div>

      <!-- 井场 新增/编辑 弹窗 -->
      <a-modal
        v-model="siteModalVisible"
        :title="siteForm.id ? '编辑井场' : '新增井场'"
        width="520px"
        @ok="saveSite"
      >
        <p class="modal-desc">{{ siteForm.id ? '修改井场名称或编号，其下井数据保持不变。' : '新建井场后，可进入该井场管理井与轨迹文件。' }}</p>
        <a-form-model ref="siteFormRef" :model="siteForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }" class="compact-form">
          <a-form-model-item label="井场名称" required>
            <a-input v-model="siteForm.name" placeholder="如：A 井场、XX 区块井场" class="input-narrow" />
          </a-form-model-item>
          <a-form-model-item label="井场编号">
            <a-input v-model="siteForm.code" placeholder="可选，如 A、B 或编码" class="input-narrow" />
          </a-form-model-item>
        </a-form-model>
      </a-modal>

      <!-- 井 编辑 弹窗 -->
      <a-modal
        v-model="wellModalVisible"
        title="编辑井信息"
        width="560px"
        @ok="saveWell"
      >
        <p class="modal-desc">修改该井的基本信息、井口坐标与井径，保存后立即生效。</p>
        <a-form-model ref="wellFormRef" :model="wellForm" :label-col="{ span: 7 }" :wrapper-col="{ span: 16 }" class="compact-form">
          <a-divider orientation="left" class="form-divider">基本信息</a-divider>
          <a-form-model-item label="井号" required>
            <a-input v-model="wellForm.wellNo" placeholder="如 41-37YH3，唯一标识" class="input-narrow" />
          </a-form-model-item>
          <a-form-model-item label="井名">
            <a-input v-model="wellForm.name" placeholder="井的显示名称，可选" class="input-narrow" />
          </a-form-model-item>
          <a-divider orientation="left" class="form-divider">井口坐标（米）</a-divider>
          <a-form-model-item label="井口东坐标 E">
            <a-input-number v-model="wellForm.wellheadE" class="input-narrow" placeholder="东向坐标 (E)" />
          </a-form-model-item>
          <a-form-model-item label="井口北坐标 N">
            <a-input-number v-model="wellForm.wellheadN" class="input-narrow" placeholder="北向坐标 (N)" />
          </a-form-model-item>
          <a-form-model-item label="井口海拔 D">
            <a-input-number v-model="wellForm.wellheadD" class="input-narrow" placeholder="海拔/垂深 (D)" />
          </a-form-model-item>
          <a-divider orientation="left" class="form-divider">井身参数</a-divider>
          <a-form-model-item label="井径">
            <a-input-number v-model="wellForm.wellDiameter" :min="0" class="input-narrow" placeholder="井径，单位：米 (m)" />
          </a-form-model-item>
        </a-form-model>
      </a-modal>

      <!-- 轨迹文件 关联井 弹窗 -->
      <a-modal
        v-model="linkWellModalVisible"
        title="关联井"
        width="480px"
        @ok="saveLinkWell"
      >
        <p class="modal-desc">将该轨迹文件关联到当前井场下的一口井，便于 3D 可视化与防碰扫描时识别。</p>
        <a-form-model :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }" class="compact-form">
          <a-form-model-item label="选择井号">
            <a-select
              v-model="linkWellNo"
              placeholder="选择要关联的井（可清空解除关联）"
              allow-clear
              class="input-narrow"
            >
              <a-select-option v-for="w in currentWellList" :key="w.id" :value="w.wellNo">{{ w.wellNo }} {{ w.name && w.name !== w.wellNo ? `（${w.name}）` : '' }}</a-select-option>
            </a-select>
          </a-form-model-item>
        </a-form-model>
      </a-modal>

      <!-- 新增井：井口坐标 + 导入轨迹 Excel -->
      <a-drawer
        title="新增井"
        :width="560"
        :visible="addWellDrawerVisible"
        :body-style="{ paddingBottom: '80px' }"
        @close="addWellDrawerVisible = false"
      >
        <a-alert
          message="请填写井号与井口坐标，并上传轨迹 Excel。Excel 须包含三列（无表头）：测深(m)、井斜角(°)、网格方位(°)。"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />
        <a-form-model :model="addWellForm" :label-col="{ span: 7 }" :wrapper-col="{ span: 16 }" class="compact-form">
          <a-divider orientation="left" class="form-divider">基本信息</a-divider>
          <a-form-model-item label="井号" required>
            <a-input v-model="addWellForm.wellNo" placeholder="如 41-37YH3，唯一标识" class="input-narrow" />
          </a-form-model-item>
          <a-form-model-item label="井名">
            <a-input v-model="addWellForm.name" placeholder="井的显示名称，可选" class="input-narrow" />
          </a-form-model-item>
          <a-divider orientation="left" class="form-divider">井口坐标（米）</a-divider>
          <a-form-model-item label="井口东坐标 E" required>
            <a-input-number v-model="addWellForm.wellheadE" class="input-narrow" placeholder="东向坐标" />
          </a-form-model-item>
          <a-form-model-item label="井口北坐标 N" required>
            <a-input-number v-model="addWellForm.wellheadN" class="input-narrow" placeholder="北向坐标" />
          </a-form-model-item>
          <a-form-model-item label="井口海拔 D" required>
            <a-input-number v-model="addWellForm.wellheadD" class="input-narrow" placeholder="海拔/垂深" />
          </a-form-model-item>
          <a-form-model-item label="井径">
            <a-input-number v-model="addWellForm.wellDiameter" :min="0" class="input-narrow" placeholder="井径，单位：米 (m)，可选" />
          </a-form-model-item>
          <a-divider orientation="left" class="form-divider">轨迹数据</a-divider>
          <a-form-model-item label="轨迹 Excel 文件" required>
            <a-upload
              :before-upload="beforeUploadWellExcel"
              :file-list="addWellForm.fileList"
              accept=".xlsx,.xls"
              @remove="addWellForm.fileList = []"
            >
              <a-button icon="upload">选择文件（测深(m)、井斜角(°)、网格方位(°)）</a-button>
            </a-upload>
            <div v-if="addWellForm.parseError" class="error-text">{{ addWellForm.parseError }}</div>
            <div v-if="addWellForm.parsePreview.length" class="preview-table">
              <div class="preview-title">解析预览（前 5 行）</div>
              <a-table
                :columns="excelPreviewColumns"
                :data-source="addWellForm.parsePreview"
                :pagination="false"
                size="small"
              />
            </div>
          </a-form-model-item>
        </a-form-model>
        <div class="drawer-footer">
          <a-button style="margin-right: 8px" @click="addWellDrawerVisible = false">取消</a-button>
          <a-button type="primary" :loading="addWellSubmitting" @click="submitAddWell">确定新增</a-button>
        </div>
      </a-drawer>
    </a-card>
  </page-header-wrapper>
</template>

<script>
import * as XLSXModule from 'xlsx'
import * as echarts from 'echarts'
import 'echarts-gl'
import { getWellTrajectoryExcel } from '@/api/drilling'

const XLSX = XLSXModule.default || XLSXModule

// 模拟井场
const MOCK_SITES = [
  { id: 's1', name: 'A 井场', code: 'A' },
  { id: 's2', name: 'B 井场', code: 'B' }
]
// 模拟井（按井场归属）
const MOCK_WELLS = [
  { id: '1', siteId: 's1', wellNo: '41-37YH3', name: '41-37YH3', wellheadE: 208, wellheadN: 2015, wellheadD: 0, wellDiameter: 0.216 },
  { id: '2', siteId: 's1', wellNo: '41-37YH5', name: '41-37YH5', wellheadE: 209, wellheadN: 2000, wellheadD: 0, wellDiameter: 0.216 },
  { id: '3', siteId: 's2', wellNo: '41-38YH1', name: '41-38YH1', wellheadE: 220, wellheadN: 2025, wellheadD: 0, wellDiameter: 0.216 }
]
const MOCK_NEIGHBOR_FILES = [
  { id: 'f1', fileName: '41-37YH3.xlsx', wellNo: '41-37YH3', uploadTime: '2024-01-15 10:00' },
  { id: 'f2', fileName: '41-37YH5.xlsx', wellNo: '41-37YH5', uploadTime: '2024-01-16 11:00' }
]

// Excel 要求列名（兼容多种写法）
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

export default {
  name: 'BasicData',
  data () {
    return {
      siteQuery: {},
      siteList: [...MOCK_SITES],
      siteColumns: [
        { title: '井场名称', dataIndex: 'name', key: 'name' },
        { title: '井场编号', dataIndex: 'code', key: 'code' },
        { title: '操作', key: 'action', scopedSlots: { customRender: 'action' }, width: 220 }
      ],
      siteModalVisible: false,
      siteForm: { id: null, name: '', code: '' },

      currentSiteId: null,
      wellQuery: {},
      wellList: [...MOCK_WELLS],
      wellColumns: [
        { title: '井号', dataIndex: 'wellNo', key: 'wellNo' },
        { title: '井名', dataIndex: 'name', key: 'name' },
        { title: '井口 E', dataIndex: 'wellheadE', key: 'wellheadE' },
        { title: '井口 N', dataIndex: 'wellheadN', key: 'wellheadN' },
        { title: '井口 D', dataIndex: 'wellheadD', key: 'wellheadD' },
        { title: '井径(m)', dataIndex: 'wellDiameter', key: 'wellDiameter' },
        { title: '操作', key: 'action', scopedSlots: { customRender: 'action' }, width: 180 }
      ],
      neighborFileList: [...MOCK_NEIGHBOR_FILES],
      neighborFileColumns: [
        { title: '文件名', dataIndex: 'fileName', key: 'fileName' },
        { title: '关联井号', dataIndex: 'wellNo', key: 'wellNo', scopedSlots: { customRender: 'wellNo' } },
        { title: '上传时间', dataIndex: 'uploadTime', key: 'uploadTime' },
        { title: '操作', key: 'action', scopedSlots: { customRender: 'action' }, width: 220 }
      ],

      wellModalVisible: false,
      wellForm: {
        id: null,
        wellNo: '',
        name: '',
        wellheadE: undefined,
        wellheadN: undefined,
        wellheadD: undefined,
        wellDiameter: undefined
      },
      linkWellModalVisible: false,
      linkWellTarget: null,
      linkWellNo: undefined,

      addWellDrawerVisible: false,
      addWellSubmitting: false,
      addWellForm: {
        wellNo: '',
        name: '',
        wellheadE: undefined,
        wellheadN: undefined,
        wellheadD: undefined,
        wellDiameter: undefined,
        fileList: [],
        parseError: '',
        parsePreview: [],
        parsedRows: null
      },
      excelPreviewColumns: [
        { title: '测深(m)', dataIndex: 'md', key: 'md' },
        { title: '井斜角(°)', dataIndex: 'inclination', key: 'inclination' },
        { title: '网格方位(°)', dataIndex: 'azimuth', key: 'azimuth' }
      ],

      showVisualization: false,
      chart3d: null,
      vizLoading: false,
      vizError: '',
      wellTrajectoryData: {}
    }
  },
  computed: {
    filteredSiteList () {
      if (!this.siteQuery.name) return this.siteList
      const q = (this.siteQuery.name || '').trim().toLowerCase()
      return this.siteList.filter(s => (s.name || '').toLowerCase().indexOf(q) >= 0)
    },
    currentSiteName () {
      const s = this.siteList.find(x => x.id === this.currentSiteId)
      return s ? s.name : ''
    },
    currentWellList () {
      if (!this.currentSiteId) return []
      return this.wellList.filter(w => w.siteId === this.currentSiteId)
    },
    filteredWellList () {
      const list = this.currentWellList
      if (!this.wellQuery.wellNo) return list
      const q = (this.wellQuery.wellNo || '').trim()
      return list.filter(w => (w.wellNo || '').indexOf(q) >= 0)
    },
    filteredNeighborFileList () {
      const wellNos = this.currentWellList.map(w => w.wellNo)
      return this.neighborFileList.filter(f => !f.wellNo || wellNos.indexOf(f.wellNo) >= 0)
    }
  },
  methods: {
    searchSites () {
      this.$forceUpdate()
    },
    openSiteModal (record) {
      this.siteForm = record ? { ...record } : { id: null, name: '', code: '' }
      this.siteModalVisible = true
    },
    saveSite () {
      if (!this.siteForm.name || !this.siteForm.name.trim()) {
        this.$message.warning('请填写井场名称')
        return
      }
      if (this.siteForm.id) {
        const idx = this.siteList.findIndex(s => s.id === this.siteForm.id)
        if (idx >= 0) this.siteList.splice(idx, 1, { ...this.siteForm })
      } else {
        this.siteList.push({ ...this.siteForm, id: 's' + Date.now() })
      }
      this.siteModalVisible = false
      this.$message.success('保存成功')
    },
    deleteSite (record) {
      this.siteList = this.siteList.filter(s => s.id !== record.id)
      this.wellList = this.wellList.filter(w => w.siteId !== record.id)
      if (this.currentSiteId === record.id) this.currentSiteId = null
      this.$message.success('已删除井场')
    },
    enterSite (record) {
      this.currentSiteId = record.id
    },
    exitSite () {
      this.currentSiteId = null
    },

    searchWells () {
      this.$forceUpdate()
    },
    openAddWellDrawer () {
      this.addWellForm = {
        wellNo: '',
        name: '',
        wellheadE: undefined,
        wellheadN: undefined,
        wellheadD: undefined,
        wellDiameter: undefined,
        fileList: [],
        parseError: '',
        parsePreview: [],
        parsedRows: null
      }
      this.addWellDrawerVisible = true
    },
    beforeUploadWellExcel (file) {
      this.addWellForm.parseError = ''
      this.addWellForm.parsePreview = []
      this.addWellForm.parsedRows = null
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result)
          const wb = XLSX.read(data, { type: 'array' })
          const firstSheet = wb.Sheets[wb.SheetNames[0]]
          const json = XLSX.utils.sheet_to_json(firstSheet, { header: 1, defval: '' })
          if (!json.length) {
            this.addWellForm.parseError = 'Excel 为空或无法解析'
            return
          }
          const headers = json[0].map(h => (h != null ? String(h).trim() : ''))
          const iMd = findColumnIndex(headers, EXCEL_COLUMNS.md)
          const iInc = findColumnIndex(headers, EXCEL_COLUMNS.inclination)
          const iAzi = findColumnIndex(headers, EXCEL_COLUMNS.azimuth)
          if (iMd < 0 || iInc < 0 || iAzi < 0) {
            const missing = []
            if (iMd < 0) missing.push('测深(m)')
            if (iInc < 0) missing.push('井斜角(°)')
            if (iAzi < 0) missing.push('网格方位(°)')
            this.addWellForm.parseError = '缺少列：' + missing.join('、') + '。请使用包含该三列的 Excel。'
            return
          }
          const rows = []
          for (let i = 1; i < json.length; i++) {
            const row = json[i]
            const md = row[iMd] != null ? Number(row[iMd]) : NaN
            const inc = row[iInc] != null ? Number(row[iInc]) : NaN
            const azi = row[iAzi] != null ? Number(row[iAzi]) : NaN
            if (Number.isNaN(md) && Number.isNaN(inc) && Number.isNaN(azi)) continue
            rows.push({ md, inclination: inc, azimuth: azi })
          }
          this.addWellForm.parsedRows = rows
          this.addWellForm.parsePreview = rows.slice(0, 5)
        } catch (err) {
          this.addWellForm.parseError = '解析失败：' + (err.message || String(err))
        }
      }
      reader.readAsArrayBuffer(file)
      this.addWellForm.fileList = [{ uid: file.uid, name: file.name, status: 'done' }]
      return false
    },
    submitAddWell () {
      const f = this.addWellForm
      if (!f.wellNo || !f.wellNo.trim()) {
        this.$message.warning('请填写井号')
        return
      }
      if (f.wellheadE == null || f.wellheadN == null || f.wellheadD == null) {
        this.$message.warning('请填写井口坐标 E、N、D')
        return
      }
      if (!f.fileList || !f.fileList.length) {
        this.$message.warning('请上传轨迹 Excel（须含测深(m)、井斜角(°)、网格方位(°)）')
        return
      }
      if (f.parseError) {
        this.$message.warning('请上传格式正确的 Excel')
        return
      }
      if (!f.parsedRows || !f.parsedRows.length) {
        this.$message.warning('Excel 中无有效数据行')
        return
      }
      this.addWellSubmitting = true
      const newWell = {
        id: String(Date.now()),
        siteId: this.currentSiteId,
        wellNo: f.wellNo.trim(),
        name: (f.name || f.wellNo).trim(),
        wellheadE: f.wellheadE,
        wellheadN: f.wellheadN,
        wellheadD: f.wellheadD,
        wellDiameter: f.wellDiameter != null ? f.wellDiameter : undefined
      }
      this.wellList.push(newWell)
      this.neighborFileList.push({
        id: 'f' + Date.now(),
        fileName: (f.fileList[0] && f.fileList[0].name) || '轨迹.xlsx',
        wellNo: newWell.wellNo,
        uploadTime: new Date().toLocaleString()
      })
      if (f.parsedRows && f.parsedRows.length) {
        this.wellTrajectoryData[newWell.id] = { rows: f.parsedRows.map(r => ({ md: r.md, inclination: r.inclination, azimuth: r.azimuth })) }
      }
      this.addWellSubmitting = false
      this.addWellDrawerVisible = false
      this.$message.success('井已新增（轨迹已按 Excel 解析）')
    },

    openEditWellModal (record) {
      this.wellForm = { ...record }
      this.wellModalVisible = true
    },
    saveWell () {
      const idx = this.wellList.findIndex(w => w.id === this.wellForm.id)
      if (idx >= 0) this.wellList.splice(idx, 1, { ...this.wellForm })
      this.wellModalVisible = false
      this.$message.success('保存成功')
    },
    deleteWell (record) {
      this.wellList = this.wellList.filter(w => w.id !== record.id)
      this.neighborFileList = this.neighborFileList.filter(f => f.wellNo !== record.wellNo)
      delete this.wellTrajectoryData[record.id]
      this.$message.success('已删除')
    },
    beforeUploadTrajectory (file) {
      this.neighborFileList.push({
        id: 'f' + Date.now(),
        fileName: file.name,
        wellNo: null,
        uploadTime: new Date().toLocaleString()
      })
      this.$message.success('已添加：' + file.name + '，请点击「关联井」选择关联井号')
      return false
    },
    downloadTrajectory (record) {
      const url = record.fileName ? `/${record.fileName}` : (record.wellNo ? `/${record.wellNo}.xlsx` : null)
      if (url) {
        window.open(url, '_blank')
        this.$message.info('若文件在 public 下存在则在新窗口打开')
      } else {
        this.$message.warning('无文件名，请先关联井或确认文件在 public 目录')
      }
    },
    deleteTrajectory (record) {
      this.neighborFileList = this.neighborFileList.filter(f => f.id !== record.id)
      this.$message.success('已删除')
    },
    openLinkWellModal (record) {
      this.linkWellTarget = record
      this.linkWellNo = record.wellNo || undefined
      this.linkWellModalVisible = true
    },
    saveLinkWell () {
      if (this.linkWellTarget) {
        this.linkWellTarget.wellNo = this.linkWellNo || null
        this.$message.success('关联成功')
      }
      this.linkWellModalVisible = false
      this.linkWellTarget = null
    },

    toggleVisualization () {
      if (this.showVisualization) {
        this.showVisualization = false
        if (this.chart3d) {
          this.chart3d.dispose()
          this.chart3d = null
        }
        return
      }
      this.showVisualization = true
      this.$nextTick(() => this.loadAndRender3D())
    },
    loadAndRender3D () {
      this.vizLoading = true
      this.vizError = ''
      const wells = this.currentWellList
      if (!wells.length) {
        this.vizLoading = false
        this.vizError = '当前井场下暂无井'
        return
      }
      if (!XLSX || typeof XLSX.read !== 'function') {
        this.vizLoading = false
        this.vizError = 'Excel 解析库未就绪，请刷新页面重试'
        return
      }
      const parseExcelBuffer = (buf, well) => {
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
        const wellhead = [well.wellheadE, well.wellheadN, well.wellheadD]
        const points = minimumCurvatureToEND(rows, wellhead)
        return { wellNo: well.wellNo, points }
      }
      const tryFetch = (well) => {
        const stored = this.wellTrajectoryData[well.id]
        if (stored && stored.rows && stored.rows.length) {
          const wellhead = [well.wellheadE, well.wellheadN, well.wellheadD]
          const points = minimumCurvatureToEND(stored.rows, wellhead)
          return Promise.resolve({ wellNo: well.wellNo, points })
        }
        // 先走后端接口（当前为占位，会 reject，不真实发请求）
        return getWellTrajectoryExcel(this.currentSiteId, well.id)
          .then(buf => parseExcelBuffer(buf, well))
          .catch(() => {
            // 回退：从 public 按井号加载（如 41-37YH3.xlsx、41-37YH5.xlsx）
            const tryUrl = (url) =>
              fetch(url).then(res => (res.ok ? res.arrayBuffer() : Promise.reject(new Error('404'))))
            const urls = [`/optimization/${well.wellNo}.xlsx`, `/${well.wellNo}.xlsx`]
            const neighbor = this.neighborFileList.find(f => f.wellNo === well.wellNo)
            if (neighbor && neighbor.fileName) urls.push(`/${neighbor.fileName}`)
            let p = Promise.reject(new Error('404'))
            urls.forEach(url => { p = p.catch(() => tryUrl(url)) })
            return p.then(buf => parseExcelBuffer(buf, well))
          })
      }
      Promise.all(wells.map(w => tryFetch(w).catch(() => null)))
        .then(results => {
          const seriesList = results.filter(r => r && r.points && r.points.length)
          this.vizLoading = false
          if (!seriesList.length) {
            this.vizError = '当前井场无轨迹数据。请通过「新增井」上传轨迹 Excel，或将井号同名 xlsx（如 41-37YH3.xlsx）放入 public 目录。'
            return
          }
          this.$nextTick(() => this.render3DChart(seriesList))
        })
        .catch(err => {
          this.vizLoading = false
          this.vizError = (err && err.message) || '加载或解析失败'
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
</script>

<style lang="less" scoped>
.section-title { font-weight: 600; margin-bottom: 12px; }
.danger { color: #ff4d4f; }
.error-text { color: #ff4d4f; font-size: 12px; margin-top: 4px; }
.preview-table { margin-top: 8px; }
.preview-title { font-size: 12px; color: rgba(0,0,0,0.45); margin-bottom: 4px; }
.drawer-footer {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 100%;
  padding: 10px 16px;
  text-align: right;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}
.drawer-footer .ant-btn + .ant-btn {
  margin-left: 10px;
}
.compact-form .ant-form-item {
  margin-bottom: 16px;
}
.compact-form .input-narrow.ant-input,
.compact-form .input-narrow.ant-input-number,
.compact-form .input-narrow.ant-select {
  width: 100%;
  max-width: 220px;
}
.compact-form .ant-btn + .ant-btn {
  margin-left: 10px;
}
.viz-section { margin-top: 24px; }
.viz-error { color: #ff4d4f; padding: 12px; }
.chart3d-container { width: 100%; height: 500px; }
.modal-desc {
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 16px;
  padding: 0;
}
.form-divider {
  margin: 16px 0 12px 0;
  font-size: 13px;
}
</style>
