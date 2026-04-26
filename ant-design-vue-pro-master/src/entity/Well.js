export default class Well {
  constructor({
    id = '',
    siteId = '',
    wellNo = '',
    name = '',
    wellheadE = 0,
    wellheadN = 0,
    wellheadD = 0,
    wellDiameter = 0,
    createTime = new Date(),
    updateTime = new Date()
  } = {}) {
    this.id = id
    this.siteId = siteId
    this.wellNo = wellNo
    this.name = name
    this.wellheadE = wellheadE
    this.wellheadN = wellheadN
    this.wellheadD = wellheadD
    this.wellDiameter = wellDiameter
    this.createTime = createTime
    this.updateTime = updateTime
  }
}
