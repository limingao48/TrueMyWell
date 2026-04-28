package club.yunzhi.api.workReview.entity;

public class OptimizationProgress {
    private int iteration;
    private int totalIterations;
    private double currentBest;
    private double progressPercent;
    private String message;
    private boolean completed;
    private TrajectoryDesignResult result;

    public OptimizationProgress() {}

    public OptimizationProgress(int iteration, int totalIterations, double currentBest, String message) {
        this.iteration = iteration;
        this.totalIterations = totalIterations;
        this.currentBest = currentBest;
        this.progressPercent = totalIterations > 0 ? (iteration * 100.0 / totalIterations) : 0;
        this.message = message;
        this.completed = false;
    }

    public int getIteration() { return iteration; }
    public void setIteration(int iteration) { this.iteration = iteration; }

    public int getTotalIterations() { return totalIterations; }
    public void setTotalIterations(int totalIterations) { this.totalIterations = totalIterations; }

    public double getCurrentBest() { return currentBest; }
    public void setCurrentBest(double currentBest) { this.currentBest = currentBest; }

    public double getProgressPercent() { return progressPercent; }
    public void setProgressPercent(double progressPercent) { this.progressPercent = progressPercent; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public boolean isCompleted() { return completed; }
    public void setCompleted(boolean completed) { this.completed = completed; }

    public TrajectoryDesignResult getResult() { return result; }
    public void setResult(TrajectoryDesignResult result) { this.result = result; }
}
