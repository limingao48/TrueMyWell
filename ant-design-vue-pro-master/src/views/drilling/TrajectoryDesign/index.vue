<template>
  <page-header-wrapper :title="false">
    <template #content>
      先选择井场，再输入靶点、入靶需求与井口，选择优化算法，一键生成七段式设计参数与轨迹，含邻井防碰。
    </template>
    <a-card :bordered="false">
      <a-steps class="steps" :current="currentStep">
        <a-step title="选择井场" />
        <a-step title="靶点与入靶与井口" />
        <a-step title="邻井选择" />
        <a-step title="算法与参数" />
        <a-step title="结果与导出" />
      </a-steps>
      <div class="content">
        <!-- 步骤0：选择井场 -->
        <div v-if="currentStep === 0" class="step-form">
          <p class="step-desc">选择在哪个井场中进行轨迹设计，后续邻井将从该井场下选择。</p>
          <div class="algo-row">
            <label class="algo-label">井场 <span class="required">*</span></label>
            <div class="algo-input">
              <a-select
                v-model="form.siteId"
                placeholder="请选择井场"
                class="algo-input-inner"
                allow-clear
              >
                <a-select-option v-for="s in siteList" :key="s.id" :value="s.id">{{ s.name }}</a-select-option>
              </a-select>
            </div>
          </div>
          <div class="step-actions">
            <a-button type="primary" :disabled="!form.siteId" @click="nextStep">下一步</a-button>
          </div>
        </div>

        <!-- 步骤1：靶点坐标、入靶需求、井口坐标 -->
        <div v-if="currentStep === 1" class="step-form">
          <p class="step-desc">输入靶点坐标、入靶时的井斜角与网格方位范围、设计井井口坐标。</p>
          <a-divider orientation="left">靶点坐标（米，E/N/D）</a-divider>
          <div class="algo-row">
            <label class="algo-label">靶点东坐标 E：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.target.e"
                :min="0"
                class="algo-input-inner"
                placeholder="如 502.64"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">靶点北坐标 N：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.target.n"
                :min="0"
                class="algo-input-inner"
                placeholder="如 2790.71"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">靶点垂深 D：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.target.d"
                :min="0"
                class="algo-input-inner"
                placeholder="如 2636.06"
              />
            </div>
          </div>
          <a-divider orientation="left">入靶需求</a-divider>
          <div class="algo-row">
            <label class="algo-label">井斜角范围(°)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.landingRequirement.inclinationMin"
                :min="0"
                :max="90"
                class="algo-input-inner algo-input-range"
                placeholder="最小"
              />
              <span class="range-sep">~</span>
              <a-input-number
                v-model="form.landingRequirement.inclinationMax"
                :min="0"
                :max="90"
                class="algo-input-inner algo-input-range"
                placeholder="最大"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">网格方位范围(°)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.landingRequirement.azimuthMin"
                :min="0"
                :max="360"
                class="algo-input-inner algo-input-range"
                placeholder="最小"
              />
              <span class="range-sep">~</span>
              <a-input-number
                v-model="form.landingRequirement.azimuthMax"
                :min="0"
                :max="360"
                class="algo-input-inner algo-input-range"
                placeholder="最大"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">垂深允差(m)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.landingRequirement.verticalTolerance"
                :min="0.1"
                :max="50"
                :step="0.1"
                class="algo-input-inner"
                placeholder="如 5"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">水平允差(m)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.landingRequirement.horizontalTolerance"
                :min="0.1"
                :max="50"
                :step="0.1"
                class="algo-input-inner"
                placeholder="如 5"
              />
            </div>
          </div>
          <a-divider orientation="left">井口坐标（米，E/N/D）</a-divider>
          <div class="algo-row">
            <label class="algo-label">井口东坐标 E：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.wellhead.e"
                :min="0"
                class="algo-input-inner"
                placeholder="如 222"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">井口北坐标 N：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.wellhead.n"
                :min="0"
                class="algo-input-inner"
                placeholder="如 2030"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">井口海拔 D：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.wellhead.d"
                :min="0"
                class="algo-input-inner"
                placeholder="如 0"
              />
            </div>
          </div>
          <div class="step-actions">
            <a-button type="primary" @click="nextStep">下一步</a-button>
            <a-button @click="prevStep">上一步</a-button>
          </div>
        </div>

        <!-- 步骤2：邻井选择 -->
        <div v-if="currentStep === 2" class="step-form">
          <div class="algo-row">
            <label class="algo-label">选择邻井：</label>
            <div class="algo-input">
              <a-select
                v-model="form.neighborWellIds"
                mode="multiple"
                placeholder="从当前井场中选择邻井（可多选）"
                class="algo-input-inner algo-input-full"
              >
                <a-select-option v-for="w in neighborWells" :key="w.id" :value="w.id">{{ w.wellNo }} {{ w.name && w.name !== w.wellNo ? `（${w.name}）` : '' }}</a-select-option>
              </a-select>
            </div>
          </div>
          <div class="algo-row algo-row-table">
            <label class="algo-label">已选邻井井口：</label>
            <div class="algo-input">
              <a-table
                :columns="neighborColumns"
                :data-source="selectedNeighborWellheads"
                :pagination="false"
                size="small"
                row-key="id"
              />
            </div>
          </div>
          <div class="step-actions">
            <a-button type="primary" @click="nextStep">下一步</a-button>
            <a-button @click="prevStep">上一步</a-button>
          </div>
        </div>

        <!-- 步骤3：算法与参数 -->
        <div v-if="currentStep === 3" class="step-form">
          <p class="step-desc">选择优化算法与防碰分析方法，填写防碰与造斜约束；高级参数可展开后按需填写。</p>

          <div class="algo-row">
            <label class="algo-label">优化算法</label>
            <div class="algo-input">
              <a-select v-model="form.algorithm.type" placeholder="请选择" class="algo-input-inner">
                <a-select-option value="PSO">PSO</a-select-option>
                <a-select-option value="B2OPT">B2OPT</a-select-option>
                <a-select-option value="GA-optiGAN">GA-optiGAN</a-select-option>
              </a-select>
            </div>
          </div>

          <a-divider orientation="left">防碰与造斜约束</a-divider>
          <div class="algo-row">
            <label class="algo-label">防碰分析方法：</label>
            <div class="algo-input">
              <a-select v-model="form.algorithm.anticollisionMethod" placeholder="请选择" class="algo-input-inner">
                <a-select-option value="CTC">CTC 井眼中心距法</a-select-option>
                <a-select-option value="SF">SF 分离系数法</a-select-option>
              </a-select>
            </div>
          </div>
          <div v-if="form.algorithm.anticollisionMethod === 'CTC'" class="algo-row">
            <label class="algo-label">最小安全半径(m)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.algorithm.safeRadius"
                :min="1"
                :max="50"
                class="algo-input-inner"
                placeholder="如 10"
              />
            </div>
          </div>
          <div v-else class="algo-row">
            <label class="algo-label">最小 SF：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.algorithm.minSafetyFactor"
                :min="1"
                :max="3"
                :step="0.1"
                class="algo-input-inner"
                placeholder="如 1.2"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">最低造斜深度(m)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.algorithm.minKickoffDepth"
                :min="0"
                :max="5000"
                class="algo-input-inner"
                placeholder="如 500"
              />
            </div>
          </div>
          <div class="algo-row">
            <label class="algo-label">狗腿度范围(°/30m)：</label>
            <div class="algo-input">
              <a-input-number
                v-model="form.algorithm.doglegMin"
                :min="0"
                :max="20"
                :step="0.1"
                class="algo-input-inner algo-input-range"
                placeholder="最小"
              />
              <span class="range-sep">~</span>
              <a-input-number
                v-model="form.algorithm.doglegMax"
                :min="0"
                :max="20"
                :step="0.1"
                class="algo-input-inner algo-input-range"
                placeholder="最大"
              />
            </div>
          </div>

          <a-collapse v-if="form.algorithm.type">
            <a-collapse-panel key="1" header="高级参数（可选）">
              <div class="algo-row">
                <label class="algo-label">种群数：</label>
                <div class="algo-input">
                  <a-input-number
                    v-model="form.algorithm.population"
                    :min="10"
                    :max="500"
                    class="algo-input-inner"
                    placeholder="如 50"
                  />
                </div>
              </div>
              <div class="algo-row">
                <label class="algo-label">迭代次数：</label>
                <div class="algo-input">
                  <a-input-number
                    v-model="form.algorithm.iterations"
                    :min="50"
                    :max="2000"
                    class="algo-input-inner"
                    placeholder="如 200"
                  />
                </div>
              </div>
            </a-collapse-panel>
          </a-collapse>

          <div class="step-actions">
            <a-button type="primary" :loading="designLoading" @click="startDesign">开始设计</a-button>
            <a-button @click="prevStep">上一步</a-button>
          </div>
        </div>

        <!-- 步骤4：结果与导出 -->
        <div v-if="currentStep === 4" class="step-form">
          <a-alert v-if="designResult" message="设计完成" type="success" show-icon style="margin-bottom: 16px" />
          <a-descriptions v-if="designResult" title="七段式设计参数（12 参数）" bordered size="small" :column="2">
            <a-descriptions-item v-for="(v, k) in designResult.best_solution_dict" :key="k" :label="paramLabels[k] || k">
              {{ v }}
            </a-descriptions-item>
          </a-descriptions>
          <div v-if="designResult" style="margin-top: 16px">
            <a-space>
              <span>入靶偏差：{{ designResult.final_deviation }} m</span>
              <span>优化耗时：{{ designResult.optimization_time }} s</span>
            </a-space>
          </div>
          <div v-if="designResult" class="trajectory-chart">
            <div class="chart-header">
              <h4>3D 轨迹图（含邻井叠加）</h4>
              <div class="legend">
                <span class="legend-item">
                  <span class="legend-color" style="background-color: #1890ff"></span>
                  <span>设计井</span>
                </span>
                <span v-for="(well, index) in designResult.neighbor_wells" :key="well.wellId" class="legend-item">
                  <span class="legend-color" :style="{ backgroundColor: getNeighborColor(index) }"></span>
                  <span>{{ well.wellName }}</span>
                </span>
              </div>
            </div>
            <div ref="trajectoryChart" class="chart-container"></div>
          </div>
          <div v-if="designResult" class="result-actions">
            <a-button type="primary" icon="save" @click="saveAsDesign">保存为设计井</a-button>
            <a-button icon="export" @click="exportReport">导出报告</a-button>
            <a-button @click="$router.push('/drilling/anticollision')">发起防碰扫描</a-button>
          </div>
          <div class="step-actions" style="margin-top: 24px">
            <a-button @click="prevStep">上一步</a-button>
            <a-button type="primary" @click="resetSteps">重新设计</a-button>
          </div>
        </div>
      </div>
    </a-card>

    <!-- 优化进度弹窗 -->
    <a-modal
      v-if="showProgressModal"
      title="轨迹设计优化中"
      :visible="showProgressModal"
      :closable="false"
      :maskClosable="false"
      :footer="null"
      width="520px"
    >
      <div class="progress-container">
        <div class="progress-header">
          <a-spin :spinning="true" size="large" tip="优化进行中..." />
        </div>
        <div class="progress-info">
          <p class="progress-message">{{ progressInfo.message || '初始化...' }}</p>
          <div class="progress-row">
            <span class="progress-label">迭代进度：</span>
            <span class="progress-value">{{ progressInfo.iteration || 0 }} / {{ progressInfo.totalIterations || 0 }}</span>
          </div>
          <div class="progress-row">
            <span class="progress-label">当前最优值：</span>
            <span class="progress-value">{{ progressInfo.currentBest !== undefined ? progressInfo.currentBest.toFixed(2) : '-' }}</span>
          </div>
        </div>
        <a-progress
          :percent="Math.round(progressInfo.progressPercent || 0)"
          :show-info="false"
          stroke-color="#1890ff"
        />
        <div class="progress-percent">{{ Math.round(progressInfo.progressPercent || 0) }}%</div>
      </div>
    </a-modal>
  </page-header-wrapper>
</template>

<script>
import { drillingAPI } from '@/api'
import TrajectoryDesignRequest from '@/entity/TrajectoryDesignRequest'
import * as echarts from 'echarts'
import 'echarts-gl'

const PARAM_LABELS = {
  seven_L0: '第1段直井段长度(m)',
  L0: '第1段直井段长度(m)',
  seven_DLS1: '第2段增斜段狗腿度(°/30m)',
  DLS1: '第2段增斜段狗腿度(°/30m)',
  seven_alpha3: '第3段稳斜井斜角(°)',
  alpha3: '第3段稳斜井斜角(°)',
  seven_L3: '第3段稳斜段长度(m)',
  L3: '第3段稳斜段长度(m)',
  seven_DLS_turn: '第4段扭方位狗腿度(°/30m)',
  DLS_turn: '第4段扭方位狗腿度(°/30m)',
  seven_L4: '第4段扭方位段长度(m)',
  L4: '第4段扭方位段长度(m)',
  seven_phi_target: '末端目标方位角(°)',
  phi_target: '末端目标方位角(°)',
  seven_L5: '第5段扭方位后稳斜段长度(m)',
  L5: '第5段扭方位后稳斜段长度(m)',
  seven_DLS6: '第6段井斜调整段狗腿度(°/30m)',
  DLS6: '第6段井斜调整段狗腿度(°/30m)',
  seven_alpha_e: '第7段末端井斜角(°)',
  alpha_e: '第7段末端井斜角(°)',
  seven_L7: '第7段末端稳斜段长度(m)',
  L7: '第7段末端稳斜段长度(m)',
  seven_phi_init: '初始方位角(°)',
  phi_init: '初始方位角(°)'
}

export default {
  name: 'TrajectoryDesign',
  data () {
    return {
      currentStep: 0,
      designLoading: false,
      siteList: [],
      wellList: [],
      form: {
        siteId: undefined,
        target: { e: 502.64, n: 2790.71, d: 2636.06 },
        landingRequirement: {
          inclinationMin: 85,
          inclinationMax: 92,
          azimuthMin: 40,
          azimuthMax: 50,
          verticalTolerance: 5,
          horizontalTolerance: 5
        },
        wellhead: { e: 222, n: 2030, d: 0 },
        neighborWellIds: [],
        algorithm: {
          type: 'PSO',
          anticollisionMethod: 'SF',
          minSafetyFactor: 1.2,
          minKickoffDepth: 500,
          doglegMin: 2,
          doglegMax: 5,
          population: 50,
          iterations: 200,
          safeRadius: 10
        }
      },
      neighborColumns: [
        { title: '井号', dataIndex: 'wellNo', key: 'wellNo' },
        { title: '井口 E', dataIndex: 'e', key: 'e' },
        { title: '井口 N', dataIndex: 'n', key: 'n' },
        { title: '井口 D', dataIndex: 'd', key: 'd' }
      ],
      designResult: null,
      paramLabels: PARAM_LABELS,
      showProgressModal: false,
      progressInfo: {
        iteration: 0,
        totalIterations: 0,
        currentBest: undefined,
        progressPercent: 0,
        message: ''
      },
      pollingInterval: null,
      currentTaskId: null
    }
  },
  watch: {
    'form.siteId' (newSiteId) {
      this.form.neighborWellIds = []
      if (!newSiteId) {
        this.wellList = []
        return
      }
      this.loadWellsBySite(newSiteId)
    }
  },
  created () {
    this.loadSiteList()
  },
  beforeUnmount () {
    this.closePolling()
  },
  computed: {
    neighborWells () {
      if (!this.form.siteId) return []
      return this.wellList
        .filter(w => w.siteId === this.form.siteId)
        .map(w => ({
          id: w.id,
          wellNo: w.wellNo,
          name: w.name,
          wellhead: { e: w.wellheadE, n: w.wellheadN, d: w.wellheadD }
        }))
    },
    selectedNeighborWellheads () {
      return this.neighborWells
        .filter(w => this.form.neighborWellIds.includes(w.id))
        .map(w => ({
          id: w.id,
          wellNo: w.wellNo,
          e: w.wellhead.e,
          n: w.wellhead.n,
          d: w.wellhead.d
        }))
    }
  },
  methods: {
    normalizeListResponse (res) {
      if (Array.isArray(res)) return res
      if (res && Array.isArray(res.data)) return res.data
      return []
    },
    loadSiteList () {
      drillingAPI.getSiteList()
        .then((res) => {
          this.siteList = this.normalizeListResponse(res)
        })
        .catch((err) => {
          this.$message.error('加载井场失败：' + (err.message || '未知错误'))
        })
    },
    loadWellsBySite (siteId) {
      drillingAPI.getWellsBySite(siteId)
        .then((res) => {
          const allWells = this.normalizeListResponse(res)
          this.wellList = allWells.filter(w => String(w.siteId) === String(siteId))
        })
        .catch((err) => {
          this.$message.error('加载井列表失败：' + (err.message || '未知错误'))
          this.wellList = []
        })
    },
    nextStep () {
      if (this.currentStep < 4) this.currentStep += 1
    },
    prevStep () {
      if (this.currentStep > 0) this.currentStep -= 1
    },
    async startDesign () {
      this.designLoading = true
      this.showProgressModal = true
      this.progressInfo = {
        iteration: 0,
        totalIterations: this.form.algorithm.iterations || 200,
        currentBest: undefined,
        progressPercent: 0,
        message: '正在初始化优化任务...'
      }

      try {
        const request = TrajectoryDesignRequest.fromForm(this.form)

        const taskId = await drillingAPI.startDesign(request.toRequest())
        this.currentTaskId = taskId

        this.startPolling(taskId)
      } catch (err) {
        this.handleDesignError(err)
      }
    },
    startPolling (taskId) {
      this.closePolling()

      this.pollingInterval = setInterval(async () => {
        try {
          const progress = await drillingAPI.getDesignStatus(taskId)
          this.progressInfo = {
            iteration: progress.iteration || 0,
            totalIterations: progress.totalIterations || this.form.algorithm.iterations || 200,
            currentBest: progress.currentBest,
            progressPercent: progress.progressPercent || 0,
            message: progress.message || '优化进行中...'
          }

          if (progress.completed) {
            this.closePolling()
            if (progress.result) {
              this.handleDesignSuccess(progress.result)
            } else {
              this.handleDesignError(new Error('优化任务已完成，但未返回结果'))
            }
          }
        } catch (err) {
          this.closePolling()
          this.handleDesignError(err)
        }
      }, 500)
    },
    handleDesignError (err) {
      this.closePolling()
      this.showProgressModal = false
      this.designLoading = false
      this.$message.error('轨迹设计失败：' + (err.message || '未知错误'))
    },
    closePolling () {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    },
    resetSteps () {
      this.closePolling()
      this.currentStep = 0
      this.designResult = null
      this.showProgressModal = false
      this.progressInfo = {
        iteration: 0,
        totalIterations: 0,
        currentBest: undefined,
        progressPercent: 0,
        message: ''
      }
    },
    getNeighborColor (index) {
      const colors = ['#52c41a', '#f5222d', '#faad14', '#722ed1', '#13c2c2', '#eb2f96']
      return colors[index % colors.length]
    },
    initTrajectoryChart () {
      if (!this.designResult || !this.$refs.trajectoryChart) return

      const el = this.$refs.trajectoryChart
      if (this.trajectoryChart) this.trajectoryChart.dispose()
      this.trajectoryChart = echarts.init(el)

      const colors = ['#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#faad14', '#f5222d']
      const seriesList = []

      // 添加设计井轨迹
      if (this.designResult.trajectory_points && this.designResult.trajectory_points.length > 0) {
        const points = this.designResult.trajectory_points.map(p => [p.x, p.y, p.z])
        seriesList.push({
          wellName: '设计井',
          points: points
        })
      }

      // 添加邻井轨迹
      if (this.designResult.neighbor_wells && this.designResult.neighbor_wells.length > 0) {
        console.log('邻井数量:', this.designResult.neighbor_wells.length)
        this.designResult.neighbor_wells.forEach((well, index) => {
          if (well.trajectory_points && well.trajectory_points.length > 0) {
            console.log('邻井', index + 1, ':', well.wellName, '点数量:', well.trajectory_points.length)
            const points = well.trajectory_points.map(p => [p.x, p.y, p.z])
            seriesList.push({
              wellName: well.wellName,
              points: points
            })
          }
        })
      } else {
        console.log('没有邻井数据')
      }

      const series = seriesList.map((item, i) => {
        const color = colors[i % colors.length]
        const data = item.points.map(p => [p[0], p[1], -p[2]])
        return {
          type: 'line3D',
          name: item.wellName,
          data,
          lineStyle: { width: i === 0 ? 4 : 2, color, opacity: i === 0 ? 1 : 0.7 },
          itemStyle: { opacity: 0.8 },
          emphasis: {
            lineStyle: { width: 6 }
          }
        }
      })

      const option = {
        tooltip: {
          formatter: (params) => {
            const data = params.value
            return `<strong>${params.seriesName}</strong><br/>
              E: ${data[0].toFixed(2)} m<br/>
              N: ${data[1].toFixed(2)} m<br/>
              D: ${-data[2].toFixed(2)} m`
          }
        },
        legend: {
          data: series.map(s => s.name),
          bottom: 0,
          itemWidth: 12,
          itemHeight: 12,
          textStyle: { fontSize: 12 }
        },
        backgroundColor: '#fff',
        xAxis3D: {
          type: 'value',
          name: 'E',
          nameTextStyle: { fontSize: 12 },
          axisLabel: { fontSize: 10 }
        },
        yAxis3D: {
          type: 'value',
          name: 'N',
          nameTextStyle: { fontSize: 12 },
          axisLabel: { fontSize: 10 }
        },
        zAxis3D: {
          type: 'value',
          name: 'D',
          nameTextStyle: { fontSize: 12 },
          axisLabel: { fontSize: 10 }
        },
        grid3D: {
          viewControl: {
            autoRotate: true,
            autoRotateSpeed: 2,
            rotateSensitivity: 1,
            zoomSensitivity: 1
          },
          axisPointer: { show: true },
          light: {
            main: { intensity: 1.2 },
            ambient: { intensity: 0.3 }
          }
        },
        series
      }

      this.trajectoryChart.setOption(option)

      window.addEventListener('resize', () => {
        if (this.trajectoryChart) this.trajectoryChart.resize()
      })
    },
    handleDesignSuccess (result) {
      this.closePolling()
      this.designResult = result
      this.designLoading = false
      this.showProgressModal = false
      this.currentStep = 4
      this.$message.success('轨迹设计完成')

      // 延迟初始化图表，确保DOM已渲染
      setTimeout(() => {
        this.initTrajectoryChart()
      }, 300)
    },
    saveAsDesign () {
      this.$message.success('已保存为设计井（模拟）')
    },
    exportReport () {
      this.$message.success('报告导出中（模拟）')
    }
  }
}
</script>

<style lang="less" scoped>
.steps {
  width: 100%;
  max-width: 100%;
  margin: 16px 0 24px;
  padding: 0 8px;
}
.steps ::v-deep .ant-steps-item {
  flex: 1;
  min-width: 100px;
}
.steps ::v-deep .ant-steps-item-title {
  white-space: normal;
  padding-right: 8px;
  line-height: 1.3;
}
.content {
  min-height: 320px;
}
.step-form {
  max-width: 720px;
  margin: 0 auto;
}
.step-desc {
  font-size: 13px;
  margin-bottom: 16px;
  line-height: 1.5;
}
.step-form .form-item-spaced {
  margin-bottom: 18px;
}
.step-form .input-narrow {
  width: 100%;
  max-width: 200px;
}
.step-form .input-narrow.full-width {
  max-width: none;
}
.step-form .algo-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.step-form .algo-row.algo-row-table {
  align-items: flex-start;
}
.step-form .algo-label {
  flex-shrink: 0;
  min-width: 180px;
  margin: 0;
  font-weight: normal;
  color: rgba(0, 0, 0, 0.85);
}
.step-form .algo-label .required {
  color: #f5222d;
  margin-right: 4px;
}
.step-form .algo-input {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.step-form .algo-input-inner {
  width: 100%;
  max-width: 280px;
}
.step-form .algo-input-inner.algo-input-range {
  max-width: 100px;
}
.step-form .algo-input-inner.algo-input-full {
  max-width: none;
}
.step-form .range-sep {
  margin: 0 10px;
}
.step-form .input-range {
  max-width: 100px;
}
.step-form .range-sep {
  margin: 0 10px;
}
.step-actions {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.step-actions .ant-btn + .ant-btn {
  margin-left: 0;
}
.step-form .ant-divider {
  margin: 16px 0 12px 0;
}
.result-actions .ant-btn + .ant-btn {
  margin-left: 10px;
}
.result-actions {
  margin-top: 16px;
}
.trajectory-chart {
  margin-top: 24px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fff;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
  }
}
.legend {
  display: flex;
  gap: 16px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}
.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.chart-container {
  width: 100%;
  height: 400px;
}

.progress-container {
  padding: 16px;
}
.progress-header {
  text-align: center;
  margin-bottom: 24px;
}
.progress-info {
  margin-bottom: 16px;
}
.progress-message {
  text-align: center;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 12px;
}
.progress-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}
.progress-label {
  color: rgba(0, 0, 0, 0.65);
}
.progress-value {
  color: rgba(0, 0, 0, 0.85);
  font-weight: 500;
}
.progress-percent {
  text-align: center;
  font-size: 14px;
  color: #1890ff;
  margin-top: 8px;
}
</style>
