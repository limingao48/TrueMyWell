package club.yunzhi.api.workReview.entity;

import java.util.List;

public class AnticollisionScanRequest {

    private Long siteId;
    private Long trajectoryId;
    private List<Long> neighborWellIds;
    private String anticollisionMethod;
    private Double safeRadius;
    private Double minSafetyFactor;

    public Long getSiteId() {
        return siteId;
    }

    public void setSiteId(Long siteId) {
        this.siteId = siteId;
    }

    public Long getTrajectoryId() {
        return trajectoryId;
    }

    public void setTrajectoryId(Long trajectoryId) {
        this.trajectoryId = trajectoryId;
    }

    public List<Long> getNeighborWellIds() {
        return neighborWellIds;
    }

    public void setNeighborWellIds(List<Long> neighborWellIds) {
        this.neighborWellIds = neighborWellIds;
    }

    public String getAnticollisionMethod() {
        return anticollisionMethod;
    }

    public void setAnticollisionMethod(String anticollisionMethod) {
        this.anticollisionMethod = anticollisionMethod;
    }

    public Double getSafeRadius() {
        return safeRadius;
    }

    public void setSafeRadius(Double safeRadius) {
        this.safeRadius = safeRadius;
    }

    public Double getMinSafetyFactor() {
        return minSafetyFactor;
    }

    public void setMinSafetyFactor(Double minSafetyFactor) {
        this.minSafetyFactor = minSafetyFactor;
    }
}
