package club.yunzhi.api.workReview.dto;

import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;

import java.util.List;
import java.util.Map;

/**
 * 保存待钻井请求体。须指定 {@code siteId} 归属井场。服务端根据设计轨迹点（与 3D 图同源）反算「测深/井斜/网格方位」Excel 入库；
 * 若未传轨迹点或点数不足，则回退为根据七段式参数在服务端重算轨迹后再生成 Excel。
 */
public class PendingDrillWellSaveDto {

    /** 所属井场 ID（必填，与基础数据井场一致） */
    private Long siteId;
    private String name;
    private Double wellheadE;
    private Double wellheadN;
    private Double wellheadD;
    private Double targetE;
    private Double targetN;
    private Double targetD;
    /** 七段式 12 参数键值对（与 {@link club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig#SEVEN_SEG_PARAM_NAMES} 一致） */
    private Map<String, Object> sevenSegmentParams;
    private Double finalDeviation;
    private Double optimizationTime;
    /** 设计井空间轨迹点（E/N/D 即 x/y/z），与轨迹设计结果、3D 图一致；优先用于生成 Excel */
    private List<TrajectoryDesignResult.TrajectoryPoint> trajectoryPoints;

    public Long getSiteId() {
        return siteId;
    }

    public void setSiteId(Long siteId) {
        this.siteId = siteId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Double getWellheadE() {
        return wellheadE;
    }

    public void setWellheadE(Double wellheadE) {
        this.wellheadE = wellheadE;
    }

    public Double getWellheadN() {
        return wellheadN;
    }

    public void setWellheadN(Double wellheadN) {
        this.wellheadN = wellheadN;
    }

    public Double getWellheadD() {
        return wellheadD;
    }

    public void setWellheadD(Double wellheadD) {
        this.wellheadD = wellheadD;
    }

    public Double getTargetE() {
        return targetE;
    }

    public void setTargetE(Double targetE) {
        this.targetE = targetE;
    }

    public Double getTargetN() {
        return targetN;
    }

    public void setTargetN(Double targetN) {
        this.targetN = targetN;
    }

    public Double getTargetD() {
        return targetD;
    }

    public void setTargetD(Double targetD) {
        this.targetD = targetD;
    }

    public Map<String, Object> getSevenSegmentParams() {
        return sevenSegmentParams;
    }

    public void setSevenSegmentParams(Map<String, Object> sevenSegmentParams) {
        this.sevenSegmentParams = sevenSegmentParams;
    }

    public Double getFinalDeviation() {
        return finalDeviation;
    }

    public void setFinalDeviation(Double finalDeviation) {
        this.finalDeviation = finalDeviation;
    }

    public Double getOptimizationTime() {
        return optimizationTime;
    }

    public void setOptimizationTime(Double optimizationTime) {
        this.optimizationTime = optimizationTime;
    }

    public List<TrajectoryDesignResult.TrajectoryPoint> getTrajectoryPoints() {
        return trajectoryPoints;
    }

    public void setTrajectoryPoints(List<TrajectoryDesignResult.TrajectoryPoint> trajectoryPoints) {
        this.trajectoryPoints = trajectoryPoints;
    }
}
