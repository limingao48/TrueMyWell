package club.yunzhi.api.workReview.entity;

import java.util.List;
import java.util.Map;

public class TrajectoryDesignResult {
    private Map<String, Double> best_solution_dict;
    private Double final_deviation;
    private Double optimization_time;
    private List<TrajectoryPoint> trajectory_points;
    private List<WellTrajectory> neighbor_wells;

    public static class TrajectoryPoint {
        private Double x;
        private Double y;
        private Double z;

        public TrajectoryPoint() {}

        public TrajectoryPoint(Double x, Double y, Double z) {
            this.x = x;
            this.y = y;
            this.z = z;
        }

        public Double getX() { return x; }
        public void setX(Double x) { this.x = x; }
        public Double getY() { return y; }
        public void setY(Double y) { this.y = y; }
        public Double getZ() { return z; }
        public void setZ(Double z) { this.z = z; }
    }

    public static class WellTrajectory {
        private String wellId;
        private String wellNo;
        private String wellName;
        private List<TrajectoryPoint> trajectory_points;

        public WellTrajectory() {}

        public WellTrajectory(String wellId, String wellNo, String wellName, List<TrajectoryPoint> trajectory_points) {
            this.wellId = wellId;
            this.wellNo = wellNo;
            this.wellName = wellName;
            this.trajectory_points = trajectory_points;
        }

        public String getWellId() { return wellId; }
        public void setWellId(String wellId) { this.wellId = wellId; }
        public String getWellNo() { return wellNo; }
        public void setWellNo(String wellNo) { this.wellNo = wellNo; }
        public String getWellName() { return wellName; }
        public void setWellName(String wellName) { this.wellName = wellName; }
        public List<TrajectoryPoint> getTrajectory_points() { return trajectory_points; }
        public void setTrajectory_points(List<TrajectoryPoint> trajectory_points) { this.trajectory_points = trajectory_points; }
    }

    public Map<String, Double> getBest_solution_dict() { return best_solution_dict; }
    public void setBest_solution_dict(Map<String, Double> best_solution_dict) { this.best_solution_dict = best_solution_dict; }
    public Double getFinal_deviation() { return final_deviation; }
    public void setFinal_deviation(Double final_deviation) { this.final_deviation = final_deviation; }
    public Double getOptimization_time() { return optimization_time; }
    public void setOptimization_time(Double optimization_time) { this.optimization_time = optimization_time; }
    public List<TrajectoryPoint> getTrajectory_points() { return trajectory_points; }
    public void setTrajectory_points(List<TrajectoryPoint> trajectory_points) { this.trajectory_points = trajectory_points; }
    public List<WellTrajectory> getNeighbor_wells() { return neighbor_wells; }
    public void setNeighbor_wells(List<WellTrajectory> neighbor_wells) { this.neighbor_wells = neighbor_wells; }
}
