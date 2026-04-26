/**
 * 钻井 / 基础数据 相关接口（井场、井、井轨迹 Excel）
 * 当前为占位实现：不真实发请求，前端仍从 public 按井号加载 xlsx（如 41-37YH3.xlsx）
 * 对接后端时取消注释并：import request from '@/utils/request'
 */

const api = {
  // 井场下井列表（后端返回当前井场下的井及井口等）
  getWellsBySite: '/drilling/site/wells',
  // 单口井轨迹 Excel 文件流（后端返回该井的轨迹 Excel）
  getWellTrajectoryExcel: '/drilling/well/trajectory-excel'
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
