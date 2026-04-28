export default class LandingRequirement {
  constructor ({
    inclinationMin = 0,
    inclinationMax = 90,
    azimuthMin = 0,
    azimuthMax = 360,
    verticalTolerance = 5,
    horizontalTolerance = 5
  } = {}) {
    this.inclinationMin = inclinationMin
    this.inclinationMax = inclinationMax
    this.azimuthMin = azimuthMin
    this.azimuthMax = azimuthMax
    this.verticalTolerance = verticalTolerance
    this.horizontalTolerance = horizontalTolerance
  }
}
