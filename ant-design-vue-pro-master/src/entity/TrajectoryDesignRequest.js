import TrajectoryTarget from './TrajectoryTarget'
import LandingRequirement from './LandingRequirement'
import Wellhead from './Wellhead'
import TrajectoryAlgorithm from './TrajectoryAlgorithm'

export default class TrajectoryDesignRequest {
  constructor ({
    siteId = '',
    target = new TrajectoryTarget(),
    landingRequirement = new LandingRequirement(),
    wellhead = new Wellhead(),
    neighborWellIds = [],
    algorithm = new TrajectoryAlgorithm()
  } = {}) {
    this.siteId = siteId
    this.target = target
    this.landingRequirement = landingRequirement
    this.wellhead = wellhead
    this.neighborWellIds = neighborWellIds
    this.algorithm = algorithm
  }

  static fromForm (form) {
    return new TrajectoryDesignRequest({
      siteId: form.siteId,
      target: new TrajectoryTarget(form.target),
      landingRequirement: new LandingRequirement(form.landingRequirement),
      wellhead: new Wellhead(form.wellhead),
      neighborWellIds: form.neighborWellIds || [],
      algorithm: new TrajectoryAlgorithm(form.algorithm)
    })
  }

  toRequest () {
    return {
      siteId: this.siteId,
      target: this.target,
      landingRequirement: this.landingRequirement,
      wellhead: this.wellhead,
      neighborWellIds: this.neighborWellIds,
      algorithm: this.algorithm
    }
  }
}
