import request from '@/utils/request'

// API路径定义
const API = {
  // 认证相关
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    forgePassword: '/auth/forge-password',
    register: '/auth/register',
    twoStepCode: '/auth/2step-code',
    sendSms: '/account/sms',
    sendSmsErr: '/account/sms_err'
  },
  // 用户相关
  user: {
    info: '/user/info',
    menu: '/user/nav'
  },
  // 管理相关
  manage: {
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
  },
  // 钻井相关
  drilling: {
    // 井场相关
    getSiteList: '/drilling/site/list',
    createSite: '/drilling/site/create',
    updateSite: '/drilling/site/update',
    deleteSite: '/drilling/site/delete',
    getSiteById: '/drilling/site/get',
    // 井相关
    getWellsBySite: '/drilling/site/wells',
    createWell: '/drilling/well/create',
    updateWell: '/drilling/well/update',
    deleteWell: '/drilling/well/delete',
    getWellById: '/drilling/well/get',
    getWellTrajectoryExcel: '/drilling/well/trajectory-excel'
  }
}

// 认证相关API
export const authAPI = {
  /**
   * 用户登录
   * @param {Object} params - 登录参数
   * @param {string} params.username - 用户名
   * @param {string} params.password - 密码
   * @param {boolean} params.remember_me - 是否记住登录状态
   * @param {string} params.captcha - 验证码
   * @returns {Promise}
   */
  login (params) {
    return request({
      url: API.auth.login,
      method: 'post',
      data: params
    })
  },

  /**
   * 发送短信验证码
   * @param {Object} params - 发送参数
   * @returns {Promise}
   */
  getSmsCaptcha (params) {
    return request({
      url: API.auth.sendSms,
      method: 'post',
      data: params
    })
  },

  /**
   * 退出登录
   * @returns {Promise}
   */
  logout () {
    return request({
      url: API.auth.logout,
      method: 'post',
      headers: {
        'Content-Type': 'application/json;charset=UTF-8'
      }
    })
  },

  /**
   * 获取两步验证状态
   * @param {Object} params - 参数
   * @returns {Promise}
   */
  get2step (params) {
    return request({
      url: API.auth.twoStepCode,
      method: 'post',
      data: params
    })
  }
}

// 用户相关API
export const userAPI = {
  /**
   * 获取用户信息
   * @returns {Promise}
   */
  getInfo () {
    return request({
      url: API.user.info,
      method: 'get',
      headers: {
        'Content-Type': 'application/json;charset=UTF-8'
      }
    })
  },

  /**
   * 获取当前用户导航菜单
   * @returns {Promise}
   */
  getCurrentUserNav () {
    return request({
      url: API.user.menu,
      method: 'get'
    })
  }
}

// 管理相关API
export const manageAPI = {
  /**
   * 获取用户列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getUserList (params) {
    return request({
      url: API.manage.user,
      method: 'get',
      params
    })
  },

  /**
   * 获取角色列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getRoleList (params) {
    return request({
      url: API.manage.role,
      method: 'get',
      params
    })
  },

  /**
   * 获取所有任务
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getAllTasks (params) {
    return request({
      url: API.manage.getAllTask,
      method: 'get',
      params
    })
  },

  /**
   * 根据ID获取井信息
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getWellById (params) {
    return request({
      url: API.manage.getWellById,
      method: 'get',
      params
    })
  },

  /**
   * 获取服务列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getServiceList (params) {
    return request({
      url: API.manage.task,
      method: 'get',
      params
    })
  },

  /**
   * 根据任务获取模型
   * @param {Object} params - 查询参数
   * @param {string} params.taskId - 任务ID
   * @returns {Promise}
   */
  getModelsByTask (params) {
    return request({
      url: API.manage.getModelsByTask,
      method: 'get',
      params: {
        taskId: params.taskId
      }
    })
  },

  /**
   * 获取权限列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getPermissions (params) {
    return request({
      url: API.manage.permissionNoPager,
      method: 'get',
      params
    })
  },

  /**
   * 获取组织树
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getOrgTree (params) {
    return request({
      url: API.manage.orgTree,
      method: 'get',
      params
    })
  },

  /**
   * 保存服务
   * @param {Object} params - 服务参数
   * @returns {Promise}
   */
  saveService (params) {
    return request({
      url: '/sub',
      method: params.id === 0 ? 'post' : 'put',
      data: params
    })
  },

  /**
   * 保存子服务
   * @param {Object} sub - 子服务参数
   * @returns {Promise}
   */
  saveSub (sub) {
    return request({
      url: '/sub',
      method: sub.id === 0 ? 'post' : 'put',
      data: sub
    })
  },

  /**
   * 获取预测列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getPredicts (params) {
    return request({
      url: API.manage.getAllPredicts,
      method: 'get',
      params
    })
  },

  /**
   * 获取所有数据
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getAll (params) {
    return request({
      url: API.manage.predictPage,
      method: 'get',
      params
    })
  },

  /**
   * 获取偏移量
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getOffset (params) {
    return request({
      url: API.manage.getOffset,
      method: 'get',
      params
    })
  },

  /**
   * 获取历史数据
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getHistory (params) {
    return request({
      url: API.manage.getHistory,
      method: 'get',
      params
    })
  },

  /**
   * 获取所有井
   * @returns {Promise}
   */
  getAllWells () {
    return request({
      url: API.manage.getAllWells,
      method: 'get'
    })
  },

  /**
   * 根据井获取预测
   * @param {string} wellID - 井ID
   * @returns {Promise}
   */
  getAllPredictByWells (wellID) {
    return request({
      url: API.manage.getAllPredictByWell,
      method: 'get',
      params: {
        wellId: wellID
      }
    })
  },

  /**
   * 获取时间
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getTime (params) {
    return request({
      url: API.manage.getTime,
      method: 'get',
      params
    })
  },

  /**
   * 获取预测列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getPredictList (params) {
    return request({
      url: API.manage.predictPage,
      method: 'get',
      params
    })
  }
}

// 钻井相关API
export const drillingAPI = {
  // 井场相关API
  /**
   * 获取井场列表
   * @returns {Promise<Array>} 井场列表
   */
  getSiteList () {
    return request({
      url: API.drilling.getSiteList,
      method: 'get'
    })
  },

  /**
   * 获取井场详情
   * @param {string} siteId - 井场ID
   * @returns {Promise<Object>} 井场详情
   */
  getSiteById (siteId) {
    return request({
      url: API.drilling.getSiteById,
      method: 'get',
      params: { siteId }
    })
  },

  /**
   * 创建井场
   * @param {Object} data - 井场数据
   * @param {string} data.name - 井场名称
   * @param {string} data.code - 井场编号
   * @returns {Promise<Object>} 创建结果
   */
  createSite (data) {
    return request({
      url: API.drilling.createSite,
      method: 'post',
      data
    })
  },

  /**
   * 更新井场
   * @param {Object} data - 井场数据
   * @param {string} data.id - 井场ID（编辑时必填，由后端自动生成）
   * @param {string} data.name - 井场名称
   * @param {string} data.code - 井场编号
   * @returns {Promise<Object>} 更新结果
   */
  updateSite (data) {
    return request({
      url: API.drilling.updateSite,
      method: 'put',
      data
    })
  },

  /**
   * 删除井场
   * @param {string} siteId - 井场ID
   * @returns {Promise<Object>} 删除结果
   */
  deleteSite (siteId) {
    return request({
      url: API.drilling.deleteSite,
      method: 'delete',
      params: { siteId }
    })
  },

  // 井相关API
  /**
   * 获取井场下的井列表
   * @param {string} siteId - 井场ID
   * @returns {Promise<Array>} 井列表
   */
  getWellsBySite (siteId) {
    return request({
      url: API.drilling.getWellsBySite,
      method: 'get',
      params: { siteId }
    })
  },

  /**
   * 获取井详情
   * @param {string} wellId - 井ID
   * @returns {Promise<Object>} 井详情
   */
  getWellById (wellId) {
    return request({
      url: API.drilling.getWellById,
      method: 'get',
      params: { wellId }
    })
  },

  /**
   * 创建井
   * @param {Object} data - 井数据
   * @param {string} data.siteId - 井场ID
   * @param {string} data.wellNo - 井号
   * @param {string} data.name - 井名
   * @param {number} data.wellheadE - 井口东坐标
   * @param {number} data.wellheadN - 井口北坐标
   * @param {number} data.wellheadD - 井口海拔
   * @param {number} data.wellDiameter - 井径
   * @returns {Promise<Object>} 创建结果
   */
  createWell (data) {
    return request({
      url: API.drilling.createWell,
      method: 'post',
      data
    })
  },

  /**
   * 更新井
   * @param {Object} data - 井数据
   * @param {string} data.id - 井ID（编辑时必填，由后端自动生成）
   * @param {string} data.wellNo - 井号
   * @param {string} data.name - 井名
   * @param {number} data.wellheadE - 井口东坐标
   * @param {number} data.wellheadN - 井口北坐标
   * @param {number} data.wellheadD - 井口海拔
   * @param {number} data.wellDiameter - 井径
   * @returns {Promise<Object>} 更新结果
   */
  updateWell (data) {
    return request({
      url: API.drilling.updateWell,
      method: 'put',
      data
    })
  },

  /**
   * 删除井
   * @param {string} wellId - 井ID
   * @returns {Promise<Object>} 删除结果
   */
  deleteWell (wellId) {
    return request({
      url: API.drilling.deleteWell,
      method: 'delete',
      params: { wellId }
    })
  },

  /**
   * 获取单口井的轨迹 Excel 文件
   * @param {string} siteId - 井场ID
   * @param {string} wellId - 井ID
   * @returns {Promise<ArrayBuffer>} Excel 文件的 ArrayBuffer
   */
  getWellTrajectoryExcel (siteId, wellId) {
    // 暂不真实请求，调用方会回退到从 public 按井号加载
    return Promise.reject(new Error('USE_PUBLIC'))
    // 对接后端时改为：
    // return request({
    //   url: API.drilling.getWellTrajectoryExcel,
    //   method: 'get',
    //   params: { siteId, wellId },
    //   responseType: 'arraybuffer'
    // }).then(res => res.data)
  }
}

// 导出默认对象
export default {
  auth: authAPI,
  user: userAPI,
  manage: manageAPI,
  drilling: drillingAPI
}
