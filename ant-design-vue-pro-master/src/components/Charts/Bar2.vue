<template>
  <div :style="{ padding: '0 0 32px 32px' }">
    <h4 :style="{ marginBottom: '20px' }">{{ title }}</h4>
    <v-chart
      height="254"
      :data="data"
      :forceFit="true"
      :padding="['auto', 'auto', '40', '50']">
      <v-tooltip />
      <v-axis dataKey="x" :label="{ formatter: (text) => text + ' 号' }"/>
      <v-axis dataKey="y" :label="{ formatter: (text) => text + ' 个' }" />
      <v-bar position="x*y"/>
    </v-chart>
  </div>
</template>

<script>
export default {
  name: 'Bar2',
  props: {
    title: {
      type: String,
      default: ''
    },
    data: {
      type: Array,
      default: () => {
        return []
      }
    },
    // xAxis: { // 添加横坐标设置
    //   type: Object,
    //   default: () => {
    //     return {
    //       dataKey: 'x', // 横坐标数据对应的属性
    //       title: '条数' // 横坐标标题
    //     }
    //   }
    // },
    // yAxis: { // 添加纵坐标设置
    //   type: Array,
    //   default: () => {
    //     return [{
    //       dataKey: 'y', // 纵坐标数据对应的属性
    //       title: 'Y轴标题', // 纵坐标标题
    //       min: 1, // 纵坐标最小值
    //       max: 22 // 纵坐标最大值
    //     }]
    //   }
    // },
    // xField: 'type',
    // yField: 'values',
    scale: {
      type: Array,
      default: () => {
        return [{
          dataKey: 'x',
          title: '条数', // 横坐标标题
          min: 2
        }, {
          dataKey: 'y',
          title: '时间',
          min: 1,
          max: 22
        }]
        // return []
      }
    },
    tooltip: {
      type: Array,
      default: () => {
        return [
          'x*y',
          (x, y) => ({
            name: x,
            value: y
          })
        ]
      }
    }
  },
  data () {
    return {
    }
  }
}
</script>
