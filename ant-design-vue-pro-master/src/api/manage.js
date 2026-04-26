import request from '@/utils/request'

const api = {
  user: '/user',
  role: '/role',
  task: '/task/page',
  getAllTask: '/task/getAllTask',
  permission: '/permission',
  permissionNoPager: '/permission/no-pager',
  orgTree: '/org/tree',
  getAllPredicts: '/predict/getAllPredict',
  getAllPredictByWell: '/predict/getPredictByWell',
  getAll: '/predict/getAll',
  getOffset: '/predict/getOffset',
  getWellById: '/well/getById',
  getModelsByTask: '/predict/getModelsByTask',
  getHistory: '/predict/getHistory',
  getAllWells: '/well/getAll',
  getTime: '/predict/getTimeByTask',
  predictPage: '/predict/page'
}

export default api

export function getUserList (parameter) {
  return request({
    url: api.user,
    method: 'get',
    params: parameter
  })
}

export function getRoleList (parameter) {
  return request({
    url: api.role,
    method: 'get',
    params: parameter
  })
}

export function getAllTasks (parameter) {
  return request({
    url: api.getAllTask,
    method: 'get',
    params: parameter
  })
}

export function getWellById (parameter) {
  return request({
    url: api.getWellById,
    method: 'get',
    params: parameter
  })
}

export function getServiceList (parameter) {
  return request({
    url: api.task,
    method: 'get',
    params: parameter
  })
}

export function getModelsByTask (parameter) {
  return request({
    url: api.getModelsByTask,
    method: 'get',
    params: {
      taskId: parameter.taskId
    }
  })
}

export function getPermissions (parameter) {
  return request({
    url: api.permissionNoPager,
    method: 'get',
    params: parameter
  })
}

export function getOrgTree (parameter) {
  return request({
    url: api.orgTree,
    method: 'get',
    params: parameter
  })
}

// id == 0 add     post
// id != 0 update  put
export function saveService (parameter) {
  return request({
    url: api.service,
    method: parameter.id === 0 ? 'post' : 'put',
    data: parameter
  })
}

export function saveSub (sub) {
  return request({
    url: '/sub',
    method: sub.id === 0 ? 'post' : 'put',
    data: sub
  })
}

export function getPredicts (parameter) {
  return request({
    url: api.getAllPredicts,
    method: 'get',
    params: parameter
  })
}

export function getAll (parameter) {
  return request({
    url: api.predictPage,
    method: 'get',
    params: parameter
  })
}

export function getOffset (parameter) {
  return request({
    url: api.getOffset,
    method: 'get',
    params: parameter
  })
}

export function getHistory (parameter) {
  return request({
    url: api.getHistory,
    method: 'get',
    params: parameter
  })
}

export function getAllWells () {
  return request({
    url: api.getAllWells,
    method: 'get'
  })
}

export function getAllPredictByWells (wellID) {
  return request({
    url: api.getAllPredictByWell,
    method: 'get',
    params: {
      wellId: wellID
    }
  })
}

export function getTime (parameter) {
  return request({
    url: api.getTime,
    method: 'get',
    params: parameter
  })
}

export function getPredictList (parameter) {
  return request({
    url: api.predictPage,
    method: 'get',
    params: parameter
  })
}
