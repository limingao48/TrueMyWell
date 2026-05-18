package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.AnticollisionScanRequest;
import club.yunzhi.api.workReview.entity.AnticollisionScanResult;
import club.yunzhi.api.workReview.entity.PendingDrillWell;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.TrajectoryFileRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.trajectory.WellObstacleDetector;
import club.yunzhi.api.workReview.trajectory.iscwsa.IscwsaMwdParameters;
import club.yunzhi.api.workReview.trajectory.iscwsa.IscwsaMwdSeparationFactor;
import club.yunzhi.api.workReview.util.ExcelParser;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class AnticollisionServiceImpl implements AnticollisionService {

    private final WellRepository wellRepository;
    private final TrajectoryFileRepository trajectoryFileRepository;
    private final PendingDrillWellService pendingDrillWellService;

    public AnticollisionServiceImpl(WellRepository wellRepository, 
                                    TrajectoryFileRepository trajectoryFileRepository,
                                    PendingDrillWellService pendingDrillWellService) {
        this.wellRepository = wellRepository;
        this.trajectoryFileRepository = trajectoryFileRepository;
        this.pendingDrillWellService = pendingDrillWellService;
    }

    @Override
    public AnticollisionScanResult scan(AnticollisionScanRequest request) {
        AnticollisionScanResult result = new AnticollisionScanResult();

        List<AnticollisionScanResult.WellTrajectory> trajectories = new ArrayList<>();

        // 获取待扫描井的轨迹（优先从待钻井表查询）
        if (request.getTrajectoryId() != null) {
            AnticollisionScanResult.WellTrajectory traj = loadPendingDrillWellTrajectory(request.getTrajectoryId());
            if (traj == null) {
                Optional<Well> wellOpt = wellRepository.findById(request.getTrajectoryId());
                if (wellOpt.isPresent()) {
                    traj = loadTrajectory(wellOpt.get());
                }
            }
            if (traj != null) {
                trajectories.add(traj);
            }
        }

        // 获取邻井轨迹
        if (request.getNeighborWellIds() != null) {
            for (Long wellId : request.getNeighborWellIds()) {
                Optional<Well> wellOpt = wellRepository.findById(wellId);
                if (wellOpt.isPresent()) {
                    Well well = wellOpt.get();
                    AnticollisionScanResult.WellTrajectory traj = loadTrajectory(well);
                    if (traj != null) {
                        trajectories.add(traj);
                    }
                }
            }
        }

        result.setTrajectories(trajectories);

        // 执行防碰扫描计算
        performScanCalculation(request, result, trajectories);

        return result;
    }

    private AnticollisionScanResult.WellTrajectory loadTrajectory(Well well) {
        String wellNo = well.getWellNo();
        Optional<club.yunzhi.api.workReview.entity.TrajectoryFile> fileOpt = 
            trajectoryFileRepository.findFirstByWellNoOrderByIdDesc(wellNo);

        if (fileOpt.isPresent()) {
            club.yunzhi.api.workReview.entity.TrajectoryFile file = fileOpt.get();
            byte[] content = file.getFileContent();
            
            List<TrajectoryDesignResult.TrajectoryPoint> points = 
                ExcelParser.parseTrajectoryFromExcel(content, file.getFileName(), 
                    well.getWellheadE(), well.getWellheadN(), well.getWellheadD());

            if (!points.isEmpty()) {
                AnticollisionScanResult.WellTrajectory traj = new AnticollisionScanResult.WellTrajectory();
                traj.setWellId(String.valueOf(well.getId()));
                traj.setWellNo(wellNo);
                traj.setWellName(well.getName() != null ? well.getName() : wellNo);
                traj.setTrajectory_points(points);
                return traj;
            }
        }

        return null;
    }

    private AnticollisionScanResult.WellTrajectory loadPendingDrillWellTrajectory(Long wellId) {
        try {
            PendingDrillWell pendingWell = pendingDrillWellService.getById(wellId);
            if (pendingWell == null) {
                return null;
            }
            
            byte[] fileContent = pendingWell.getTrajectoryFileContent();
            String fileName = pendingWell.getTrajectoryFileName();
            
            if (fileContent == null || fileContent.length == 0 || fileName == null) {
                return null;
            }
            
            List<TrajectoryDesignResult.TrajectoryPoint> points = 
                ExcelParser.parseTrajectoryFromExcel(fileContent, fileName,
                    pendingWell.getWellheadE(), pendingWell.getWellheadN(), pendingWell.getWellheadD());
            
            if (!points.isEmpty()) {
                AnticollisionScanResult.WellTrajectory traj = new AnticollisionScanResult.WellTrajectory();
                traj.setWellId(String.valueOf(pendingWell.getId()));
                traj.setWellNo(pendingWell.getName() != null ? pendingWell.getName() : "待钻井" + pendingWell.getId());
                traj.setWellName(pendingWell.getName() != null ? pendingWell.getName() : "待钻井" + pendingWell.getId());
                traj.setTrajectory_points(points);
                return traj;
            }
        } catch (Exception e) {
            // 待钻井不存在或查询失败，返回null
        }
        return null;
    }

    private double[][] convertToTrajectoryArray(List<TrajectoryDesignResult.TrajectoryPoint> points) {
        if (points == null || points.isEmpty()) {
            return new double[0][3];
        }
        double[][] trajectory = new double[points.size()][3];
        for (int i = 0; i < points.size(); i++) {
            TrajectoryDesignResult.TrajectoryPoint p = points.get(i);
            trajectory[i][0] = p.getX() != null ? p.getX() : 0.0;
            trajectory[i][1] = p.getY() != null ? p.getY() : 0.0;
            trajectory[i][2] = p.getZ() != null ? p.getZ() : 0.0;
        }
        return trajectory;
    }

    private void performScanCalculation(AnticollisionScanRequest request, AnticollisionScanResult result, 
                                        List<AnticollisionScanResult.WellTrajectory> trajectories) {
        if (trajectories.size() < 2) {
            result.setMinDistance(0.0);
            result.setMinSafetyFactor(0.0);
            result.setRiskLevel("安全");
            result.setNearestDepth(0.0);
            result.setNearestPoint(new AnticollisionScanResult.Point(0.0, 0.0, 0.0));
            result.setSegments(new ArrayList<>());
            return;
        }

        // 获取待扫描井的轨迹并转换为三维数组格式
        AnticollisionScanResult.WellTrajectory designTraj = trajectories.get(0);
        double[][] designTrajectory = convertToTrajectoryArray(designTraj.getTrajectory_points());

        // 默认参数
        double safetyRadius = request.getSafeRadius() != null ? request.getSafeRadius() : 10.0;
        double minSafetyFactor = request.getMinSafetyFactor() != null ? request.getMinSafetyFactor() : 1.2;
        boolean isSFMmode = "SF".equalsIgnoreCase(request.getAnticollisionMethod());

        double minDistance = Double.MAX_VALUE;
        double minSF = Double.MAX_VALUE;
        double nearestDepth = 0.0;
        AnticollisionScanResult.Point nearestPoint = new AnticollisionScanResult.Point(0.0, 0.0, 0.0);

        // 初始化 MWD 参数（用于 SF 计算）
        IscwsaMwdParameters mwdParams = new IscwsaMwdParameters(0.6, Math.toRadians(0.2), Math.toRadians(0.3));

        // 计算与每口邻井的最小距离/SF
        for (int i = 1; i < trajectories.size(); i++) {
            AnticollisionScanResult.WellTrajectory neighborTraj = trajectories.get(i);
            double[][] neighborTrajectory = convertToTrajectoryArray(neighborTraj.getTrajectory_points());
            WellObstacleDetector detector = new WellObstacleDetector(neighborTrajectory, safetyRadius);
            
            if (isSFMmode) {
                // SF 方法：计算最小分离系数
                double fs = IscwsaMwdSeparationFactor.minimumSeparationFactorScan(
                        designTrajectory,
                        neighborTrajectory,
                        mwdParams,
                        mwdParams,
                        1.0);
                
                if (Double.isFinite(fs) && fs < minSF) {
                    minSF = fs;
                    // SF 模式下距离也需要计算用于风险判断
                    double dist = detector.minCenterToCenterScanDistance(designTrajectory);
                    if (dist < minDistance) {
                        minDistance = dist;
                    }
                }
            } else {
                // CTC 方法：计算井眼中心最小三维距离
                double dist = detector.minCenterToCenterScanDistance(designTrajectory);
                
                if (Double.isFinite(dist) && dist < minDistance) {
                    minDistance = dist;
                    minSF = dist / safetyRadius;
                }
            }
        }

        // 获取最近点深度（从设计轨迹中获取）
        if (designTrajectory.length > 0) {
            nearestDepth = Math.abs(designTrajectory[designTrajectory.length - 1][2]);
        }

        result.setMinDistance(Math.round(minDistance * 100.0) / 100.0);
        result.setMinSafetyFactor(Math.round(minSF * 100.0) / 100.0);
        result.setNearestDepth(Math.round(nearestDepth * 100.0) / 100.0);
        result.setNearestPoint(nearestPoint);

        // 判断风险等级
        double threshold = request.getMinSafetyFactor() != null ? request.getMinSafetyFactor() : 1.2;
        if ("SF".equals(request.getAnticollisionMethod())) {
            if (minSF >= threshold) {
                result.setRiskLevel("安全");
            } else if (minSF >= threshold * 0.8) {
                result.setRiskLevel("预警");
            } else {
                result.setRiskLevel("危险");
            }
        } else {
            if (minDistance >= (request.getSafeRadius() != null ? request.getSafeRadius() : 10.0)) {
                result.setRiskLevel("安全");
            } else if (minDistance >= (request.getSafeRadius() != null ? request.getSafeRadius() : 10.0) * 0.8) {
                result.setRiskLevel("预警");
            } else {
                result.setRiskLevel("危险");
            }
        }

        // 生成井段扫描结果
        List<AnticollisionScanResult.ScanSegment> segments = new ArrayList<>();
        double totalDepth = designTrajectory.length > 0 ? Math.abs(designTrajectory[designTrajectory.length - 1][2]) : 2500.0;
        int segmentCount = 5;
        double segmentDepth = totalDepth / segmentCount;

        for (int i = 0; i < segmentCount; i++) {
            AnticollisionScanResult.ScanSegment seg = new AnticollisionScanResult.ScanSegment();
            double startDepth = i * segmentDepth;
            double endDepth = (i + 1) * segmentDepth;
            seg.setSegment((int)startDepth + "-" + (int)endDepth + "m");
            
            double segMinDist = Double.MAX_VALUE;
            double segMinSF = Double.MAX_VALUE;
            
            for (TrajectoryDesignResult.TrajectoryPoint p : designTraj.getTrajectory_points()) {
                double depth = Math.abs(p.getZ());
                if (depth >= startDepth && depth < endDepth) {
                    for (int j = 1; j < trajectories.size(); j++) {
                        for (TrajectoryDesignResult.TrajectoryPoint np : trajectories.get(j).getTrajectory_points()) {
                            double dx = p.getX() - np.getX();
                            double dy = p.getY() - np.getY();
                            double dz = p.getZ() - np.getZ();
                            double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
                            double sf = dist / (request.getSafeRadius() != null ? request.getSafeRadius() : 10.0);
                            
                            if (dist < segMinDist) {
                                segMinDist = dist;
                                segMinSF = sf;
                            }
                        }
                    }
                }
            }
            
            seg.setMinDist(Math.round(segMinDist * 100.0) / 100.0);
            seg.setMinSF(Math.round(segMinSF * 100.0) / 100.0);
            
            double segThreshold = request.getMinSafetyFactor() != null ? request.getMinSafetyFactor() : 1.2;
            if ("SF".equals(request.getAnticollisionMethod())) {
                if (segMinSF >= segThreshold) {
                    seg.setRisk("安全");
                } else if (segMinSF >= segThreshold * 0.8) {
                    seg.setRisk("预警");
                } else {
                    seg.setRisk("危险");
                }
            } else {
                double safeRadius = request.getSafeRadius() != null ? request.getSafeRadius() : 10.0;
                if (segMinDist >= safeRadius) {
                    seg.setRisk("安全");
                } else if (segMinDist >= safeRadius * 0.8) {
                    seg.setRisk("预警");
                } else {
                    seg.setRisk("危险");
                }
            }
            
            segments.add(seg);
        }
        
        result.setSegments(segments);
    }
}
