package club.yunzhi.api.workReview.entity;

import java.util.Map;

public class TrajectoryDesignResult {
    private Map<String, Double> best_solution_dict;
    private Double final_deviation;
    private Double optimization_time;

    public Map<String, Double> getBest_solution_dict() { return best_solution_dict; }
    public void setBest_solution_dict(Map<String, Double> best_solution_dict) { this.best_solution_dict = best_solution_dict; }
    public Double getFinal_deviation() { return final_deviation; }
    public void setFinal_deviation(Double final_deviation) { this.final_deviation = final_deviation; }
    public Double getOptimization_time() { return optimization_time; }
    public void setOptimization_time(Double optimization_time) { this.optimization_time = optimization_time; }
}
