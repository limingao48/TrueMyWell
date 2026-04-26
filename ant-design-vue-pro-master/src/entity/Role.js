export default class Role {
  constructor({
    id = '',
    name = '',
    code = '',
    description = '',
    status = 1,
    createTime = new Date(),
    updateTime = new Date()
  } = {}) {
    this.id = id
    this.name = name
    this.code = code
    this.description = description
    this.status = status
    this.createTime = createTime
    this.updateTime = updateTime
  }
}
