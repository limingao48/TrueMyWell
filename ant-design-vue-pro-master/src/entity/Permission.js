export default class Permission {
  constructor({
    id = '',
    name = '',
    code = '',
    description = '',
    parentId = '',
    level = 1,
    sort = 0,
    createTime = new Date(),
    updateTime = new Date()
  } = {}) {
    this.id = id
    this.name = name
    this.code = code
    this.description = description
    this.parentId = parentId
    this.level = level
    this.sort = sort
    this.createTime = createTime
    this.updateTime = updateTime
  }
}
