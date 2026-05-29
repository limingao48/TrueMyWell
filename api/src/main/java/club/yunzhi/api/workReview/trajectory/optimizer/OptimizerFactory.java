package club.yunzhi.api.workReview.trajectory.optimizer;

import java.util.HashMap;
import java.util.Map;

public class OptimizerFactory {

    private static final Map<String, TrajectoryOptimizer> OPTIMIZERS = new HashMap<>();

    static {
        OPTIMIZERS.put("PSO", new PSOOptimizer());
        OPTIMIZERS.put("L-SHADE", new LSHADEOptimizer());
        OPTIMIZERS.put("L_SHADE", new LSHADEOptimizer());
        OPTIMIZERS.put("RANDOM", new RandomSearchOptimizer());
        // B2OPT 暂用 L-SHADE 近似；GA-optiGAN 由 GaOptiganOptimizationService 调用 Python 实现
        OPTIMIZERS.put("B2OPT", new LSHADEOptimizer());
    }

    public static TrajectoryOptimizer getOptimizer(String algorithmType) {
        if (algorithmType == null || algorithmType.isEmpty()) {
            return OPTIMIZERS.get("PSO");
        }

        TrajectoryOptimizer optimizer = OPTIMIZERS.get(algorithmType.toUpperCase());
        if (optimizer == null) {
            throw new IllegalArgumentException("不支持的优化算法类型: " + algorithmType);
        }

        return optimizer;
    }

    public static void registerOptimizer(String algorithmType, TrajectoryOptimizer optimizer) {
        OPTIMIZERS.put(algorithmType.toUpperCase(), optimizer);
    }
}
