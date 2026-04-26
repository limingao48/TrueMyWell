export default class User {
  constructor({
    id = '',
    username = '',
    password = '',
    name = '',
    avatar = '',
    email = '',
    phone = '',
    roleId = '',
    orgId = '',
    status = 1,
    createTime = new Date(),
    updateTime = new Date()
  } = {}) {
    this.id = id
    this.username = username
    this.password = password
    this.name = name
    this.avatar = avatar
    this.email = email
    this.phone = phone
    this.roleId = roleId
    this.orgId = orgId
    this.status = status
    this.createTime = createTime
    this.updateTime = updateTime
  }
}
