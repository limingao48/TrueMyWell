package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.TrajectoryFileRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.trajectory.WellObstacleDetector;
import club.yunzhi.api.workReview.trajectory.WellTrajectoryObjective;
import club.yunzhi.api.workReview.util.ExcelParser;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 从数据库加载邻井轨迹 Excel，用于结果展示与防碰障碍物建模。
 */
@Service
public class NeighborWellTrajectoryService {

    private final WellRepository wellRepository;
    private final TrajectoryFileRepository trajectoryFileRepository;

    public NeighborWellTrajectoryService(WellRepository wellRepository,
                                         TrajectoryFileRepository trajectoryFileRepository) {
        this.wellRepository = wellRepository;
        this.trajectoryFileRepository = trajectoryFileRepository;
    }

    /**
     * 为优化目标函数注册邻井障碍物（井眼中心轨迹），用于 CTC/SF 扫描。
     *
     * @param detectorPaddingRadius 构造 {@link WellObstacleDetector} 时使用的参考半径（与 config.safetyRadius 一致即可）
     */
    public void attachObstaclesForOptimization(TrajectoryDesignRequest request,
                                               WellTrajectoryObjective objective,
                                               double detectorPaddingRadius) {
        if (request.getNeighborWellIds() == null || request.getNeighborWellIds().isEmpty()) {
            return;
        }
        for (Long wellId : request.getNeighborWellIds()) {
            try {
                Optional<Well> wellOpt = wellRepository.findById(wellId);
                if (!wellOpt.isPresent()) {
                    continue;
                }
                Well well = wellOpt.get();
                Optional<club.yunzhi.api.workReview.entity.TrajectoryFile> fileOpt =
                        trajectoryFileRepository.findFirstByWellNoOrderByIdDesc(well.getWellNo());
                if (!fileOpt.isPresent()) {
                    continue;
                }
                club.yunzhi.api.workReview.entity.TrajectoryFile trajectoryFile = fileOpt.get();
                List<TrajectoryDesignResult.TrajectoryPoint> points = ExcelParser.parseTrajectoryFromExcel(
                        trajectoryFile.getFileContent(),
                        trajectoryFile.getFileName(),
                        well.getWellheadE(),
                        well.getWellheadN(),
                        well.getWellheadD()
                );
                double[][] path = trajectoryPointsToArray(points);
                if (path.length >= 2) {
                    objective.addWellObstacle(new WellObstacleDetector(path, detectorPaddingRadius));
                }
            } catch (Exception ignored) {
                // 跳过无效邻井
            }
        }
    }

    public List<TrajectoryDesignResult.WellTrajectory> loadNeighborTrajectories(TrajectoryDesignRequest request) {
        List<TrajectoryDesignResult.WellTrajectory> neighborWells = new ArrayList<>();
        if (request.getNeighborWellIds() == null || request.getNeighborWellIds().isEmpty()) {
            return neighborWells;
        }
        for (Long wellId : request.getNeighborWellIds()) {
            try {
                Optional<Well> wellOpt = wellRepository.findById(wellId);
                if (!wellOpt.isPresent()) {
                    continue;
                }
                Well well = wellOpt.get();
                Optional<club.yunzhi.api.workReview.entity.TrajectoryFile> fileOpt =
                        trajectoryFileRepository.findFirstByWellNoOrderByIdDesc(well.getWellNo());
                if (!fileOpt.isPresent()) {
                    continue;
                }
                club.yunzhi.api.workReview.entity.TrajectoryFile trajectoryFile = fileOpt.get();
                List<TrajectoryDesignResult.TrajectoryPoint> points = ExcelParser.parseTrajectoryFromExcel(
                        trajectoryFile.getFileContent(),
                        trajectoryFile.getFileName(),
                        well.getWellheadE(),
                        well.getWellheadN(),
                        well.getWellheadD()
                );
                if (!points.isEmpty()) {
                    TrajectoryDesignResult.WellTrajectory wt = new TrajectoryDesignResult.WellTrajectory();
                    wt.setWellId(wellId.toString());
                    wt.setWellNo(well.getWellNo());
                    wt.setWellName(well.getName() != null ? well.getName() : well.getWellNo());
                    wt.setTrajectory_points(points);
                    neighborWells.add(wt);
                }
            } catch (Exception ignored) {
                // ignore
            }
        }
        return neighborWells;
    }

    static double[][] trajectoryPointsToArray(List<TrajectoryDesignResult.TrajectoryPoint> points) {
        List<double[]> rows = new ArrayList<>();
        if (points == null) {
            return new double[0][];
        }
        for (TrajectoryDesignResult.TrajectoryPoint p : points) {
            if (p == null || p.getX() == null || p.getY() == null || p.getZ() == null) {
                continue;
            }
            rows.add(new double[]{p.getX(), p.getY(), p.getZ()});
        }
        return rows.toArray(new double[0][]);
    }
}
