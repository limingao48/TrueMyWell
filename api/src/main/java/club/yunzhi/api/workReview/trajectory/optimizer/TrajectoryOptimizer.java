package club.yunzhi.api.workReview.trajectory.optimizer;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

@FunctionalInterface
public interface TrajectoryOptimizer {
    /**
     * 优化井轨迹参数
     *
     * @param objectiveFunc 目标函数，输入参数数组，返回目标函数值
     * @param config        轨迹配置
     * @param bounds        参数边界 [参数索引][min, max]
     * @param population    种群大小
     * @param iterations    迭代次数
     * @return 最优参数数组
     */
    double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                      double[][] bounds, int population, int iterations);
}
