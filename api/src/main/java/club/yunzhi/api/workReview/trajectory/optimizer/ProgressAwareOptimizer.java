package club.yunzhi.api.workReview.trajectory.optimizer;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

public interface ProgressAwareOptimizer extends TrajectoryOptimizer {
    double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                      double[][] bounds, int population, int iterations,
                      ProgressCallback callback);
}
