/**
 * 钻井 / 基础数据 相关接口（井场、井、井轨迹 Excel）
 * 当前为占位实现：不真实发请求，前端仍从 public 按井号加载 xlsx（如 41-37YH3.xlsx）
 * 对接后端时取消注释并：import request from '@/utils/request'
 */

const api = {
  // 井场下井列表（后端返回当前井场下的井及井口等）
  getWellsBySite: '/drilling/site/wells',
  // 单口井轨迹 Excel 文件流（后端返回该井的轨迹 Excel）
  getWellTrajectoryExcel: '/drilling/well/trajectory-excel',
  // 轨迹设计（后端执行优化算法返回七段式设计参数）
  designTrajectory: '/drilling/trajectory/design'
}

export default api

/**
 * 获取井场下的井列表（对应后端：当前井场下的井）
 * @param {string} siteId 井场 ID
 * @returns {Promise<Array>} 井列表 [{ id, wellNo, name, wellheadE, wellheadN, wellheadD, ... }]
 */
export function getWellsBySite (siteId) {
  // 暂不真实请求，由前端使用本地 wellList 等数据
  return Promise.reject(new Error('USE_LOCAL'))
  // 对接后端时改为：
  // return request({ url: api.getWellsBySite, method: 'get', params: { siteId } })
}

/**
 * 获取单口井的轨迹 Excel 文件（对应后端：返回该井的 Excel 流）
 * @param {string} siteId 井场 ID
 * @param {string} wellId 井 ID（或 wellNo，视后端约定）
 * @returns {Promise<ArrayBuffer>} Excel 文件的 ArrayBuffer
 */
export function getWellTrajectoryExcel (siteId, wellId) {
  // 暂不真实请求，调用方会回退到从 public 按井号加载（如 /41-37YH3.xlsx）
  return Promise.reject(new Error('USE_PUBLIC'))
  // 对接后端时改为（需后端返回 blob/arraybuffer）：
  // return request({
  //   url: api.getWellTrajectoryExcel,
  //   method: 'get',
  //   params: { siteId, wellId },
  //   responseType: 'arraybuffer'
  // }).then(res => res.data)
}

/**
 * 轨迹设计（对应后端：执行优化算法返回七段式设计参数）
 * @param {Object} params 轨迹设计参数
 * @param {string} params.siteId 井场 ID
 * @param {Object} params.target 靶点坐标 { e, n, d }
 * @param {Object} params.landingRequirement 入靶需求
 * @param {Object} params.wellhead 井口坐标 { e, n, d }
 * @param {Array} params.neighborWellIds 邻井 ID 列表
 * @param {Object} params.algorithm 算法参数
 * @returns {Promise<Object>} 设计结果
 */
export function designTrajectory (params) {
  // 暂不真实请求，返回模拟数据
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        data: {
          best_solution_dict: {
            L0: 800,
            DLS1: 3.2,
            alpha3: 45,
            L3: 1200,
            DLS_turn: 2.5,
            L4: 300,
            phi_target: 0.2,
            L5: 600,
            DLS6: 2.8,
            alpha_e: 88.5,
            L7: 800,
            phi_init: 45
          },
          final_deviation: 0.12,
          optimization_time: 8.5
        }
      })
    }, 1500)
  })
  // 对接后端时改为：
  // return request({ url: api.designTrajectory, method: 'post', data: params })
}
