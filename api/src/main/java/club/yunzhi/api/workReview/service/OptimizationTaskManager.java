package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.OptimizationProgress;
import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.TrajectoryFileRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryObjective;
import club.yunzhi.api.workReview.trajectory.optimizer.ObjectiveFunction;
import club.yunzhi.api.workReview.trajectory.optimizer.OptimizerFactory;
import club.yunzhi.api.workReview.trajectory.optimizer.PSOOptimizer;
import club.yunzhi.api.workReview.trajectory.optimizer.TrajectoryOptimizer;
import club.yunzhi.api.workReview.util.ExcelParser;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Component
public class OptimizationTaskManager {

    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();
    private final Map<String, OptimizationProgress> progressMap = new ConcurrentHashMap<>();
    private final ExecutorService executorService = Executors.newFixedThreadPool(4);

    private final WellRepository wellRepository;
    private final TrajectoryFileRepository trajectoryFileRepository;

    public OptimizationTaskManager(WellRepository wellRepository, TrajectoryFileRepository trajectoryFileRepository) {
        this.wellRepository = wellRepository;
        this.trajectoryFileRepository = trajectoryFileRepository;
    }

    public SseEmitter createProgressEmitter(String taskId) {
        SseEmitter emitter = new SseEmitter(300000L);

        emitter.onCompletion(() -> emitters.remove(taskId));
        emitter.onTimeout(() -> emitters.remove(taskId));
        emitter.onError(e -> emitters.remove(taskId));

        emitters.put(taskId, emitter);
        return emitter;
    }

    public void submitOptimizationTask(String taskId, TrajectoryDesignRequest request) {
        executorService.submit(() -> {
            try {
                OptimizationProgress progress = new OptimizationProgress();
                progressMap.put(taskId, progress);

                TrajectoryDesignResult result = performOptimization(taskId, request, progress);

                progress.setCompleted(true);
                progress.setResult(result);

                sendProgress(taskId, progress);

                SseEmitter emitter = emitters.get(taskId);
                if (emitter != null) {
                    emitter.complete();
                }
            } catch (Exception e) {
                OptimizationProgress progress = progressMap.get(taskId);
                if (progress != null) {
                    progress.setMessage("优化失败: " + e.getMessage());
                    sendProgress(taskId, progress);
                }
                SseEmitter emitter = emitters.get(taskId);
                if (emitter != null) {
                    emitter.completeWithError(e);
                }
            }
        });
    }

    private TrajectoryDesignResult performOptimization(String taskId, TrajectoryDesignRequest request,
                                                       OptimizationProgress progress) {
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
        int population = 50;
        int iterations = 200;

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

        double[][] bounds = config.getSevenSegmentBounds();
        ObjectiveFunction objectiveFunc = params -> objective.calculateSevenSegmentObjective(params);

        TrajectoryOptimizer optimizer = OptimizerFactory.getOptimizer(algorithmType);

        double[] bestPosition;
        if (optimizer instanceof PSOOptimizer) {
            bestPosition = ((PSOOptimizer) optimizer).optimize(objectiveFunc, config, bounds,
                    population, iterations, (iteration, total, currentBest, message) -> {
                        progress.setIteration(iteration);
                        progress.setTotalIterations(total);
                        progress.setCurrentBest(currentBest);
                        progress.setProgressPercent(iteration * 100.0 / total);
                        progress.setMessage(message);
                        sendProgress(taskId, progress);
                    });
        } else {
            bestPosition = optimizer.optimize(objectiveFunc, config, bounds, population, iterations);
        }

        // 构建结果
        java.util.Map<String, Double> bestSolution = new java.util.LinkedHashMap<>();
        String[] paramNames = WellTrajectoryConfig.SEVEN_SEG_PARAM_NAMES;
        for (int i = 0; i < paramNames.length; i++) {
            bestSolution.put(paramNames[i], bestPosition[i]);
        }

        result.setBest_solution_dict(bestSolution);

        java.util.Map<String, Object> trajectoryInfo = objective.getTrajectoryInfo(bestPosition);
        result.setFinal_deviation((Double) trajectoryInfo.getOrDefault("targetDeviation", 999.0));
        result.setOptimization_time(0.5);

        double[][] trajectory = (double[][]) trajectoryInfo.get("trajectory");
        if (trajectory != null) {
            java.util.List<TrajectoryDesignResult.TrajectoryPoint> points = new java.util.ArrayList<>();
            for (int i = 0; i < trajectory[0].length; i++) {
                points.add(new TrajectoryDesignResult.TrajectoryPoint(trajectory[0][i], trajectory[1][i], trajectory[2][i]));
            }
            result.setTrajectory_points(points);
        }

        // 生成邻井轨迹数据
        generateNeighborWellTrajectories(request, result);

        return result;
    }

    private void generateNeighborWellTrajectories(TrajectoryDesignRequest request, TrajectoryDesignResult result) {
        java.util.List<TrajectoryDesignResult.WellTrajectory> neighborWells = new java.util.ArrayList<>();

        if (request.getNeighborWellIds() != null && !request.getNeighborWellIds().isEmpty()) {
            for (String wellIdStr : request.getNeighborWellIds()) {
                try {
                    Long wellId = Long.parseLong(wellIdStr);
                    Optional<Well> wellOpt = wellRepository.findById(wellId);

                    if (wellOpt.isPresent()) {
                        Well well = wellOpt.get();
                        String wellNo = well.getWellNo();
                        
                        // 从数据库查询该井的轨迹文件
                        Optional<club.yunzhi.api.workReview.entity.TrajectoryFile> fileOpt = 
                            trajectoryFileRepository.findFirstByWellNoOrderByIdDesc(wellNo);

                        if (fileOpt.isPresent()) {
                            club.yunzhi.api.workReview.entity.TrajectoryFile trajectoryFile = fileOpt.get();
                            byte[] fileContent = trajectoryFile.getFileContent();
                            
                            // 解析Excel文件获取轨迹点
                            java.util.List<TrajectoryDesignResult.TrajectoryPoint> points = 
                                ExcelParser.parseTrajectoryFromExcel(fileContent, trajectoryFile.getFileName());

                            if (!points.isEmpty()) {
                                TrajectoryDesignResult.WellTrajectory wellTrajectory = new TrajectoryDesignResult.WellTrajectory();
                                wellTrajectory.setWellId(wellIdStr);
                                wellTrajectory.setWellNo(wellNo);
                                wellTrajectory.setWellName(well.getName() != null ? well.getName() : wellNo);
                                wellTrajectory.setTrajectory_points(points);
                                neighborWells.add(wellTrajectory);
                            }
                        }
                    }
                } catch (NumberFormatException e) {
                    // 忽略无效的井ID
                }
            }
        }

        result.setNeighbor_wells(neighborWells);
    }

    private void sendProgress(String taskId, OptimizationProgress progress) {
        SseEmitter emitter = emitters.get(taskId);
        if (emitter != null) {
            try {
                emitter.send(SseEmitter.event()
                        .name("progress")
                        .data(progress));
            } catch (IOException e) {
                emitter.completeWithError(e);
                emitters.remove(taskId);
            }
        }
    }

    public OptimizationProgress getProgress(String taskId) {
        return progressMap.get(taskId);
    }

    public void cleanupTask(String taskId) {
        emitters.remove(taskId);
        progressMap.remove(taskId);
    }
}
