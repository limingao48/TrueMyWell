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
          <a-alert
            v-if="form.algorithm.type === 'GA-optiGAN'"
            type="info"
            show-icon
            class="algo-hint"
            message="GA-optiGAN 由 Java 调用本机 Python（需 numpy、torch）。请在 optimization 目录执行 pip install -r requirements-ga-optigan.txt，并在 api/application.yml 配置 python-executable 为该解释器完整路径；可用 check_ga_optigan_env.py 自检。"
          />

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
              <div v-if="form.algorithm.type === 'GA-optiGAN'" class="algo-row">
                <label class="algo-label">最大评估次数：</label>
                <div class="algo-input">
                  <a-input-number
                    v-model="form.algorithm.maxEvaluations"
                    :min="5000"
                    :max="500000"
                    :step="1000"
                    class="algo-input-inner"
                    placeholder="如 30000"
                  />
                </div>
              </div>
              <div v-else class="algo-row">
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
          <a-descriptions
            v-if="designResult"
            title="七段式设计参数（12 参数）"
            bordered
            size="small"
            :column="2"
            style="margin-top: 16px"
          >
            <a-descriptions-item v-for="item in orderedDesignParameters" :key="item.key" :label="item.label">
              {{ formatNumber(item.value) }}
            </a-descriptions-item>
          </a-descriptions>

          <div v-if="designResult" style="margin-top: 16px">
            <a-space>
              <span>入靶偏差：{{ formatNumber(designResult.final_deviation) }} m</span>
              <span>优化耗时：{{ formatNumber(designResult.optimization_time) }} s</span>
            </a-space>
          </div>

          <div v-if="designResult" class="trajectory-chart">
            <div class="chart-header">
              <h4>3D 轨迹图（含邻井叠加）</h4>
              <div class="legend">
                <span v-for="(seriesItem, index) in trajectorySeriesList" :key="seriesItem.name" class="legend-item">
                  <span class="legend-color" :style="{ backgroundColor: getSeriesColor(index) }"></span>
                  <span>{{ seriesItem.name }}</span>
                </span>
              </div>
            </div>
            <div ref="trajectoryChart" class="chart-container"></div>
          </div>

          <div v-if="designResult" class="result-actions">
            <a-button type="primary" icon="save" @click="openPendingSaveModal">保存为待钻井</a-button>
            <a-button icon="file-pdf" :loading="reportExporting" @click="exportReport">导出报告</a-button>
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

    <a-modal
      title="保存为待钻井"
      :visible="showPendingSaveModal"
      :confirm-loading="pendingSaveSubmitting"
      ok-text="保存"
      cancel-text="取消"
      @ok="confirmSavePending"
      @cancel="closePendingSaveModal"
    >
      <a-form layout="vertical">
        <a-form-item label="待钻井名称" required>
          <a-input v-model="pendingSaveName" placeholder="请输入名称" allow-clear />
        </a-form-item>
        <p style="margin: 0; color: rgba(0,0,0,.45); font-size: 12px; line-height: 1.6">
          待钻井必须归属当前设计所选井场（与第一步「选择井场」一致）。保存后服务端将根据设计井坐标生成标准「井斜数据表」（工作表名与文件名均含此称谓），包含测深、井斜角、网格方位并入库。
        </p>
      </a-form>
    </a-modal>

    <div v-if="designResult" ref="reportRoot" class="report-export-root">
      <div class="report-render-stage" aria-hidden="true">
        <div ref="planChart" class="report-render-chart"></div>
        <div ref="profileChart" class="report-render-chart"></div>
      </div>

      <div class="report-page">
        <div class="report-page-header">
          <div class="report-title">井轨迹设计报告</div>
          <div class="report-subtitle">
            井场：{{ currentSiteName || '未命名井场' }} ｜ 生成时间：{{ reportDisplayTime }} ｜ 防碰约束：{{ getAnticollisionSummary() }}
          </div>
        </div>

        <div class="report-section">
          <div class="report-section-title">1. 基础信息</div>
          <div class="report-info-grid">
            <div v-for="item in reportBasicInfoItems" :key="`basic-${item.label}`" class="report-data-card">
              <div class="report-data-label">{{ item.label }}</div>
              <div class="report-data-value">{{ item.value }}</div>
            </div>
          </div>
        </div>

        <div class="report-section">
          <div class="report-section-title">2. 七段式设计参数（12 参数）</div>
          <div class="report-parameter-grid">
            <div v-for="item in orderedDesignParameters" :key="`param-${item.key}`" class="report-data-card">
              <div class="report-data-label">{{ item.label }}</div>
              <div class="report-data-value">{{ formatNumber(item.value) }}</div>
            </div>
          </div>
        </div>

        <div class="report-section">
          <div class="report-section-title">3. 设计摘要</div>
          <div class="report-summary-grid">
            <div v-for="item in reportSummaryItems" :key="`summary-${item.label}`" class="report-data-card">
              <div class="report-data-label">{{ item.label }}</div>
              <div class="report-data-value">{{ item.value }}</div>
            </div>
          </div>
        </div>

        <div class="report-footer">第 1 页</div>
      </div>

      <div class="report-page">
        <div class="report-page-header">
          <div class="report-title">井轨迹设计图件</div>
          <div class="report-subtitle">三维视图、水平投影图与垂直剖面图</div>
        </div>

        <div class="report-section">
          <div class="report-section-title">4. 图件输出</div>

          <div class="report-chart-card">
            <div class="report-chart-title">4.1 三维轨迹图（含邻井叠加）</div>
            <img
              v-if="reportAssets.trajectory3d"
              :src="reportAssets.trajectory3d"
              alt="三维轨迹图"
              class="report-chart-image report-chart-image-large"
            >
          </div>

          <div class="report-chart-grid">
            <div class="report-chart-card">
              <div class="report-chart-title">4.2 水平投影图</div>
              <img
                v-if="reportAssets.plan"
                :src="reportAssets.plan"
                alt="水平投影图"
                class="report-chart-image"
              >
            </div>

            <div class="report-chart-card">
              <div class="report-chart-title">4.3 垂直剖面图（剖面方位 {{ formatNumber(reportSectionAzimuth) }}°）</div>
              <img
                v-if="reportAssets.profile"
                :src="reportAssets.profile"
                alt="垂直剖面图"
                class="report-chart-image"
              >
            </div>
          </div>
        </div>

        <div class="report-footer">第 2 页</div>
      </div>

      <div v-for="(chunk, chunkIndex) in reportSurveyChunks" :key="`survey-${chunkIndex}`" class="report-page">
        <div class="report-page-header">
          <div class="report-title">关键轨迹测点表</div>
          <div class="report-subtitle">按每 {{ SURVEY_SAMPLE_INTERVAL }} m 测量井深采样，并保留各段起点及最终靶点</div>
        </div>

        <div class="report-section report-section-flex">
          <div class="report-section-title">5. 关键轨迹测点（测深、井斜角、网格方位、狗腿角）</div>
          <table class="report-table">
            <thead>
              <tr>
                <th>序号</th>
                <th>测深 MD(m)</th>
                <th>井斜角(°)</th>
                <th>网格方位(°)</th>
                <th>垂深 TVD(m)</th>
                <th>北坐标 N(m)</th>
                <th>东坐标 E(m)</th>
                <th>狗腿角（°/30m）</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in chunk" :key="`row-${chunkIndex}-${rowIndex}`">
                <td>{{ chunkIndex * SURVEY_ROWS_PER_PAGE + rowIndex + 1 }}</td>
                <td>{{ formatNumber(row.md) }}</td>
                <td>{{ formatNumber(row.inc) }}</td>
                <td>{{ formatNumber(row.azi) }}</td>
                <td>{{ formatNumber(row.tvd) }}</td>
                <td>{{ formatNumber(row.n) }}</td>
                <td>{{ formatNumber(row.e) }}</td>
                <td>{{ formatNumber(row.doglegSeverity) }}</td>
              </tr>
              <tr v-if="!chunk.length">
                <td colspan="8" class="report-empty">暂无轨迹采样点</td>
              </tr>
            </tbody>
          </table>
          <div class="report-table-note">
            注：表中狗腿角（°/30m）直接取自七段式设计参数中该点所属井段对应的狗腿值；直井段和稳斜段狗腿角记为 0。
          </div>
        </div>

        <div class="report-footer">第 {{ chunkIndex + 3 }} 页</div>
      </div>
    </div>
  </page-header-wrapper>
</template>

<script>
import { drillingAPI } from '@/api'
import TrajectoryDesignRequest from '@/entity/TrajectoryDesignRequest'
import { createImagePdfFromPages } from '@/utils/imagePdf'
import html2canvas from 'html2canvas'
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

const PARAM_ORDER = ['L0', 'DLS1', 'alpha3', 'L3', 'DLS_turn', 'L4', 'L5', 'DLS6', 'alpha_e', 'L7', 'phi_init', 'phi_target']
const CHART_COLORS = ['#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#faad14', '#f5222d']
const REPORT_PAGE_WIDTH = 794
const REPORT_PAGE_HEIGHT = 1123
const SURVEY_SAMPLE_INTERVAL = 100
const SURVEY_ROWS_PER_PAGE = 18

function toNumber (value, fallback = 0) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

function clamp (value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function toRadians (value) {
  return toNumber(value, 0) * Math.PI / 180
}

function normalizeAzimuth (value) {
  let azimuth = toNumber(value, 0) % 360
  if (azimuth < 0) azimuth += 360
  return azimuth
}

function formatDateTime (date) {
  const value = date instanceof Date ? date : new Date(date)
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  const hour = String(value.getHours()).padStart(2, '0')
  const minute = String(value.getMinutes()).padStart(2, '0')
  const second = String(value.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

function formatDisplayNumber (value, digits = 2) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '-'
  return numeric.toFixed(digits).replace(/\.?0+$/, '')
}

function getSolutionValue (solution, key) {
  if (!solution) return undefined
  if (solution[key] !== undefined) return solution[key]
  const prefixedKey = key.indexOf('seven_') === 0 ? key : `seven_${key}`
  if (solution[prefixedKey] !== undefined) return solution[prefixedKey]
  return undefined
}

function normalizeTrajectoryPoints (points) {
  if (!Array.isArray(points)) return []
  return points.map((point) => {
    const x = point && point.x !== undefined ? point.x : point && point.e !== undefined ? point.e : 0
    const y = point && point.y !== undefined ? point.y : point && point.n !== undefined ? point.n : 0
    const z = point && point.z !== undefined ? point.z : point && point.d !== undefined ? point.d : 0
    return {
      x: toNumber(x, 0),
      y: toNumber(y, 0),
      z: toNumber(z, 0)
    }
  })
}

function getWellDisplayName (well, fallback) {
  if (!well) return fallback
  return well.wellName || well.wellNo || fallback
}

function buildTrajectorySeriesList (designResult) {
  const seriesList = []
  const designPoints = normalizeTrajectoryPoints(designResult && designResult.trajectory_points)
  if (designPoints.length) {
    seriesList.push({
      name: '设计井',
      points: designPoints,
      isDesign: true
    })
  }

  const neighborWells = designResult && Array.isArray(designResult.neighbor_wells) ? designResult.neighbor_wells : []
  neighborWells.forEach((well, index) => {
    const points = normalizeTrajectoryPoints(well.trajectory_points)
    if (points.length) {
      seriesList.push({
        name: getWellDisplayName(well, `邻井${index + 1}`),
        points,
        isDesign: false
      })
    }
  })

  return seriesList
}

function calculateTrajectoryLength (points) {
  const normalizedPoints = normalizeTrajectoryPoints(points)
  let totalLength = 0
  for (let i = 1; i < normalizedPoints.length; i++) {
    const deltaE = normalizedPoints[i].x - normalizedPoints[i - 1].x
    const deltaN = normalizedPoints[i].y - normalizedPoints[i - 1].y
    const deltaD = normalizedPoints[i].z - normalizedPoints[i - 1].z
    totalLength += Math.sqrt(deltaE * deltaE + deltaN * deltaN + deltaD * deltaD)
  }
  return totalLength
}

function deriveSectionAzimuth (designResult, wellhead, target) {
  const solution = designResult && designResult.best_solution_dict
  const solutionAzimuth = getSolutionValue(solution, 'phi_target')
  if (solutionAzimuth !== undefined) {
    return normalizeAzimuth(solutionAzimuth)
  }

  const points = normalizeTrajectoryPoints(designResult && designResult.trajectory_points)
  if (points.length > 1) {
    const firstPoint = points[0]
    const lastPoint = points[points.length - 1]
    const deltaE = lastPoint.x - firstPoint.x
    const deltaN = lastPoint.y - firstPoint.y
    if (Math.abs(deltaE) > 1e-6 || Math.abs(deltaN) > 1e-6) {
      return normalizeAzimuth(Math.atan2(deltaE, deltaN) * 180 / Math.PI)
    }
  }

  const deltaTargetE = toNumber(target && target.e, 0) - toNumber(wellhead && wellhead.e, 0)
  const deltaTargetN = toNumber(target && target.n, 0) - toNumber(wellhead && wellhead.n, 0)
  if (Math.abs(deltaTargetE) > 1e-6 || Math.abs(deltaTargetN) > 1e-6) {
    return normalizeAzimuth(Math.atan2(deltaTargetE, deltaTargetN) * 180 / Math.PI)
  }

  return 0
}

function buildPlanProjection (points, wellhead) {
  const baseE = toNumber(wellhead && wellhead.e, 0)
  const baseN = toNumber(wellhead && wellhead.n, 0)
  return normalizeTrajectoryPoints(points).map(point => [point.x - baseE, point.y - baseN])
}

function buildVerticalSectionProjection (points, wellhead, azimuthDeg) {
  const baseE = toNumber(wellhead && wellhead.e, 0)
  const baseN = toNumber(wellhead && wellhead.n, 0)
  const azimuthRad = normalizeAzimuth(azimuthDeg) * Math.PI / 180

  return normalizeTrajectoryPoints(points).map((point) => {
    const deltaE = point.x - baseE
    const deltaN = point.y - baseN
    const sectionOffset = deltaE * Math.sin(azimuthRad) + deltaN * Math.cos(azimuthRad)
    // 纵轴使用绝对垂深 D（与后端 trajectory、表单靶点垂深、测点表 TVD 一致）；横轴仍为相对设计井口的剖面位移
    return [sectionOffset, point.z]
  })
}

function buildSurveySegments (points) {
  const normalizedPoints = normalizeTrajectoryPoints(points)
  if (normalizedPoints.length < 2) {
    return {
      points: normalizedPoints,
      segments: [],
      totalMd: 0
    }
  }

  const segments = []
  let totalMd = 0
  let lastAzimuth = 0

  for (let i = 1; i < normalizedPoints.length; i++) {
    const startPoint = normalizedPoints[i - 1]
    const endPoint = normalizedPoints[i]
    const deltaE = endPoint.x - startPoint.x
    const deltaN = endPoint.y - startPoint.y
    const deltaD = endPoint.z - startPoint.z
    const length = Math.sqrt(deltaE * deltaE + deltaN * deltaN + deltaD * deltaD)
    if (length < 1e-9) continue

    const horizontalLength = Math.sqrt(deltaE * deltaE + deltaN * deltaN)
    const inclination = Math.acos(clamp(deltaD / length, -1, 1)) * 180 / Math.PI
    const azimuth = horizontalLength > 1e-9 ? normalizeAzimuth(Math.atan2(deltaE, deltaN) * 180 / Math.PI) : lastAzimuth

    segments.push({
      index: segments.length,
      startMd: totalMd,
      endMd: totalMd + length,
      length,
      inc: inclination,
      azi: azimuth,
      startPoint,
      endPoint
    })

    totalMd += length
    lastAzimuth = azimuth
  }

  return {
    points: normalizedPoints,
    segments,
    totalMd
  }
}

function buildSevenSegmentDefinitions (solution, totalMd) {
  const fallbackTotal = Math.max(toNumber(totalMd, 0), 0)
  if (!solution) {
    return [{
      segmentIndex: 1,
      label: '第1段直井段',
      startMd: 0,
      endMd: fallbackTotal,
      doglegSeverity: 0
    }]
  }

  const L0 = Math.max(0, toNumber(getSolutionValue(solution, 'L0'), 0))
  const DLS1 = Math.max(0, toNumber(getSolutionValue(solution, 'DLS1'), 0))
  const alpha3 = clamp(toNumber(getSolutionValue(solution, 'alpha3'), 0), 0, 89)
  const L3 = Math.max(0, toNumber(getSolutionValue(solution, 'L3'), 0))
  const dlsTurn = Math.max(0, toNumber(getSolutionValue(solution, 'DLS_turn'), 0))
  const L5 = Math.max(0, toNumber(getSolutionValue(solution, 'L5'), 0))
  const DLS6 = Math.max(0, toNumber(getSolutionValue(solution, 'DLS6'), 0))
  const alphaE = clamp(toNumber(getSolutionValue(solution, 'alpha_e'), 0), 0, 89)
  const L7 = Math.max(0, toNumber(getSolutionValue(solution, 'L7'), 0))
  const phiInit = normalizeAzimuth(getSolutionValue(solution, 'phi_init'))
  const phiTarget = normalizeAzimuth(getSolutionValue(solution, 'phi_target'))

  const L1 = DLS1 > 1e-9 ? Math.abs(alpha3) / (DLS1 / 30) : 0
  const deltaPhiTarget = ((phiTarget - phiInit + 180) % 360) - 180
  const sinAlpha = Math.max(Math.sin(toRadians(Math.max(alpha3, 1e-3))), 1e-3)
  const L4Used = dlsTurn > 1e-9 ? Math.abs(deltaPhiTarget) * sinAlpha / Math.abs(dlsTurn / 30) : 0
  const L6 = DLS6 > 1e-9 ? Math.abs(alphaE - alpha3) / (DLS6 / 30) : 0
  const rawLengths = [L0, L1, L3, L4Used, L5, L6, L7]
  const labels = [
    '第1段直井段',
    '第2段增斜段',
    '第3段稳斜段',
    '第4段扭方位段',
    '第5段扭方位后稳斜段',
    '第6段井斜调整段',
    '第7段末端稳斜段'
  ]
  const segmentDoglegs = [0, DLS1, 0, dlsTurn, 0, DLS6, 0]
  const rawTotalMd = rawLengths.reduce((sum, length) => sum + length, 0)
  const normalizedTotalMd = fallbackTotal > 0 ? fallbackTotal : rawTotalMd
  const scale = rawTotalMd > 1e-9 ? normalizedTotalMd / rawTotalMd : 1

  const definitions = []
  let cumulativeMd = 0
  labels.forEach((label, index) => {
    const isLast = index === labels.length - 1
    const scaledLength = rawLengths[index] * scale
    const endMd = isLast ? normalizedTotalMd : cumulativeMd + scaledLength
    definitions.push({
      segmentIndex: index + 1,
      label,
      startMd: cumulativeMd,
      endMd,
      doglegSeverity: segmentDoglegs[index]
    })
    cumulativeMd = endMd
  })

  return definitions
}

function buildSevenSegmentKeyNodeSpecs (segmentDefinitions) {
  if (!Array.isArray(segmentDefinitions) || !segmentDefinitions.length) {
    return [{ md: 0, label: '最终靶点', preferOutgoingSegment: false }]
  }

  const specs = segmentDefinitions.map(segment => ({
    md: segment.startMd,
    label: `${segment.label}起点`,
    preferOutgoingSegment: true
  }))

  specs.push({
    md: segmentDefinitions[segmentDefinitions.length - 1].endMd,
    label: '最终靶点',
    preferOutgoingSegment: false
  })

  return specs
}

function mergeSurveySpecs (intervalSpecs, keyNodeSpecs, totalMd) {
  const mergedMap = new Map()
  const normalizeDepth = (md) => {
    const clamped = clamp(toNumber(md, 0), 0, totalMd)
    return Number(clamped.toFixed(6))
  }

  const pushSpec = (spec) => {
    const md = normalizeDepth(spec.md)
    const key = md.toFixed(6)
    if (!mergedMap.has(key)) {
      mergedMap.set(key, {
        md,
        labels: [],
        preferOutgoingSegment: false
      })
    }
    const target = mergedMap.get(key)
    if (spec.label && !target.labels.includes(spec.label)) {
      target.labels.push(spec.label)
    }
    target.preferOutgoingSegment = target.preferOutgoingSegment || Boolean(spec.preferOutgoingSegment)
  }

  intervalSpecs.forEach(pushSpec)
  keyNodeSpecs.forEach(pushSpec)

  return Array.from(mergedMap.values())
    .sort((a, b) => a.md - b.md)
    .map(item => ({
      md: item.md,
      nodeLabel: item.labels.length ? item.labels.join('；') : '间隔采样点',
      preferOutgoingSegment: item.preferOutgoingSegment
    }))
}

function resolveSurveySegment (md, segments, preferOutgoingSegment) {
  if (!segments.length) return null
  const epsilon = 1e-6

  if (md <= epsilon) {
    return segments[0]
  }

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i]
    const startHit = Math.abs(md - segment.startMd) <= epsilon
    const endHit = Math.abs(md - segment.endMd) <= epsilon

    if (startHit && preferOutgoingSegment) {
      return segment
    }

    if (md > segment.startMd + epsilon && md < segment.endMd - epsilon) {
      return segment
    }

    if (endHit) {
      if (preferOutgoingSegment && i + 1 < segments.length) {
        return segments[i + 1]
      }
      return segment
    }
  }

  return segments[segments.length - 1]
}

function resolveDesignSegment (md, segmentDefinitions, preferOutgoingSegment) {
  if (!Array.isArray(segmentDefinitions) || !segmentDefinitions.length) return null
  const epsilon = 1e-6

  if (md <= epsilon) {
    return segmentDefinitions[0]
  }

  for (let i = 0; i < segmentDefinitions.length; i++) {
    const segment = segmentDefinitions[i]
    const startHit = Math.abs(md - segment.startMd) <= epsilon
    const endHit = Math.abs(md - segment.endMd) <= epsilon

    if (startHit && preferOutgoingSegment) {
      return segment
    }

    if (md > segment.startMd + epsilon && md < segment.endMd - epsilon) {
      return segment
    }

    if (endHit) {
      if (preferOutgoingSegment && i + 1 < segmentDefinitions.length) {
        return segmentDefinitions[i + 1]
      }
      return segment
    }
  }

  return segmentDefinitions[segmentDefinitions.length - 1]
}

function interpolateSurveyRow (spec, segments, firstPoint, segmentDefinitions) {
  const md = toNumber(spec && spec.md, 0)
  const designSegment = resolveDesignSegment(md, segmentDefinitions, spec && spec.preferOutgoingSegment)
  if (md <= 0 || !segments.length) {
    return {
      md: 0,
      inc: 0,
      azi: 0,
      doglegSeverity: designSegment ? designSegment.doglegSeverity : 0,
      tvd: firstPoint.z,
      e: firstPoint.x,
      n: firstPoint.y
    }
  }

  const segment = resolveSurveySegment(md, segments, spec && spec.preferOutgoingSegment)
  const segmentMd = clamp(md - segment.startMd, 0, segment.length)
  const ratio = segment.length > 1e-9 ? segmentMd / segment.length : 0

  return {
    md,
    inc: segment.inc,
    azi: segment.azi,
    doglegSeverity: designSegment ? designSegment.doglegSeverity : 0,
    tvd: segment.startPoint.z + (segment.endPoint.z - segment.startPoint.z) * ratio,
    e: segment.startPoint.x + (segment.endPoint.x - segment.startPoint.x) * ratio,
    n: segment.startPoint.y + (segment.endPoint.y - segment.startPoint.y) * ratio
  }
}

function buildSurveyRows (points, solution, interval = SURVEY_SAMPLE_INTERVAL) {
  const { points: normalizedPoints, segments, totalMd } = buildSurveySegments(points)
  const segmentDefinitions = buildSevenSegmentDefinitions(solution, totalMd)
  if (!normalizedPoints.length) return []
  if (normalizedPoints.length === 1) {
    return [{
      md: 0,
      inc: 0,
      azi: 0,
      doglegSeverity: segmentDefinitions.length ? segmentDefinitions[0].doglegSeverity : 0,
      tvd: normalizedPoints[0].z,
      e: normalizedPoints[0].x,
      n: normalizedPoints[0].y
    }]
  }

  if (!segments.length) {
    return [{
      md: 0,
      inc: 0,
      azi: 0,
      doglegSeverity: segmentDefinitions.length ? segmentDefinitions[0].doglegSeverity : 0,
      tvd: normalizedPoints[0].z,
      e: normalizedPoints[0].x,
      n: normalizedPoints[0].y
    }]
  }

  const intervalSpecs = [{ md: 0, label: '间隔采样点', preferOutgoingSegment: true }]
  for (let md = interval; md < totalMd - 1e-6; md += interval) {
    intervalSpecs.push({
      md,
      label: '间隔采样点',
      preferOutgoingSegment: false
    })
  }
  intervalSpecs.push({
    md: totalMd,
    label: '间隔采样点',
    preferOutgoingSegment: false
  })

  const keyNodeSpecs = buildSevenSegmentKeyNodeSpecs(segmentDefinitions)
  const mergedSpecs = mergeSurveySpecs(intervalSpecs, keyNodeSpecs, totalMd)
  return mergedSpecs.map(spec => interpolateSurveyRow(spec, segments, normalizedPoints[0], segmentDefinitions))
}

function splitIntoChunks (list, size) {
  if (!Array.isArray(list) || !list.length) return [[]]
  const chunks = []
  for (let i = 0; i < list.length; i += size) {
    chunks.push(list.slice(i, i + size))
  }
  return chunks
}

export default {
  name: 'TrajectoryDesign',
  data () {
    return {
      currentStep: 0,
      designLoading: false,
      reportExporting: false,
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
          maxEvaluations: 30000,
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
      trajectoryChart: null,
      planChart: null,
      profileChart: null,
      resultChartResizeHandler: null,
      pollingTimeout: null,
      activePollingKey: null,
      currentTaskId: null,
      showPendingSaveModal: false,
      pendingSaveName: '',
      pendingSaveSubmitting: false,
      reportGeneratedAt: '',
      reportAssets: {
        trajectory3d: '',
        plan: '',
        profile: ''
      },
      SURVEY_SAMPLE_INTERVAL,
      SURVEY_ROWS_PER_PAGE
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
    },
    currentStep (step) {
      if (step === 4 && this.designResult) {
        this.$nextTick(() => {
          if (this.currentStep === 4 && this.designResult) {
            this.initResultCharts()
          }
        })
        return
      }
      this.destroyResultCharts()
    }
  },
  created () {
    this.loadSiteList()
  },
  beforeDestroy () {
    this.closePolling()
    this.destroyResultCharts()
  },
  computed: {
    currentSiteName () {
      const site = this.siteList.find(item => String(item.id) === String(this.form.siteId))
      return site ? site.name : ''
    },
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
    },
    orderedDesignParameters () {
      const solution = this.designResult && this.designResult.best_solution_dict
      return PARAM_ORDER.map((key) => ({
        key,
        label: this.paramLabels[key] || key,
        value: getSolutionValue(solution, key)
      }))
    },
    trajectorySeriesList () {
      return buildTrajectorySeriesList(this.designResult)
    },
    reportSectionAzimuth () {
      return deriveSectionAzimuth(this.designResult, this.form.wellhead, this.form.target)
    },
    trajectoryTotalLength () {
      return calculateTrajectoryLength(this.designResult && this.designResult.trajectory_points)
    },
    surveyRows () {
      return buildSurveyRows(
        this.designResult && this.designResult.trajectory_points,
        this.designResult && this.designResult.best_solution_dict,
        SURVEY_SAMPLE_INTERVAL
      )
    },
    reportSurveyChunks () {
      return splitIntoChunks(this.surveyRows, SURVEY_ROWS_PER_PAGE)
    },
    reportNeighborNames () {
      return this.trajectorySeriesList
        .filter(item => !item.isDesign)
        .map(item => item.name)
    },
    reportDisplayTime () {
      return this.reportGeneratedAt || formatDateTime(new Date())
    },
    reportBasicInfoItems () {
      return [
        { label: '井场', value: this.currentSiteName || '-' },
        { label: '优化算法', value: this.form.algorithm.type || '-' },
        { label: '井口坐标', value: this.formatCoordinate(this.form.wellhead) },
        { label: '靶点坐标', value: this.formatCoordinate(this.form.target) },
        {
          label: '入靶井斜范围',
          value: this.formatRange(this.form.landingRequirement.inclinationMin, this.form.landingRequirement.inclinationMax, 2, '°')
        },
        {
          label: '网格方位范围',
          value: this.formatRange(this.form.landingRequirement.azimuthMin, this.form.landingRequirement.azimuthMax, 2, '°')
        },
        { label: '防碰约束', value: this.getAnticollisionSummary() },
        {
          label: '邻井信息',
          value: this.reportNeighborNames.length ? this.reportNeighborNames.join('、') : '未选择邻井'
        }
      ]
    },
    reportSummaryItems () {
      return [
        { label: '轨迹总井深', value: `${this.formatNumber(this.trajectoryTotalLength)} m` },
        { label: '入靶偏差', value: `${this.formatNumber(this.designResult && this.designResult.final_deviation)} m` },
        { label: '优化耗时', value: `${this.formatNumber(this.designResult && this.designResult.optimization_time)} s` },
        { label: '剖面方位', value: `${this.formatNumber(this.reportSectionAzimuth)} °` },
        { label: '最小造斜深度', value: `${this.formatNumber(this.form.algorithm.minKickoffDepth)} m` },
        {
          label: '狗腿度范围',
          value: `${this.formatNumber(this.form.algorithm.doglegMin)} ~ ${this.formatNumber(this.form.algorithm.doglegMax)} °/30m`
        }
      ]
    }
  },
  methods: {
    formatNumber (value, digits = 2) {
      return formatDisplayNumber(value, digits)
    },
    formatCoordinate (point) {
      if (!point) return '-'
      return `E ${this.formatNumber(point.e)} m，N ${this.formatNumber(point.n)} m，D ${this.formatNumber(point.d)} m`
    },
    formatRange (min, max, digits = 2, unit = '') {
      const suffix = unit ? ` ${unit}` : ''
      return `${this.formatNumber(min, digits)} ~ ${this.formatNumber(max, digits)}${suffix}`
    },
    normalizeListResponse (res) {
      if (Array.isArray(res)) return res
      if (res && Array.isArray(res.data)) return res.data
      return []
    },
    getSeriesColor (index) {
      return CHART_COLORS[index % CHART_COLORS.length]
    },
    getAnticollisionSummary () {
      if (this.form.algorithm.anticollisionMethod === 'CTC') {
        return `CTC 井眼中心距法，最小安全半径 ${this.formatNumber(this.form.algorithm.safeRadius)} m`
      }
      return `SF 分离系数法，最小 SF ${this.formatNumber(this.form.algorithm.minSafetyFactor)}`
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
      this.resetReportAssets()
      this.progressInfo = {
        iteration: 0,
        totalIterations: this.form.algorithm.type === 'GA-optiGAN'
          ? (this.form.algorithm.maxEvaluations || 30000)
          : (this.form.algorithm.iterations || 200),
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
      this.currentTaskId = taskId
      const pollingKey = `${taskId}_${Date.now()}`
      this.activePollingKey = pollingKey

      const poll = async () => {
        if (this.activePollingKey !== pollingKey || this.currentTaskId !== taskId) {
          return
        }

        try {
          const progress = await drillingAPI.getDesignStatus(taskId)
          if (this.activePollingKey !== pollingKey || this.currentTaskId !== taskId) {
            return
          }

          this.progressInfo = {
            iteration: progress.iteration || 0,
            totalIterations: progress.totalIterations || (this.form.algorithm.type === 'GA-optiGAN'
              ? (this.form.algorithm.maxEvaluations || 30000)
              : (this.form.algorithm.iterations || 200)),
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
            return
          }

          this.pollingTimeout = setTimeout(poll, 500)
        } catch (err) {
          if (this.activePollingKey !== pollingKey || this.currentTaskId !== taskId) {
            return
          }
          this.closePolling()
          this.handleDesignError(err)
        }
      }

      poll()
    },
    handleDesignError (err) {
      this.closePolling()
      this.showProgressModal = false
      this.designLoading = false
      this.currentTaskId = null
      this.$message.error('轨迹设计失败：' + (err.message || '未知错误'))
    },
    closePolling () {
      this.activePollingKey = null
      if (this.pollingTimeout) {
        clearTimeout(this.pollingTimeout)
        this.pollingTimeout = null
      }
    },
    resetReportAssets () {
      this.reportGeneratedAt = ''
      this.reportAssets = {
        trajectory3d: '',
        plan: '',
        profile: ''
      }
    },
    resizeResultCharts () {
      if (this.trajectoryChart) this.trajectoryChart.resize()
      if (this.planChart) this.planChart.resize()
      if (this.profileChart) this.profileChart.resize()
    },
    attachResultChartResizeHandler () {
      if (this.resultChartResizeHandler) return
      this.resultChartResizeHandler = () => {
        this.resizeResultCharts()
      }
      window.addEventListener('resize', this.resultChartResizeHandler)
    },
    destroyResultCharts () {
      if (this.trajectoryChart) {
        this.trajectoryChart.dispose()
        this.trajectoryChart = null
      }
      if (this.planChart) {
        this.planChart.dispose()
        this.planChart = null
      }
      if (this.profileChart) {
        this.profileChart.dispose()
        this.profileChart = null
      }
      if (this.resultChartResizeHandler) {
        window.removeEventListener('resize', this.resultChartResizeHandler)
        this.resultChartResizeHandler = null
      }
    },
    initResultCharts () {
      if (!this.designResult) return
      this.initTrajectoryChart()
      this.initPlanChart()
      this.initProfileChart()
      this.attachResultChartResizeHandler()
    },
    initTrajectoryChart () {
      if (!this.$refs.trajectoryChart || !this.trajectorySeriesList.length) return

      if (this.trajectoryChart) {
        this.trajectoryChart.dispose()
      }
      this.trajectoryChart = echarts.init(this.$refs.trajectoryChart)

      // 绘图第三维用 -z，垂深增大时沿 Z 轴「向下」；物理垂深 D = -Z_plot，与 E/N 数值仍同源
      const series = this.trajectorySeriesList.map((item, index) => ({
        type: 'line3D',
        name: item.name,
        data: item.points.map(point => [point.x, point.y, -point.z]),
        lineStyle: {
          width: item.isDesign ? 4 : 2.5,
          color: this.getSeriesColor(index),
          opacity: item.isDesign ? 1 : 0.72
        },
        itemStyle: {
          opacity: 0.85
        },
        emphasis: {
          lineStyle: {
            width: item.isDesign ? 6 : 4
          }
        }
      }))

      this.trajectoryChart.setOption({
        animation: false,
        tooltip: {
          formatter: (params) => {
            const value = params.value || []
            return [
              `<strong>${params.seriesName}</strong>`,
              `E：${this.formatNumber(value[0])} m`,
              `N：${this.formatNumber(value[1])} m`,
              `D：${this.formatNumber(-value[2])} m`
            ].join('<br/>')
          }
        },
        legend: {
          data: this.trajectorySeriesList.map(item => item.name),
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
          name: '垂深 D (m)',
          nameTextStyle: { fontSize: 12 },
          axisLabel: { fontSize: 10 }
        },
        grid3D: {
          viewControl: {
            autoRotate: false,
            rotateSensitivity: 1,
            zoomSensitivity: 1
          },
          axisPointer: { show: true },
          light: {
            main: { intensity: 1.2 },
            ambient: { intensity: 0.35 }
          }
        },
        series
      })
    },
    initPlanChart () {
      if (!this.$refs.planChart || !this.trajectorySeriesList.length) return

      if (this.planChart) {
        this.planChart.dispose()
      }
      this.planChart = echarts.init(this.$refs.planChart)

      const lineSeries = this.trajectorySeriesList.map((item, index) => ({
        type: 'line',
        name: item.name,
        data: buildPlanProjection(item.points, this.form.wellhead),
        showSymbol: false,
        symbol: 'none',
        lineStyle: {
          width: item.isDesign ? 3 : 2,
          color: this.getSeriesColor(index)
        }
      }))

      const targetData = [[
        toNumber(this.form.target.e, 0) - toNumber(this.form.wellhead.e, 0),
        toNumber(this.form.target.n, 0) - toNumber(this.form.wellhead.n, 0)
      ]]

      this.planChart.setOption({
        animation: false,
        backgroundColor: '#fff',
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const value = params.value || []
            return [
              `<strong>${params.seriesName}</strong>`,
              `东西位移：${this.formatNumber(value[0])} m`,
              `南北位移：${this.formatNumber(value[1])} m`
            ].join('<br/>')
          }
        },
        legend: {
          data: this.trajectorySeriesList.map(item => item.name).concat(['井口', '靶点']),
          bottom: 0
        },
        grid: {
          left: 60,
          right: 24,
          top: 24,
          bottom: 48
        },
        xAxis: {
          type: 'value',
          name: 'East/West [m]',
          splitLine: { lineStyle: { color: '#f0f0f0' } }
        },
        yAxis: {
          type: 'value',
          name: 'South/North [m]',
          splitLine: { lineStyle: { color: '#f0f0f0' } }
        },
        series: lineSeries.concat([
          {
            type: 'scatter',
            name: '井口',
            data: [[0, 0]],
            symbolSize: 10,
            itemStyle: { color: '#2f54eb' },
            label: {
              show: true,
              formatter: '井口',
              position: 'top',
              color: '#2f54eb',
              fontSize: 11
            }
          },
          {
            type: 'scatter',
            name: '靶点',
            data: targetData,
            symbolSize: 12,
            itemStyle: { color: '#cf1322' },
            label: {
              show: true,
              formatter: '靶点',
              position: 'top',
              color: '#cf1322',
              fontSize: 11
            }
          }
        ])
      })
    },
    initProfileChart () {
      if (!this.$refs.profileChart || !this.trajectorySeriesList.length) return

      if (this.profileChart) {
        this.profileChart.dispose()
      }
      this.profileChart = echarts.init(this.$refs.profileChart)

      const lineSeries = this.trajectorySeriesList.map((item, index) => ({
        type: 'line',
        name: item.name,
        data: buildVerticalSectionProjection(item.points, this.form.wellhead, this.reportSectionAzimuth),
        showSymbol: false,
        symbol: 'none',
        lineStyle: {
          width: item.isDesign ? 3 : 2,
          color: this.getSeriesColor(index)
        }
      }))

      const sectionRad = this.reportSectionAzimuth * Math.PI / 180
      const targetSection = (
        (toNumber(this.form.target.e, 0) - toNumber(this.form.wellhead.e, 0)) * Math.sin(sectionRad) +
        (toNumber(this.form.target.n, 0) - toNumber(this.form.wellhead.n, 0)) * Math.cos(sectionRad)
      )

      this.profileChart.setOption({
        animation: false,
        backgroundColor: '#fff',
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const value = params.value || []
            return [
              `<strong>${params.seriesName}</strong>`,
              `剖面位移：${this.formatNumber(value[0])} m`,
              `垂深：${this.formatNumber(value[1])} m`
            ].join('<br/>')
          }
        },
        legend: {
          data: this.trajectorySeriesList.map(item => item.name).concat(['井口', '靶点']),
          bottom: 0
        },
        grid: {
          left: 60,
          right: 24,
          top: 24,
          bottom: 48
        },
        xAxis: {
          type: 'value',
          name: `Vertical Section ${this.formatNumber(this.reportSectionAzimuth)}° [m]`,
          splitLine: { lineStyle: { color: '#f0f0f0' } }
        },
        yAxis: {
          type: 'value',
          name: '垂深 D (m)',
          inverse: true,
          splitLine: { lineStyle: { color: '#f0f0f0' } }
        },
        series: lineSeries.concat([
          {
            type: 'scatter',
            name: '井口',
            data: [[0, toNumber(this.form.wellhead.d, 0)]],
            symbolSize: 10,
            itemStyle: { color: '#2f54eb' },
            label: {
              show: true,
              formatter: '井口',
              position: 'top',
              color: '#2f54eb',
              fontSize: 11
            }
          },
          {
            type: 'scatter',
            name: '靶点',
            data: [[targetSection, toNumber(this.form.target.d, 0)]],
            symbolSize: 12,
            itemStyle: { color: '#cf1322' },
            label: {
              show: true,
              formatter: '靶点',
              position: 'top',
              color: '#cf1322',
              fontSize: 11
            }
          }
        ])
      })
    },
    async waitForViewUpdate () {
      return new Promise(resolve => this.$nextTick(resolve))
    },
    async waitForNextPaint () {
      return new Promise(resolve => {
        requestAnimationFrame(() => {
          requestAnimationFrame(resolve)
        })
      })
    },
    async ensureResultChartsReady () {
      await this.waitForViewUpdate()
      if (!this.trajectoryChart || !this.planChart || !this.profileChart) {
        this.initResultCharts()
        await this.waitForNextPaint()
      }
    },
    async getChartDataUrl (chart, refName) {
      if (chart && typeof chart.getDataURL === 'function') {
        try {
          return chart.getDataURL({
            type: 'jpeg',
            pixelRatio: 2,
            backgroundColor: '#ffffff'
          })
        } catch (e) {
          // ignore and fallback to html2canvas below
        }
      }

      const element = this.$refs[refName]
      if (!element) return ''
      const canvas = await html2canvas(element, {
        scale: 2,
        backgroundColor: '#ffffff',
        useCORS: true
      })
      return canvas.toDataURL('image/jpeg', 0.95)
    },
    async prepareReportAssets () {
      await this.ensureResultChartsReady()
      this.reportGeneratedAt = formatDateTime(new Date())

      const [trajectory3d, plan, profile] = await Promise.all([
        this.getChartDataUrl(this.trajectoryChart, 'trajectoryChart'),
        this.getChartDataUrl(this.planChart, 'planChart'),
        this.getChartDataUrl(this.profileChart, 'profileChart')
      ])

      this.reportAssets = {
        trajectory3d,
        plan,
        profile
      }

      await this.waitForViewUpdate()
      await this.waitForNextPaint()
      await this.waitForReportImages()
    },
    async waitForReportImages () {
      const root = this.$refs.reportRoot
      if (!root) return
      const images = Array.from(root.querySelectorAll('img'))
      if (!images.length) return

      await Promise.all(images.map(image => {
        if (image.complete && image.naturalWidth > 0) return Promise.resolve()
        return new Promise(resolve => {
          image.onload = () => resolve()
          image.onerror = () => resolve()
        })
      }))
    },
    async captureReportPages () {
      const root = this.$refs.reportRoot
      if (!root) {
        throw new Error('报告内容尚未准备完成')
      }

      const pageElements = Array.from(root.querySelectorAll('.report-page'))
      const pageImages = []

      for (const pageElement of pageElements) {
        const canvas = await html2canvas(pageElement, {
          scale: 2,
          backgroundColor: '#ffffff',
          useCORS: true,
          width: REPORT_PAGE_WIDTH,
          height: REPORT_PAGE_HEIGHT,
          windowWidth: REPORT_PAGE_WIDTH,
          windowHeight: REPORT_PAGE_HEIGHT,
          scrollX: 0,
          scrollY: 0
        })

        pageImages.push({
          dataUrl: canvas.toDataURL('image/jpeg', 0.95),
          width: canvas.width,
          height: canvas.height
        })
      }

      return pageImages
    },
    downloadBlob (blob, filename) {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      setTimeout(() => {
        window.URL.revokeObjectURL(url)
      }, 1000)
    },
    buildReportFileName () {
      const siteName = (this.currentSiteName || '井场').replace(/[\\/:*?"<>|]/g, '-')
      const timestamp = this.reportGeneratedAt.replace(/[:\s]/g, '-')
      return `${siteName}_井轨迹设计报告_${timestamp}.pdf`
    },
    handleDesignSuccess (result) {
      this.closePolling()
      this.designResult = result
      this.designLoading = false
      this.showProgressModal = false
      this.currentTaskId = null
      this.currentStep = 4
      this.resetReportAssets()
      this.$message.success('轨迹设计完成')
    },
    resetSteps () {
      this.closePolling()
      this.destroyResultCharts()
      this.currentStep = 0
      this.designResult = null
      this.showProgressModal = false
      this.currentTaskId = null
      this.resetReportAssets()
      this.progressInfo = {
        iteration: 0,
        totalIterations: 0,
        currentBest: undefined,
        progressPercent: 0,
        message: ''
      }
    },
    openPendingSaveModal () {
      if (!this.designResult || !this.designResult.best_solution_dict) {
        this.$message.warning('请先完成轨迹设计')
        return
      }
      const t = new Date()
      const pad = (n) => (n < 10 ? '0' + n : '' + n)
      const stamp = `${t.getFullYear()}${pad(t.getMonth() + 1)}${pad(t.getDate())}_${pad(t.getHours())}${pad(t.getMinutes())}`
      this.pendingSaveName = `待钻井-${stamp}`
      this.showPendingSaveModal = true
    },
    closePendingSaveModal () {
      this.showPendingSaveModal = false
      this.pendingSaveSubmitting = false
    },
    async confirmSavePending () {
      if (!this.pendingSaveName || !String(this.pendingSaveName).trim()) {
        this.$message.warning('请填写待钻井名称')
        return
      }
      if (!this.designResult || !this.designResult.best_solution_dict) {
        this.$message.warning('无设计结果可保存')
        return
      }
      if (this.form.siteId == null || this.form.siteId === '') {
        this.$message.warning('待钻井须归属井场，请返回第一步选择井场后再保存')
        return
      }
      const seven = {}
      for (const k of Object.keys(this.designResult.best_solution_dict)) {
        const v = this.designResult.best_solution_dict[k]
        const n = Number(v)
        seven[k] = Number.isFinite(n) ? n : v
      }
      const rawPts = this.designResult.trajectory_points || []
      const trajectoryPoints = rawPts
        .map((p) => ({
          x: p && p.x != null ? Number(p.x) : NaN,
          y: p && p.y != null ? Number(p.y) : NaN,
          z: p && p.z != null ? Number(p.z) : NaN
        }))
        .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z))
      const dto = {
        siteId: this.form.siteId != null && this.form.siteId !== '' ? Number(this.form.siteId) : null,
        name: String(this.pendingSaveName).trim(),
        wellheadE: this.form.wellhead && this.form.wellhead.e != null ? Number(this.form.wellhead.e) : null,
        wellheadN: this.form.wellhead && this.form.wellhead.n != null ? Number(this.form.wellhead.n) : null,
        wellheadD: this.form.wellhead && this.form.wellhead.d != null ? Number(this.form.wellhead.d) : null,
        targetE: this.form.target && this.form.target.e != null ? Number(this.form.target.e) : null,
        targetN: this.form.target && this.form.target.n != null ? Number(this.form.target.n) : null,
        targetD: this.form.target && this.form.target.d != null ? Number(this.form.target.d) : null,
        sevenSegmentParams: seven,
        trajectoryPoints,
        finalDeviation: this.designResult.final_deviation != null ? Number(this.designResult.final_deviation) : null,
        optimizationTime: this.designResult.optimization_time != null ? Number(this.designResult.optimization_time) : null
      }
      this.pendingSaveSubmitting = true
      try {
        await drillingAPI.savePendingDrillWell(dto)
        this.$message.success('已保存为待钻井（井斜数据表已自动生成并入库）')
        this.closePendingSaveModal()
      } catch (err) {
        this.$message.error('保存失败：' + (err.message || '未知错误'))
        this.pendingSaveSubmitting = false
      }
    },
    async exportReport () {
      if (!this.designResult) {
        this.$message.warning('暂无可导出的设计结果')
        return
      }

      this.reportExporting = true
      const hideLoading = this.$message.loading('正在生成 PDF 报告...', 0)

      try {
        await this.prepareReportAssets()
        const pages = await this.captureReportPages()
        const pdfBlob = createImagePdfFromPages(pages)
        this.downloadBlob(pdfBlob, this.buildReportFileName())
        this.$message.success('PDF 报告已导出')
      } catch (err) {
        this.$message.error('导出报告失败：' + (err.message || '未知错误'))
      } finally {
        if (typeof hideLoading === 'function') {
          hideLoading()
        }
        this.reportExporting = false
      }
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
.result-step {
  max-width: 1100px;
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
.result-metrics {
  margin-top: 16px;
}
.result-actions .ant-btn + .ant-btn {
  margin-left: 10px;
}
.result-actions {
  margin-top: 16px;
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 24px;
}
.trajectory-chart {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
}
.trajectory-chart-wide {
  grid-column: 1 / -1;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
  }
}
.chart-header-meta {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}
.legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
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
  height: 420px;
}
.chart-container-2d {
  height: 340px;
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

.report-export-root {
  position: fixed;
  left: -20000px;
  top: 0;
  width: 794px;
  pointer-events: none;
  z-index: -1;
}
.report-render-stage {
  position: absolute;
  top: 0;
  left: 0;
  width: 794px;
  opacity: 0;
  pointer-events: none;
}
.report-render-chart {
  width: 706px;
  height: 340px;
  margin-left: 44px;
  margin-bottom: 12px;
  background: #ffffff;
}
.report-page {
  width: 794px;
  height: 1123px;
  padding: 40px 44px 34px;
  box-sizing: border-box;
  background: #ffffff;
  color: #1f1f1f;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  display: flex;
  flex-direction: column;
}
.report-page + .report-page {
  margin-top: 24px;
}
.report-page-header {
  border-bottom: 2px solid #0f52ba;
  padding-bottom: 14px;
  margin-bottom: 20px;
}
.report-title {
  font-size: 28px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 1px;
}
.report-subtitle {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: #5b6675;
}
.report-section {
  margin-bottom: 16px;
}
.report-section-flex {
  flex: 1;
}
.report-section-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #0f52ba;
}
.report-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.report-parameter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.report-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.report-data-card {
  min-height: 68px;
  padding: 10px 12px;
  border: 1px solid #dce6f5;
  border-radius: 8px;
  background: #f8fbff;
  box-sizing: border-box;
}
.report-data-label {
  font-size: 12px;
  color: #4f5b6b;
}
.report-data-value {
  margin-top: 8px;
  font-size: 15px;
  line-height: 1.45;
  font-weight: 600;
  word-break: break-word;
}
.report-chart-card {
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  background: #ffffff;
}
.report-chart-title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #1f1f1f;
}
.report-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.report-chart-image {
  width: 100%;
  height: 242px;
  display: block;
  object-fit: contain;
  border: 1px solid #f0f0f0;
  background: #fff;
}
.report-chart-image-large {
  height: 338px;
}
.report-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 11px;
}
.report-table th,
.report-table td {
  border: 1px solid #d9d9d9;
  padding: 7px 6px;
  text-align: center;
}
.report-table th {
  background: #f4f8fe;
  font-weight: 600;
}
.report-empty {
  padding: 18px 0;
  color: #8c8c8c;
}
.report-table-note {
  margin-top: 10px;
  font-size: 11px;
  line-height: 1.6;
  color: #666;
}
.report-footer {
  margin-top: auto;
  padding-top: 16px;
  font-size: 11px;
  color: #7a7a7a;
  text-align: right;
}

@media (max-width: 960px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
  .trajectory-chart-wide {
    grid-column: auto;
  }
}
</style>
