package club.yunzhi.api.workReview.entity;

import java.util.List;

public class WhileDrillingEvaluationResult {
    private String sessionId;
    private Long pendingWellId;
    private String wellName;
    private Double currentX;
    private Double currentY;
    private Double currentZ;
    private Double designX;
    private Double designY;
    private Double horizontalDistance;
    private Double alertDistanceThreshold;
    private Boolean distanceExpanding;
    private Boolean predictionTriggered;
    private Boolean predictionTrendExpanding;
    private Boolean shouldStopDrilling;
    private String status;
    private String message;
    private Double doglegDeg;
    private Double dlsDegPer30m;
    private List<PredictionPoint> predictionPoints;
    private Long timestamp;

    /** 蒙特卡洛抽样次数 */
    private Integer monteCarloSampleCount;
    /** 蒙特卡洛综合偏差样本数（外推2步：下一步>阈值且下下步更大） */
    private Integer monteCarloComprehensiveCount;
    /** 综合概率 (0~100%) */
    private Double monteCarloComprehensiveProbability;
    /** 下下步水平偏移样本均值 (m) */
    private Double monteCarloMeanSecondStepDistance;
    /** 综合偏差判定阈值 (m) */
    private Double monteCarloComprehensiveThresholdM;
    /** 蒙特卡洛是否建议停钻 */
    private Boolean monteCarloStopRecommended;
    private Double iscwsaSigmaMd;
    private Double iscwsaSigmaIncDeg;
    private Double iscwsaSigmaAziDeg;

    public static class PredictionPoint {
        private Double x;
        private Double y;
        private Double z;
        private Double horizontalDistance;
        private Double extrapolatedMd;

        public Double getX() { return x; }
        public void setX(Double x) { this.x = x; }
        public Double getY() { return y; }
        public void setY(Double y) { this.y = y; }
        public Double getZ() { return z; }
        public void setZ(Double z) { this.z = z; }
        public Double getHorizontalDistance() { return horizontalDistance; }
        public void setHorizontalDistance(Double horizontalDistance) { this.horizontalDistance = horizontalDistance; }
        public Double getExtrapolatedMd() { return extrapolatedMd; }
        public void setExtrapolatedMd(Double extrapolatedMd) { this.extrapolatedMd = extrapolatedMd; }
    }

    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public Long getPendingWellId() { return pendingWellId; }
    public void setPendingWellId(Long pendingWellId) { this.pendingWellId = pendingWellId; }
    public String getWellName() { return wellName; }
    public void setWellName(String wellName) { this.wellName = wellName; }
    public Double getCurrentX() { return currentX; }
    public void setCurrentX(Double currentX) { this.currentX = currentX; }
    public Double getCurrentY() { return currentY; }
    public void setCurrentY(Double currentY) { this.currentY = currentY; }
    public Double getCurrentZ() { return currentZ; }
    public void setCurrentZ(Double currentZ) { this.currentZ = currentZ; }
    public Double getDesignX() { return designX; }
    public void setDesignX(Double designX) { this.designX = designX; }
    public Double getDesignY() { return designY; }
    public void setDesignY(Double designY) { this.designY = designY; }
    public Double getHorizontalDistance() { return horizontalDistance; }
    public void setHorizontalDistance(Double horizontalDistance) { this.horizontalDistance = horizontalDistance; }
    public Double getAlertDistanceThreshold() { return alertDistanceThreshold; }
    public void setAlertDistanceThreshold(Double alertDistanceThreshold) { this.alertDistanceThreshold = alertDistanceThreshold; }
    public Boolean getDistanceExpanding() { return distanceExpanding; }
    public void setDistanceExpanding(Boolean distanceExpanding) { this.distanceExpanding = distanceExpanding; }
    public Boolean getPredictionTriggered() { return predictionTriggered; }
    public void setPredictionTriggered(Boolean predictionTriggered) { this.predictionTriggered = predictionTriggered; }
    public Boolean getPredictionTrendExpanding() { return predictionTrendExpanding; }
    public void setPredictionTrendExpanding(Boolean predictionTrendExpanding) { this.predictionTrendExpanding = predictionTrendExpanding; }
    public Boolean getShouldStopDrilling() { return shouldStopDrilling; }
    public void setShouldStopDrilling(Boolean shouldStopDrilling) { this.shouldStopDrilling = shouldStopDrilling; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public Double getDoglegDeg() { return doglegDeg; }
    public void setDoglegDeg(Double doglegDeg) { this.doglegDeg = doglegDeg; }
    public Double getDlsDegPer30m() { return dlsDegPer30m; }
    public void setDlsDegPer30m(Double dlsDegPer30m) { this.dlsDegPer30m = dlsDegPer30m; }
    public List<PredictionPoint> getPredictionPoints() { return predictionPoints; }
    public void setPredictionPoints(List<PredictionPoint> predictionPoints) { this.predictionPoints = predictionPoints; }
    public Long getTimestamp() { return timestamp; }
    public void setTimestamp(Long timestamp) { this.timestamp = timestamp; }
    public Integer getMonteCarloSampleCount() { return monteCarloSampleCount; }
    public void setMonteCarloSampleCount(Integer monteCarloSampleCount) { this.monteCarloSampleCount = monteCarloSampleCount; }
    public Integer getMonteCarloComprehensiveCount() { return monteCarloComprehensiveCount; }
    public void setMonteCarloComprehensiveCount(Integer v) { this.monteCarloComprehensiveCount = v; }
    public Double getMonteCarloComprehensiveProbability() { return monteCarloComprehensiveProbability; }
    public void setMonteCarloComprehensiveProbability(Double v) { this.monteCarloComprehensiveProbability = v; }
    public Double getMonteCarloMeanSecondStepDistance() { return monteCarloMeanSecondStepDistance; }
    public void setMonteCarloMeanSecondStepDistance(Double v) { this.monteCarloMeanSecondStepDistance = v; }
    public Double getMonteCarloComprehensiveThresholdM() { return monteCarloComprehensiveThresholdM; }
    public void setMonteCarloComprehensiveThresholdM(Double v) { this.monteCarloComprehensiveThresholdM = v; }
    public Boolean getMonteCarloStopRecommended() { return monteCarloStopRecommended; }
    public void setMonteCarloStopRecommended(Boolean monteCarloStopRecommended) { this.monteCarloStopRecommended = monteCarloStopRecommended; }
    public Double getIscwsaSigmaMd() { return iscwsaSigmaMd; }
    public void setIscwsaSigmaMd(Double iscwsaSigmaMd) { this.iscwsaSigmaMd = iscwsaSigmaMd; }
    public Double getIscwsaSigmaIncDeg() { return iscwsaSigmaIncDeg; }
    public void setIscwsaSigmaIncDeg(Double iscwsaSigmaIncDeg) { this.iscwsaSigmaIncDeg = iscwsaSigmaIncDeg; }
    public Double getIscwsaSigmaAziDeg() { return iscwsaSigmaAziDeg; }
    public void setIscwsaSigmaAziDeg(Double iscwsaSigmaAziDeg) { this.iscwsaSigmaAziDeg = iscwsaSigmaAziDeg; }
}
