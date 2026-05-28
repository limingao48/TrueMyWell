package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.OptimizationProgress;
import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.trajectory.TrajectoryAnticollisionConfig;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryObjective;
import club.yunzhi.api.workReview.trajectory.optimizer.ObjectiveFunction;
import club.yunzhi.api.workReview.trajectory.optimizer.OptimizerFactory;
import club.yunzhi.api.workReview.trajectory.optimizer.ProgressAwareOptimizer;
import club.yunzhi.api.workReview.trajectory.optimizer.TrajectoryOptimizer;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Component
public class OptimizationTaskManager {

    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();
    private final Map<String, OptimizationProgress> progressMap = new ConcurrentHashMap<>();
    private final ExecutorService executorService = Executors.newFixedThreadPool(4);

    private final NeighborWellTrajectoryService neighborWellTrajectoryService;
    private final GaOptiganOptimizationService gaOptiganOptimizationService;

    public OptimizationTaskManager(NeighborWellTrajectoryService neighborWellTrajectoryService,
                                  GaOptiganOptimizationService gaOptiganOptimizationService) {
        this.neighborWellTrajectoryService = neighborWellTrajectoryService;
        this.gaOptiganOptimizationService = gaOptiganOptimizationService;
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
        if (request.getLandingRequirement() != null) {
            TrajectoryDesignRequest.LandingRequirement lr = request.getLandingRequirement();
            if (lr.getInclinationMin() != null) {
                config.landingInclinationMin = lr.getInclinationMin();
            }
            if (lr.getInclinationMax() != null) {
                config.landingInclinationMax = lr.getInclinationMax();
            }
            if (lr.getAzimuthMin() != null) {
                config.landingAzimuthMin = lr.getAzimuthMin();
            }
            if (lr.getAzimuthMax() != null) {
                config.landingAzimuthMax = lr.getAzimuthMax();
            }
            if (lr.getVerticalTolerance() != null) {
                config.verticalTolerance = lr.getVerticalTolerance();
            }
            if (lr.getHorizontalTolerance() != null) {
                config.horizontalTolerance = lr.getHorizontalTolerance();
            }
        }

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
            if (algorithm.getMinKickoffDepth() != null) {
                config.sevenL0Range[0] = Math.max(0.0, algorithm.getMinKickoffDepth());
            }
            if (algorithm.getDoglegMin() != null) {
                double minDogleg = Math.max(0.1, algorithm.getDoglegMin());
                config.sevenDLS1Range[0] = minDogleg;
                config.sevenDLSTurnRange[0] = minDogleg;
                config.sevenDLS6Range[0] = minDogleg;
            }
            if (algorithm.getDoglegMax() != null) {
                double maxDogleg = Math.max(config.sevenDLS1Range[0], algorithm.getDoglegMax());
                config.sevenDLS1Range[1] = maxDogleg;
                config.sevenDLSTurnRange[1] = maxDogleg;
                config.sevenDLS6Range[1] = maxDogleg;
            }
            TrajectoryAnticollisionConfig.applyFromAlgorithm(algorithm, config);
        }

        if (config.landingInclinationMin > config.landingInclinationMax) {
            double t = config.landingInclinationMin;
            config.landingInclinationMin = config.landingInclinationMax;
            config.landingInclinationMax = t;
        }
        config.sevenAlphaERange[0] = config.landingInclinationMin;
        config.sevenAlphaERange[1] = config.landingInclinationMax;

        if (config.landingAzimuthMin <= config.landingAzimuthMax) {
            config.sevenPhiTargetRange[0] = config.landingAzimuthMin;
            config.sevenPhiTargetRange[1] = config.landingAzimuthMax;
        } else {
            config.sevenPhiTargetRange[0] = 0.0;
            config.sevenPhiTargetRange[1] = 360.0;
        }

        config.sevenL0Range[1] = Math.max(config.sevenL0Range[1], config.sevenL0Range[0] + 1.0);
        config.refreshSevenSegmentBounds();

        config.D_kop_min = config.sevenL0Range[0];
        config.refreshLegacyEightParamBounds();

        if (GaOptiganOptimizationService.isGaOptiganAlgorithm(algorithmType)) {
            int progressTotal = iterations;
            if (request.getAlgorithm() != null && request.getAlgorithm().getMaxEvaluations() != null
                    && request.getAlgorithm().getMaxEvaluations() > 0) {
                progressTotal = request.getAlgorithm().getMaxEvaluations();
            }
            return runGaOptiganOptimization(taskId, request, progress, progressTotal);
        }

        WellTrajectoryObjective objective = new WellTrajectoryObjective(config);
        neighborWellTrajectoryService.attachObstaclesForOptimization(request, objective, config.safetyRadius);

        double[][] bounds = config.getSevenSegmentBounds();
        ObjectiveFunction objectiveFunc = params -> objective.calculateSevenSegmentObjective(params);

        TrajectoryOptimizer optimizer = OptimizerFactory.getOptimizer(algorithmType);

        long optimizeStartNs = System.nanoTime();
        double[] bestPosition;
        if (optimizer instanceof ProgressAwareOptimizer) {
            bestPosition = ((ProgressAwareOptimizer) optimizer).optimize(objectiveFunc, config, bounds,
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
        double optimizationSeconds = (System.nanoTime() - optimizeStartNs) / 1_000_000_000.0;

        // 构建结果
        java.util.Map<String, Double> bestSolution = new java.util.LinkedHashMap<>();
        String[] paramNames = WellTrajectoryConfig.SEVEN_SEG_PARAM_NAMES;
        for (int i = 0; i < paramNames.length; i++) {
            bestSolution.put(paramNames[i], bestPosition[i]);
        }

        result.setBest_solution_dict(bestSolution);

        java.util.Map<String, Object> trajectoryInfo = objective.getTrajectoryInfo(bestPosition);
        result.setFinal_deviation((Double) trajectoryInfo.getOrDefault("targetDeviation", 999.0));
        result.setOptimization_time(optimizationSeconds);

        double[][] trajectory = (double[][]) trajectoryInfo.get("trajectory");
        if (trajectory != null) {
            java.util.List<TrajectoryDesignResult.TrajectoryPoint> points = new java.util.ArrayList<>();
            for (int i = 0; i < trajectory[0].length; i++) {
                points.add(new TrajectoryDesignResult.TrajectoryPoint(trajectory[0][i], trajectory[1][i], trajectory[2][i]));
            }
            result.setTrajectory_points(points);
        }

        result.setNeighbor_wells(neighborWellTrajectoryService.loadNeighborTrajectories(request));

        return result;
    }

    private TrajectoryDesignResult runGaOptiganOptimization(String taskId,
                                                            TrajectoryDesignRequest request,
                                                            OptimizationProgress progress,
                                                            int totalIterations) {
        progress.setTotalIterations(totalIterations);
        progress.setMessage("正在启动 GA-optiGAN（Python + PyTorch）...");
        progress.setProgressPercent(1.0);
        sendProgress(taskId, progress);

        try {
            TrajectoryDesignResult result = gaOptiganOptimizationService.runOptimization(
                    request,
                    (iteration, total, currentBest, message) -> {
                        progress.setIteration(iteration);
                        progress.setTotalIterations(total);
                        progress.setCurrentBest(currentBest);
                        progress.setProgressPercent(Math.min(99.0, Math.max(1.0, iteration * 100.0 / Math.max(1, total))));
                        progress.setMessage(message);
                        sendProgress(taskId, progress);
                    }
            );

            progress.setIteration(totalIterations);
            progress.setProgressPercent(100.0);
            progress.setMessage("GA-optiGAN 优化完成");
            if (result.getBest_solution_dict() != null && result.getFinal_deviation() != null) {
                progress.setCurrentBest(result.getFinal_deviation());
            }
            sendProgress(taskId, progress);
            return result;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("GA-optiGAN 优化被中断", e);
        } catch (IOException e) {
            throw new RuntimeException("GA-optiGAN 优化失败: " + e.getMessage(), e);
        }
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
