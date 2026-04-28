/**
 * 钻井 / 基础数据 相关接口（井场、井、井轨迹 Excel）
 */

import request from '@/utils/request'

const api = {
  getWellsBySite: '/drilling/site/wells',
  getWellTrajectoryExcel: '/drilling/well/trajectory-excel',
  designTrajectory: '/trajectory/design',
  startDesign: '/trajectory/design/start',
  getDesignProgress: '/trajectory/design/progress/',
  getDesignStatus: '/trajectory/design/status/'
}

export default api

export function getWellsBySite (siteId) {
  return Promise.reject(new Error('USE_LOCAL'))
  // return request({ url: api.getWellsBySite, method: 'get', params: { siteId } })
}

export function getWellTrajectoryExcel (siteId, wellId) {
  return Promise.reject(new Error('USE_PUBLIC'))
  // return request({
  //   url: api.getWellTrajectoryExcel,
  //   method: 'get',
  //   params: { siteId, wellId },
  //   responseType: 'arraybuffer'
  // }).then(res => res.data)
}

export function designTrajectory (params) {
  return request({ url: api.designTrajectory, method: 'post', data: params })
}

export function startDesign (params) {
  return request({ url: api.startDesign, method: 'post', data: params })
}

export function createProgressEventSource (taskId) {
  return new EventSource(`${api.getDesignProgress}${taskId}`)
}

export function getDesignStatus (taskId) {
  return request({ url: `${api.getDesignStatus}${taskId}`, method: 'get' })
}
