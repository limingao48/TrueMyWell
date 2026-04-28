package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult.TrajectoryPoint;
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
        }

        WellTrajectoryObjective objective = new WellTrajectoryObjective(config);

        // 使用优化器工厂获取对应的优化算法
        TrajectoryOptimizer optimizer = OptimizerFactory.getOptimizer(algorithmType);

        // 定义目标函数
        ObjectiveFunction objectiveFunc = params -> objective.calculateSevenSegmentObjective(params);

        // 执行优化
        double[][] bounds = config.getSevenSegmentBounds();
        double[] bestPosition = optimizer.optimize(objectiveFunc, config, bounds, population, iterations);

        // 构建结果
        Map<String, Double> bestSolution = new LinkedHashMap<>();
        String[] paramNames = WellTrajectoryConfig.SEVEN_SEG_PARAM_NAMES;
        for (int i = 0; i < paramNames.length; i++) {
            bestSolution.put(paramNames[i], bestPosition[i]);
        }

        result.setBest_solution_dict(bestSolution);

        Map<String, Object> trajectoryInfo = objective.getTrajectoryInfo(bestPosition);
        result.setFinal_deviation((Double) trajectoryInfo.getOrDefault("targetDeviation", 999.0));
        result.setOptimization_time(0.5);

        double[][] trajectory = (double[][]) trajectoryInfo.get("trajectory");
        if (trajectory != null) {
            List<TrajectoryPoint> points = new ArrayList<>();
            for (int i = 0; i < trajectory[0].length; i++) {
                points.add(new TrajectoryPoint(trajectory[0][i], trajectory[1][i], trajectory[2][i]));
            }
            result.setTrajectory_points(points);
        }

        // 生成邻井轨迹数据
        generateNeighborWellTrajectories(request, result);

        return result;
    }

    private void generateNeighborWellTrajectories(TrajectoryDesignRequest request, TrajectoryDesignResult result) {
        List<TrajectoryDesignResult.WellTrajectory> neighborWells = new ArrayList<>();

        if (request.getNeighborWellIds() != null && !request.getNeighborWellIds().isEmpty()) {
            Random random = new Random(42); // 固定种子确保可重复

            for (Long wellId : request.getNeighborWellIds()) {
                List<TrajectoryPoint> points = new ArrayList<>();

                // 生成模拟的邻井轨迹（螺旋下降）
                double baseE = random.nextDouble() * 200 - 100; // -100 ~ 100
                double baseN = random.nextDouble() * 200 - 100;
                double angle = random.nextDouble() * Math.PI * 2;
                double radius = 50 + random.nextDouble() * 50;

                for (int i = 0; i <= 100; i++) {
                    double depth = -i * 20; // 从0到-2000米
                    double theta = angle + depth * 0.005; // 螺旋角度
                    double e = baseE + Math.cos(theta) * radius;
                    double n = baseN + Math.sin(theta) * radius;

                    points.add(new TrajectoryPoint(e, n, depth));
                }

                TrajectoryDesignResult.WellTrajectory wellTrajectory = new TrajectoryDesignResult.WellTrajectory();
                wellTrajectory.setWellId(wellId.toString());
                wellTrajectory.setWellNo("邻井" + wellId.toString().substring(0, Math.min(4, wellId.toString().length())));
                wellTrajectory.setWellName("邻井" + wellId.toString().substring(0, Math.min(4, wellId.toString().length())));
                wellTrajectory.setTrajectory_points(points);

                neighborWells.add(wellTrajectory);
            }
        }

        result.setNeighbor_wells(neighborWells);
    }
}
