export default class Site {
  constructor({
    id = '',
    name = '',
    code = '',
    createTime = new Date(),
    updateTime = new Date()
  } = {}) {
    this.id = id
    this.name = name
    this.code = code
    this.createTime = createTime
    this.updateTime = updateTime
  }
}
