export default class TrajectoryAlgorithm {
  constructor ({
    type = 'PSO',
    anticollisionMethod = 'SF',
    safeRadius = 10,
    minSafetyFactor = 1.2,
    minKickoffDepth = 500,
    doglegMin = 2,
    doglegMax = 5,
    population = 50,
    iterations = 200
  } = {}) {
    this.type = type
    this.anticollisionMethod = anticollisionMethod
    this.safeRadius = safeRadius
    this.minSafetyFactor = minSafetyFactor
    this.minKickoffDepth = minKickoffDepth
    this.doglegMin = doglegMin
    this.doglegMax = doglegMax
    this.population = population
    this.iterations = iterations
  }
}
