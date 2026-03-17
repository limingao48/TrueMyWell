<!--<template>-->
<!--  <div id='test_app'>-->
<!--    &lt;!&ndash;echarts的容器&ndash;&gt;-->
<!--    <div id='main' style='width: 100%;height: 520px;background:#fff'></div>-->
<!--  </div>-->
<!--</template>-->

<!--<script>-->
<!--import * as echarts from 'echarts'-->
<!--export default {-->
<!--  name: 'Line',-->
<!--  // data () {-->
<!--  //   return {-->
<!--  //     charts: '',-->
<!--  //     opinionData: ['155', '400', '900', '800', '300', '900', '270', '333', '379', '1748', '321', '549', '221', '498']-->
<!--  //   }-->
<!--  // },-->
<!--  methods: {-->
<!--    drawLine (id) {-->
<!--      console.log(document.getElementById(id))-->
<!--      this.charts = echarts.init(document.getElementById(id))-->
<!--      this.charts.setOption({-->
<!--        title: {-->
<!--          left: '3%',-->
<!--          top: '5%',-->
<!--          text: '预测详情'-->
<!--        },-->
<!--        tooltip: {-->
<!--          trigger: 'axis'-->
<!--        },-->
<!--        legend: {-->
<!--          align: 'right',-->
<!--          left: '3%',-->
<!--          top: '15%',-->
<!--          data: ['深度']-->
<!--        },-->
<!--        grid: {-->
<!--          top: '30%',-->
<!--          left: '5%',-->
<!--          right: '5%',-->
<!--          bottom: '5%',-->
<!--          containLabel: true-->
<!--        },-->

<!--        toolbox: {-->
<!--          feature: {-->
<!--            saveAsImage: {}-->
<!--          }-->
<!--        },-->
<!--        xAxis: {-->
<!--          type: 'category',-->
<!--          boundaryGap: true,-->
<!--          axisTick: {-->
<!--            alignWithLabel: true-->
<!--          },-->
<!--          data: ['200', '201', '202', '203', '204', '205', '206', '207', '208', '209', '210', '211', '212', '213']-->

<!--        },-->
<!--        yAxis: {-->
<!--          type: 'value',-->
<!--          boundaryGap: true,-->
<!--          splitNumber: 4,-->
<!--          interval: 250-->
<!--        },-->

<!--        series: [{-->
<!--          name: 'MLP',-->
<!--          type: 'line',-->
<!--          stack: '总量',-->
<!--          areaStyle: {-->
<!--            color: {-->
<!--              type: 'linear',-->
<!--              x: 0,-->
<!--              y: 0,-->
<!--              x2: 0,-->
<!--              y2: 1,-->
<!--              colorStops: [{-->
<!--                offset: 0, color: 'rgb(255,200,213)'-->
<!--              }, {-->
<!--                offset: 1, color: '#ffffff'-->
<!--              }],-->
<!--              global: false-->
<!--            }-->
<!--          },-->
<!--          itemStyle: {-->
<!--            color: 'rgb(255,96,64)',-->
<!--            lineStyle: {-->
<!--              color: 'rgb(255,96,64)'-->
<!--            }-->

<!--          },-->
<!--          data: ['155', '400', '900', '800', '300', '900', '270', '333', '379', '1748', '321', '549', '221', '498']-->
<!--        },-->
<!--          {-->
<!--            name: 'SVR',-->
<!--            type: 'line',-->
<!--            stack: '总量',-->
<!--            areaStyle: {-->
<!--              color: {-->
<!--                type: 'linear',-->
<!--                x: 0,-->
<!--                y: 0,-->
<!--                x2: 0,-->
<!--                y2: 1,-->
<!--                colorStops: [{-->
<!--                  offset: 0, color: 'rgb(255,200,213)'-->
<!--                }, {-->
<!--                  offset: 1, color: '#ffffff'-->
<!--                }],-->
<!--                global: false-->
<!--              }-->
<!--            },-->
<!--            itemStyle: {-->
<!--              color: 'rgb(0,0,255)',-->
<!--              lineStyle: {-->
<!--                color: 'rgb(0,0,255)'-->
<!--              }-->

<!--            },-->
<!--            data: ['333', '863', '764', '911', '344', '566', '131', '333', '454', '551', '1112', '368', '299', '498']-->
<!--          }-->
<!--        ]-->
<!--      })-->
<!--    }-->
<!--  },-->
<!--  mounted () {-->
<!--    this.$nextTick(function () {-->
<!--      this.drawLine('main')-->
<!--    })-->
<!--  }-->
<!--}-->
<!--</script>-->

<!--<style scoped>-->
<!--* {-->
<!--  margin: 0;-->
<!--  padding: 0;-->
<!--  list-style: none;-->
<!--}-->
<!--</style>-->
