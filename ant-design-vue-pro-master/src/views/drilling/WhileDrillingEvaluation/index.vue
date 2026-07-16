<template>
  <div class="while-drilling-evaluation">
    <a-card :bordered="false" class="scan-form">
      <div class="algo-row">
        <label class="algo-label">井场：</label>
        <div class="algo-input">
          <a-select
            v-model="form.siteId"
            placeholder="请选择井场"
            class="algo-input-inner"
            :disabled="monitoring"
            @change="onSiteChange"
          >
            <a-select-option v-for="site in siteList" :key="site.id" :value="site.id">
              {{ site.name }}
            </a-select-option>
          </a-select>
        </div>
      </div>
      <div class="algo-row">
        <label class="algo-label">待钻井：</label>
        <div class="algo-input">
          <a-select
            v-model="form.pendingWellId"
            placeholder="请先选择井场"
            class="algo-input-inner"
            :disabled="!form.siteId || monitoring"
          >
            <a-select-option v-for="well in pendingWells" :key="well.id" :value="well.id">
              {{ well.wellNo }} - {{ well.name }}
            </a-select-option>
          </a-select>
        </div>
      </div>
      <div class="algo-row">
        <label class="algo-label"></label>
        <div class="algo-input">
          <a-button
            v-if="!monitoring"
            type="primary"
            :loading="startLoading"
            :disabled="!form.pendingWellId"
            icon="play-circle"
            @click="startMonitoring"
          >
            开始随钻评估
          </a-button>
          <a-button v-else type="danger" icon="pause-circle" @click="stopMonitoring">
            停止评估
          </a-button>
        </div>
      </div>

      <template v-if="sessionInfo">
        <a-divider>数据接收端口</a-divider>
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="会话 ID">{{ sessionInfo.sessionId }}</a-descriptions-item>
          <a-descriptions-item label="TCP 端口">
            {{ sessionInfo.tcpPort }}（JSON 行格式：{"sessionId":"...","x":E,"y":N,"z":TVD}）
          </a-descriptions-item>
          <a-descriptions-item label="REST 接口">POST {{ sessionInfo.restPositionUrl }}</a-descriptions-item>
          <a-descriptions-item label="WebSocket">{{ sessionInfo.wsPath }}</a-descriptions-item>
          <a-descriptions-item label="启用轨迹偏离预测阈值">{{ sessionInfo.alertDistanceM }} m</a-descriptions-item>
        </a-descriptions>
      </template>

      <a-divider>实时评估</a-divider>
      <template v-if="latestResult">
        <a-alert
          :message="latestResult.message"
          :type="alertType"
          show-icon
          style="margin-bottom: 16px"
        />
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="状态">
            <a-tag :color="statusColor">{{ latestResult.status }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="水平偏移">{{ fmt2(latestResult.horizontalDistance) }} m</a-descriptions-item>
          <a-descriptions-item label="当前坐标">
            E={{ fmt2(latestResult.currentX) }}, N={{ fmt2(latestResult.currentY) }}, TVD={{ fmt2(latestResult.currentZ) }}
          </a-descriptions-item>
          <a-descriptions-item label="设计点(同深)">
            E={{ fmt2(latestResult.designX) }}, N={{ fmt2(latestResult.designY) }}
          </a-descriptions-item>
          <a-descriptions-item v-if="latestResult.dlsDegPer30m != null" label="DLS">
            {{ fmt2(latestResult.dlsDegPer30m) }} °/30m
          </a-descriptions-item>
          <a-descriptions-item v-if="latestResult.monteCarloSampleCount > 0" label="偏移概率">
            {{ fmt2(latestResult.monteCarloComprehensiveProbability) }}%
            （{{ latestResult.monteCarloComprehensiveCount }}/{{ latestResult.monteCarloSampleCount }}）
          </a-descriptions-item>
          <a-descriptions-item v-if="latestResult.shouldStopDrilling" label="钻进建议" :span="2">
            <span style="color: #f5222d; font-weight: bold">建议停止钻进</span>
          </a-descriptions-item>
        </a-descriptions>

        <div v-if="latestResult.monteCarloSampleCount > 0" style="margin-top: 16px">
          <a-divider orientation="left">ISCWSA 误差参数</a-divider>
          <a-descriptions bordered size="small" :column="2">
            <a-descriptions-item label="MWD σ(MD)">{{ fmt2(latestResult.iscwsaSigmaMd) }} m</a-descriptions-item>
            <a-descriptions-item label="MWD σ(Inc)">{{ fmt2(latestResult.iscwsaSigmaIncDeg) }} °</a-descriptions-item>
            <a-descriptions-item label="MWD σ(Azi)">{{ fmt2(latestResult.iscwsaSigmaAziDeg) }} °</a-descriptions-item>
            <a-descriptions-item label="偏移阈值">
              {{ fmt2(latestResult.monteCarloComprehensiveThresholdM) }} m
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </template>
      <a-empty v-else-if="monitoring" description="等待接收钻进坐标..." />
      <a-empty v-else description="请选择井场与待钻井后开始评估" />

      <div v-if="history.length" style="margin-top: 24px">
        <a-divider orientation="left">监测历史</a-divider>
        <a-table
          :columns="historyColumns"
          :data-source="history"
          :pagination="{ pageSize: 10 }"
          size="small"
          row-key="timestamp"
        >
          <span slot="status" slot-scope="text">
            <a-tag :color="statusColorMap[text] || 'default'">{{ text }}</a-tag>
          </span>
        </a-table>
      </div>
    </a-card>
  </div>
</template>

<script>
import { drillingAPI } from '@/api'

function fmt2 (v) {
  if (v == null || v === '' || Number.isNaN(Number(v))) return '-'
  return Number(v).toFixed(2)
}

export default {
  name: 'WhileDrillingEvaluation',
  data () {
    return {
      siteList: [],
      wellList: [],
      form: {
        siteId: undefined,
        pendingWellId: undefined
      },
      monitoring: false,
      startLoading: false,
      sessionInfo: null,
      latestResult: null,
      ws: null,
      history: [],
      statusColorMap: {
        '正常': 'green',
        '关注': 'blue',
        '预警': 'orange',
        '危险': 'red'
      },
      historyColumns: [
        { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
        { title: '水平偏移(m)', dataIndex: 'horizontalDistance', key: 'horizontalDistance', customRender: (t) => fmt2(t) },
        { title: '状态', dataIndex: 'status', key: 'status', scopedSlots: { customRender: 'status' } },
        { title: '说明', dataIndex: 'message', key: 'message', ellipsis: true }
      ]
    }
  },
  computed: {
    pendingWells () {
      if (!this.form.siteId) return []
      return this.wellList.filter(w => w.siteId === this.form.siteId && w.type === 'planned')
    },
    alertType () {
      if (!this.latestResult) return 'info'
      const s = this.latestResult.status
      if (s === '正常') return 'success'
      if (s === '危险') return 'error'
      if (s === '预警') return 'warning'
      return 'info'
    },
    statusColor () {
      return this.statusColorMap[this.latestResult?.status] || 'default'
    }
  },
  created () {
    this.loadSiteList()
  },
  beforeDestroy () {
    this.closeWebSocket()
    if (this.monitoring && this.sessionInfo) {
      this.stopMonitoring()
    }
  },
  methods: {
    fmt2,
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
          id: w.id, siteId: w.siteId, wellNo: w.wellNo, name: w.name, type: 'existing'
        }))
        const pendingWells = this.normalizeListResponse(pendingRes).map(w => ({
          id: w.id, siteId: w.siteId, wellNo: w.wellNo, name: w.name, type: 'planned'
        }))
        this.wellList = [...existingWells, ...pendingWells]
      } catch (e) {
        this.$message.error('加载井列表失败：' + (e.message || '未知错误'))
      }
    },
    onSiteChange () {
      this.form.pendingWellId = undefined
      if (this.form.siteId) {
        this.loadWellsBySite(this.form.siteId)
      }
    },
    async startMonitoring () {
      if (!this.form.siteId || !this.form.pendingWellId) {
        this.$message.warning('请选择井场和待钻井')
        return
      }
      this.startLoading = true
      try {
        const res = await drillingAPI.startWhileDrillingSession({
          siteId: this.form.siteId,
          pendingWellId: this.form.pendingWellId
        })
        this.sessionInfo = res.data || res
        this.monitoring = true
        this.latestResult = null
        this.history = []
        this.connectWebSocket(this.sessionInfo.sessionId)
        this.$message.success('随钻评估已启动，TCP 端口 ' + this.sessionInfo.tcpPort + ' 已开放')
      } catch (e) {
        this.$message.error('启动失败：' + (e.message || '未知错误'))
      } finally {
        this.startLoading = false
      }
    },
    async stopMonitoring () {
      if (this.sessionInfo) {
        try {
          await drillingAPI.stopWhileDrillingSession({ sessionId: this.sessionInfo.sessionId })
        } catch (e) {
          console.warn('停止会话失败', e)
        }
      }
      this.closeWebSocket()
      this.monitoring = false
      this.sessionInfo = null
      this.$message.info('随钻评估已停止')
    },
    connectWebSocket (sessionId) {
      this.closeWebSocket()
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = process.env.NODE_ENV === 'development' ? '127.0.0.1:8003' : window.location.host
      const url = `${protocol}//${host}/whileDrilling/ws/${sessionId}`
      this.ws = new WebSocket(url)
      this.ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data)
          this.onEvaluationResult(data)
        } catch (e) {
          console.warn('WebSocket 消息解析失败', e)
        }
      }
      this.ws.onerror = () => {
        console.warn('WebSocket 连接异常，请检查后端服务或使用 TCP/REST 推送坐标')
      }
    },
    closeWebSocket () {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
    },
    onEvaluationResult (result) {
      this.latestResult = result
      this.history.unshift({
        timestamp: result.timestamp || Date.now(),
        time: new Date(result.timestamp || Date.now()).toLocaleString(),
        horizontalDistance: result.horizontalDistance,
        status: result.status,
        message: result.message
      })
    }
  }
}
</script>

<style lang="less" scoped>
.while-drilling-evaluation {
  .algo-row {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  .algo-label {
    flex-shrink: 0;
    min-width: 180px;
    margin: 0;
    font-weight: normal;
    color: rgba(0, 0, 0, 0.85);
  }
  .algo-input {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
  }
  .algo-input-inner {
    width: 100%;
    max-width: 280px;
  }
}
</style>
