package club.yunzhi.api.workReview.trajectory.optimizer;

public interface ProgressCallback {
    /**
     * 进度更新回调
     *
     * @param iteration 当前迭代次数
     * @param totalIterations 总迭代次数
     * @param currentBest  当前最优目标函数值
     * @param message 进度消息
     */
    void onProgress(int iteration, int totalIterations, double currentBest, String message);
}
