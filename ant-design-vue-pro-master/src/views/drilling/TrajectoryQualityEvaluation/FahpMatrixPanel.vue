<template>
  <div class="fahp-matrix-panel">
    <div v-if="criteria.length < 2" class="fahp-single-hint">
      仅 {{ criteria.length }} 项指标，权重固定为 1。
    </div>
    <template v-else>
      <div class="fahp-matrix-hint">
        第 <strong>i</strong> 行第 <strong>j</strong> 列表示指标 i 相对 j 的重要程度。
        上三角可编辑；下三角自动为倒数（如上方为 3，下方为 1/3），对角线为 1。
      </div>
      <div class="fahp-matrix-scroll">
        <table class="fahp-matrix-table">
          <thead>
            <tr>
              <th class="corner" />
              <th v-for="c in criteria" :key="'h-' + c.key" class="col-head">
                {{ c.short || c.title }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in criteria" :key="'r-' + row.key">
              <th class="row-head">{{ row.short || row.title }}</th>
              <td
                v-for="(col, ci) in criteria"
                :key="row.key + '-' + col.key"
                :class="cellClass(ri, ci)"
              >
                <template v-if="ri === ci">
                  <span class="diag">1</span>
                </template>
                <template v-else-if="ri < ci">
                  <a-select
                    :value="storedUpper(ri, ci)"
                    size="small"
                    class="fahp-select"
                    @change="v => setUpper(ri, ci, v)"
                  >
                    <a-select-option
                      v-for="opt in linguisticOptions"
                      :key="opt.value"
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </a-select-option>
                  </a-select>
                </template>
                <template v-else>
                  <span class="reciprocal" :title="lowerCellTitle(ri, ci)">
                    {{ lowerCellLabel(ri, ci) }}
                  </span>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="consistency" class="fahp-cr">
        一致性 CR = {{ consistency.cr }}
        <span :class="consistency.acceptable ? 'cr-ok' : 'cr-warn'">
          {{ consistency.acceptable ? '（通过，CR≤0.1）' : '（建议调整判断矩阵，CR>0.1）' }}
        </span>
        <span class="cr-detail">λmax={{ consistency.lambdaMax }}，CI={{ consistency.ci }}</span>
      </div>
    </template>
  </div>
</template>

<script>
import { FAHP_LINGUISTIC_OPTIONS } from '@/utils/trajectoryEvaluation/fahpConfig'
import {
  formatLowerCellLabel,
  getStoredUpperScale,
  setPairImportance
} from '@/utils/trajectoryEvaluation/fahp'

export default {
  name: 'FahpMatrixPanel',
  props: {
    criteria: {
      type: Array,
      required: true
    },
    value: {
      type: Object,
      default: () => ({})
    },
    consistency: {
      type: Object,
      default: null
    }
  },
  data () {
    return {
      linguisticOptions: FAHP_LINGUISTIC_OPTIONS
    }
  },
  computed: {
    criteriaKeys () {
      return this.criteria.map(c => c.key)
    }
  },
  methods: {
    cellClass (ri, ci) {
      if (ri === ci) return 'cell-diag'
      if (ri < ci) return 'cell-upper'
      return 'cell-lower'
    },
    storedUpper (ri, ci) {
      return getStoredUpperScale(this.value, this.criteriaKeys, ri, ci)
    },
    lowerCellLabel (ri, ci) {
      const stored = this.storedUpper(ri, ci)
      return formatLowerCellLabel(stored)
    },
    lowerCellTitle (ri, ci) {
      const stored = this.storedUpper(ri, ci)
      return `a(${ri + 1},${ci + 1}) = 1 / a(${ci + 1},${ri + 1}) = 1/${stored}`
    },
    setUpper (ri, ci, scale) {
      const rowKey = this.criteriaKeys[ri]
      const colKey = this.criteriaKeys[ci]
      const next = setPairImportance(this.value, this.criteriaKeys, rowKey, colKey, scale)
      this.$emit('input', next)
      this.$emit('change', next)
    }
  }
}
</script>

<style lang="less" scoped>
.fahp-matrix-panel {
  margin-bottom: 8px;
}
.fahp-single-hint,
.fahp-matrix-hint {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
  line-height: 1.5;
}
.fahp-matrix-scroll {
  overflow-x: auto;
}
.fahp-matrix-table {
  border-collapse: collapse;
  font-size: 12px;
  min-width: 100%;
  th, td {
    border: 1px solid #e8e8e8;
    padding: 4px 6px;
    text-align: center;
    vertical-align: middle;
  }
  .corner {
    background: #fafafa;
    min-width: 88px;
  }
  .row-head {
    background: #fafafa;
    font-weight: 500;
    text-align: left;
    white-space: nowrap;
    max-width: 120px;
  }
  .col-head {
    background: #fafafa;
    font-weight: 500;
    max-width: 100px;
    line-height: 1.3;
  }
  .cell-upper {
    background: #fff;
  }
  .cell-lower {
    background: #f5f5f5;
    color: #cf1322;
    font-weight: 600;
  }
  .cell-diag {
    background: #f0f5ff;
  }
  .diag, .reciprocal {
    font-weight: 600;
  }
}
.fahp-select {
  min-width: 140px;
  max-width: 180px;
}
.fahp-cr {
  margin-top: 8px;
  font-size: 12px;
  .cr-ok { color: #52c41a; margin-left: 4px; }
  .cr-warn { color: #fa8c16; margin-left: 4px; }
  .cr-detail {
    color: rgba(0, 0, 0, 0.45);
    margin-left: 8px;
  }
}
</style>
