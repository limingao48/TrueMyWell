package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult.TrajectoryPoint;
import club.yunzhi.api.workReview.trajectory.TrajectoryAnticollisionConfig;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryObjective;
import club.yunzhi.api.workReview.trajectory.optimizer.ObjectiveFunction;
import club.yunzhi.api.workReview.trajectory.optimizer.OptimizerFactory;
import club.yunzhi.api.workReview.trajectory.optimizer.TrajectoryOptimizer;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class TrajectoryServiceImpl implements TrajectoryService {

    private static final int DEFAULT_POPULATION = 50;
    private static final int DEFAULT_ITERATIONS = 200;

    private final NeighborWellTrajectoryService neighborWellTrajectoryService;

    public TrajectoryServiceImpl(NeighborWellTrajectoryService neighborWellTrajectoryService) {
        this.neighborWellTrajectoryService = neighborWellTrajectoryService;
    }

    @Override
    public TrajectoryDesignResult design(TrajectoryDesignRequest request) {
        TrajectoryDesignResult result = new TrajectoryDesignResult();

        WellTrajectoryConfig config = new WellTrajectoryConfig();

        // 设置目标点坐标
        if (request.getTarget() != null) {
            TrajectoryDesignRequest.Target target = request.getTarget();
            if (target.getE() != null) config.E_target = target.getE();
            if (target.getN() != null) config.N_target = target.getN();
            if (target.getD() != null) config.D_target = target.getD();
        }

        // 设置井口坐标
        if (request.getWellhead() != null) {
            TrajectoryDesignRequest.Wellhead wellhead = request.getWellhead();
            if (wellhead.getE() != null) config.E_wellhead = wellhead.getE();
            if (wellhead.getN() != null) config.N_wellhead = wellhead.getN();
            if (wellhead.getD() != null) config.D_wellhead = wellhead.getD();
        }

        config.refreshLegacyEightParamBounds();

        // 获取算法参数
        String algorithmType = "PSO";
        int population = DEFAULT_POPULATION;
        int iterations = DEFAULT_ITERATIONS;

        if (request.getAlgorithm() != null) {
            TrajectoryDesignRequest.Algorithm algorithm = request.getAlgorithm();
            if (algorithm.getType() != null && !algorithm.getType().isEmpty()) {
                algorithmType = algorithm.getType();
            }
            if (algorithm.getPopulation() != null && algorithm.getPopulation() > 0) {
                population = algorithm.getPopulation();
            }
            if (algorithm.getIterations() != null && algorithm.getIterations() > 0) {
                iterations = algorithm.getIterations();
            }
            TrajectoryAnticollisionConfig.applyFromAlgorithm(algorithm, config);
        }

        WellTrajectoryObjective objective = new WellTrajectoryObjective(config);
        neighborWellTrajectoryService.attachObstaclesForOptimization(request, objective, config.safetyRadius);

        // 使用优化器工厂获取对应的优化算法
        TrajectoryOptimizer optimizer = OptimizerFactory.getOptimizer(algorithmType);

        // 定义目标函数
        ObjectiveFunction objectiveFunc = params -> objective.calculateSevenSegmentObjective(params);

        // 执行优化
        double[][] bounds = config.getSevenSegmentBounds();
        long optimizeStartNs = System.nanoTime();
        double[] bestPosition = optimizer.optimize(objectiveFunc, config, bounds, population, iterations);
        double optimizationSeconds = (System.nanoTime() - optimizeStartNs) / 1_000_000_000.0;

        // 构建结果
        Map<String, Double> bestSolution = new LinkedHashMap<>();
        String[] paramNames = WellTrajectoryConfig.SEVEN_SEG_PARAM_NAMES;
        for (int i = 0; i < paramNames.length; i++) {
            bestSolution.put(paramNames[i], bestPosition[i]);
        }

        result.setBest_solution_dict(bestSolution);

        Map<String, Object> trajectoryInfo = objective.getTrajectoryInfo(bestPosition);
        result.setFinal_deviation((Double) trajectoryInfo.getOrDefault("targetDeviation", 999.0));
        result.setOptimization_time(optimizationSeconds);

        double[][] trajectory = (double[][]) trajectoryInfo.get("trajectory");
        if (trajectory != null) {
            List<TrajectoryPoint> points = new ArrayList<>();
            for (int i = 0; i < trajectory[0].length; i++) {
                points.add(new TrajectoryPoint(trajectory[0][i], trajectory[1][i], trajectory[2][i]));
            }
            result.setTrajectory_points(points);
        }

        result.setNeighbor_wells(neighborWellTrajectoryService.loadNeighborTrajectories(request));

        return result;
    }
}
