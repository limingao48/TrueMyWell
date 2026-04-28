package club.yunzhi.api.workReview.entity;

import java.util.List;

public class TrajectoryDesignRequest {
    private Long siteId;
    private Target target;
    private LandingRequirement landingRequirement;
    private Wellhead wellhead;
    private List<Long> neighborWellIds;
    private Algorithm algorithm;

    public static class Target {
        private Double e;
        private Double n;
        private Double d;

        public Double getE() { return e; }
        public void setE(Double e) { this.e = e; }
        public Double getN() { return n; }
        public void setN(Double n) { this.n = n; }
        public Double getD() { return d; }
        public void setD(Double d) { this.d = d; }
    }

    public static class LandingRequirement {
        private Double inclinationMin;
        private Double inclinationMax;
        private Double azimuthMin;
        private Double azimuthMax;
        private Double verticalTolerance;
        private Double horizontalTolerance;

        public Double getInclinationMin() { return inclinationMin; }
        public void setInclinationMin(Double inclinationMin) { this.inclinationMin = inclinationMin; }
        public Double getInclinationMax() { return inclinationMax; }
        public void setInclinationMax(Double inclinationMax) { this.inclinationMax = inclinationMax; }
        public Double getAzimuthMin() { return azimuthMin; }
        public void setAzimuthMin(Double azimuthMin) { this.azimuthMin = azimuthMin; }
        public Double getAzimuthMax() { return azimuthMax; }
        public void setAzimuthMax(Double azimuthMax) { this.azimuthMax = azimuthMax; }
        public Double getVerticalTolerance() { return verticalTolerance; }
        public void setVerticalTolerance(Double verticalTolerance) { this.verticalTolerance = verticalTolerance; }
        public Double getHorizontalTolerance() { return horizontalTolerance; }
        public void setHorizontalTolerance(Double horizontalTolerance) { this.horizontalTolerance = horizontalTolerance; }
    }

    public static class Wellhead {
        private Double e;
        private Double n;
        private Double d;

        public Double getE() { return e; }
        public void setE(Double e) { this.e = e; }
        public Double getN() { return n; }
        public void setN(Double n) { this.n = n; }
        public Double getD() { return d; }
        public void setD(Double d) { this.d = d; }
    }

    public static class Algorithm {
        private String type;
        private String anticollisionMethod;
        private Double safeRadius;
        private Double minSafetyFactor;
        private Double minKickoffDepth;
        private Double doglegMin;
        private Double doglegMax;
        private Integer population;
        private Integer iterations;

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public String getAnticollisionMethod() { return anticollisionMethod; }
        public void setAnticollisionMethod(String anticollisionMethod) { this.anticollisionMethod = anticollisionMethod; }
        public Double getSafeRadius() { return safeRadius; }
        public void setSafeRadius(Double safeRadius) { this.safeRadius = safeRadius; }
        public Double getMinSafetyFactor() { return minSafetyFactor; }
        public void setMinSafetyFactor(Double minSafetyFactor) { this.minSafetyFactor = minSafetyFactor; }
        public Double getMinKickoffDepth() { return minKickoffDepth; }
        public void setMinKickoffDepth(Double minKickoffDepth) { this.minKickoffDepth = minKickoffDepth; }
        public Double getDoglegMin() { return doglegMin; }
        public void setDoglegMin(Double doglegMin) { this.doglegMin = doglegMin; }
        public Double getDoglegMax() { return doglegMax; }
        public void setDoglegMax(Double doglegMax) { this.doglegMax = doglegMax; }
        public Integer getPopulation() { return population; }
        public void setPopulation(Integer population) { this.population = population; }
        public Integer getIterations() { return iterations; }
        public void setIterations(Integer iterations) { this.iterations = iterations; }
    }

    public Long getSiteId() { return siteId; }
    public void setSiteId(Long siteId) { this.siteId = siteId; }
    public Target getTarget() { return target; }
    public void setTarget(Target target) { this.target = target; }
    public LandingRequirement getLandingRequirement() { return landingRequirement; }
    public void setLandingRequirement(LandingRequirement landingRequirement) { this.landingRequirement = landingRequirement; }
    public Wellhead getWellhead() { return wellhead; }
    public void setWellhead(Wellhead wellhead) { this.wellhead = wellhead; }
    public List<Long> getNeighborWellIds() { return neighborWellIds; }
    public void setNeighborWellIds(List<Long> neighborWellIds) { this.neighborWellIds = neighborWellIds; }
    public Algorithm getAlgorithm() { return algorithm; }
    public void setAlgorithm(Algorithm algorithm) { this.algorithm = algorithm; }
}
