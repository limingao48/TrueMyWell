package club.yunzhi.api.workReview.trajectory.optimizer;

@FunctionalInterface
public interface ObjectiveFunction {
    /**
     * 计算目标函数值
     *
     * @param params 参数数组
     * @return 目标函数值（越小越好）
     */
    double evaluate(double[] params);
}
