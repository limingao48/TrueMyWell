package club.yunzhi.api.workReview.entity;

import java.util.List;

public class AnticollisionScanResult {

    private Double minDistance;
    private Double minSafetyFactor;
    private String riskLevel;
    private Double nearestDepth;
    private Point nearestPoint;
    private List<ScanSegment> segments;
    private List<WellTrajectory> trajectories;

    public static class Point {
        private Double e;
        private Double n;
        private Double d;

        public Point() {}

        public Point(Double e, Double n, Double d) {
            this.e = e;
            this.n = n;
            this.d = d;
        }

        public Double getE() { return e; }
        public void setE(Double e) { this.e = e; }
        public Double getN() { return n; }
        public void setN(Double n) { this.n = n; }
        public Double getD() { return d; }
        public void setD(Double d) { this.d = d; }
    }

    public static class ScanSegment {
        private String segment;
        private Double minDist;
        private Double minSF;
        private String risk;

        public String getSegment() { return segment; }
        public void setSegment(String segment) { this.segment = segment; }
        public Double getMinDist() { return minDist; }
        public void setMinDist(Double minDist) { this.minDist = minDist; }
        public Double getMinSF() { return minSF; }
        public void setMinSF(Double minSF) { this.minSF = minSF; }
        public String getRisk() { return risk; }
        public void setRisk(String risk) { this.risk = risk; }
    }

    public static class WellTrajectory {
        private String wellId;
        private String wellNo;
        private String wellName;
        private List<TrajectoryDesignResult.TrajectoryPoint> trajectory_points;

        public String getWellId() { return wellId; }
        public void setWellId(String wellId) { this.wellId = wellId; }
        public String getWellNo() { return wellNo; }
        public void setWellNo(String wellNo) { this.wellNo = wellNo; }
        public String getWellName() { return wellName; }
        public void setWellName(String wellName) { this.wellName = wellName; }
        public List<TrajectoryDesignResult.TrajectoryPoint> getTrajectory_points() { return trajectory_points; }
        public void setTrajectory_points(List<TrajectoryDesignResult.TrajectoryPoint> trajectory_points) { this.trajectory_points = trajectory_points; }
    }

    public Double getMinDistance() { return minDistance; }
    public void setMinDistance(Double minDistance) { this.minDistance = minDistance; }
    public Double getMinSafetyFactor() { return minSafetyFactor; }
    public void setMinSafetyFactor(Double minSafetyFactor) { this.minSafetyFactor = minSafetyFactor; }
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    public Double getNearestDepth() { return nearestDepth; }
    public void setNearestDepth(Double nearestDepth) { this.nearestDepth = nearestDepth; }
    public Point getNearestPoint() { return nearestPoint; }
    public void setNearestPoint(Point nearestPoint) { this.nearestPoint = nearestPoint; }
    public List<ScanSegment> getSegments() { return segments; }
    public void setSegments(List<ScanSegment> segments) { this.segments = segments; }
    public List<WellTrajectory> getTrajectories() { return trajectories; }
    public void setTrajectories(List<WellTrajectory> trajectories) { this.trajectories = trajectories; }
}
