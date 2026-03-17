<template>
  <page-header-wrapper>
    <template v-slot:content>
      录井数据上传、关联井、查询与简单曲线展示（深度-参数）。
    </template>
    <a-card :bordered="false">
      <a-form layout="inline" style="margin-bottom: 16px">
        <a-form-item label="井号">
          <a-select v-model="query.wellId" placeholder="请选择井" allow-clear style="width: 160px">
            <a-select-option v-for="w in wellOptions" :key="w.id" :value="w.id">{{ w.wellNo }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="时间范围">
          <a-range-picker v-model="query.dateRange" format="YYYY-MM-DD" style="width: 220px" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="search">查询</a-button>
          <a-button style="margin-left: 8px" @click="resetQuery">重置</a-button>
        </a-form-item>
      </a-form>

      <a-upload
        name="file"
        :before-upload="beforeUpload"
        accept=".csv,.xlsx,.xls"
        style="margin-bottom: 16px"
      >
        <a-button icon="upload">上传录井文件 (CSV/Excel)</a-button>
        <span style="margin-left: 8px; color: #999">关联井号、井深/时间后存储</span>
      </a-upload>

      <a-table
        :columns="columns"
        :data-source="dataSource"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        row-key="id"
        style="margin-bottom: 24px"
      />

      <a-divider>深度-参数曲线（示例）</a-divider>
      <div ref="chartRef" class="chart-container" />
    </a-card>
  </page-header-wrapper>
</template>

<script>
import * as echarts from 'echarts'

const MOCK_WELLS = [
  { id: '1', wellNo: '41-37YH3' },
  { id: '2', wellNo: '41-37YH5' },
  { id: '3', wellNo: '41-38YH1' }
]
const MOCK_LOGGING = [
  { id: '1', wellId: '1', wellNo: '41-37YH3', depth: 500, inclination: 2.1, azimuth: 45, time: '2024-01-10 08:00' },
  { id: '2', wellId: '1', wellNo: '41-37YH3', depth: 1000, inclination: 15.2, azimuth: 46, time: '2024-01-10 10:00' },
  { id: '3', wellId: '1', wellNo: '41-37YH3', depth: 1500, inclination: 32.5, azimuth: 47, time: '2024-01-10 12:00' },
  { id: '4', wellId: '1', wellNo: '41-37YH3', depth: 2000, inclination: 55.0, azimuth: 45, time: '2024-01-10 14:00' },
  { id: '5', wellId: '1', wellNo: '41-37YH3', depth: 2500, inclination: 78.2, azimuth: 44, time: '2024-01-10 16:00' },
  { id: '6', wellId: '2', wellNo: '41-37YH5', depth: 800, inclination: 5.0, azimuth: 50, time: '2024-01-11 09:00' },
  { id: '7', wellId: '2', wellNo: '41-37YH5', depth: 1600, inclination: 28.0, azimuth: 51, time: '2024-01-11 11:00' }
]

export default {
  name: 'MudLogging',
  data () {
    return {
      query: { wellId: undefined, dateRange: null },
      wellOptions: MOCK_WELLS,
      dataSource: [...MOCK_LOGGING],
      columns: [
        { title: '井号', dataIndex: 'wellNo', key: 'wellNo' },
        { title: '井深(m)', dataIndex: 'depth', key: 'depth' },
        { title: '井斜(°)', dataIndex: 'inclination', key: 'inclination' },
        { title: '方位(°)', dataIndex: 'azimuth', key: 'azimuth' },
        { title: '时间', dataIndex: 'time', key: 'time' }
      ],
      chart: null
    }
  },
  mounted () {
    this.$nextTick(() => this.initChart())
  },
  beforeDestroy () {
    if (this.chart) this.chart.dispose()
  },
  methods: {
    search () {
      if (!this.query.wellId) {
        this.dataSource = [...MOCK_LOGGING]
      } else {
        this.dataSource = MOCK_LOGGING.filter(l => l.wellId === this.query.wellId)
      }
      this.initChart()
    },
    resetQuery () {
      this.query = { wellId: undefined, dateRange: null }
      this.dataSource = [...MOCK_LOGGING]
      this.initChart()
    },
    beforeUpload (file) {
      this.$message.success('上传成功（模拟），已关联当前选中井')
      return false
    },
    initChart () {
      if (!this.$refs.chartRef) return
      if (this.chart) this.chart.dispose()
      this.chart = echarts.init(this.$refs.chartRef)
      const depths = this.dataSource.map(d => d.depth).sort((a, b) => a - b)
      const inclinations = this.dataSource.map(d => d.inclination)
      const azimuths = this.dataSource.map(d => d.azimuth)
      this.chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['井斜', '方位'], bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
        xAxis: { type: 'category', name: '深度 (m)', data: depths },
        yAxis: { type: 'value', name: '角度 (°)' },
        series: [
          { name: '井斜', type: 'line', data: inclinations, smooth: true },
          { name: '方位', type: 'line', data: azimuths, smooth: true }
        ]
      })
    }
  }
}
</script>

<style lang="less" scoped>
.chart-container {
  width: 100%;
  height: 320px;
}
</style>
