package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Lob;

/**
 * 待钻井：须归属井场（siteId），保存轨迹设计结果（七段式参数、井口、靶点）及关联轨迹 Excel。
 */
@Entity
public class PendingDrillWell extends BaseEntity {

    /** 所属井场 ID（与基础数据井场一致，必填） */
    private Long siteId;

    /** 待钻井名称/备注 */
    private String name;

    private Double wellheadE;
    private Double wellheadN;
    private Double wellheadD;

    private Double targetE;
    private Double targetN;
    private Double targetD;

    /** 七段式 12 参数字典的 JSON 字符串 */
    @Column(columnDefinition = "TEXT")
    private String sevenSegmentParamsJson;

    private Double finalDeviation;
    private Double optimizationTime;

    /** 井斜数据表文件名（xlsx，工作表名为「井斜数据表」） */
    private String trajectoryFileName;

    @Lob
    @JsonIgnore
    private byte[] trajectoryFileContent;

    private Long trajectoryFileSize;

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

    public String getSevenSegmentParamsJson() {
        return sevenSegmentParamsJson;
    }

    public void setSevenSegmentParamsJson(String sevenSegmentParamsJson) {
        this.sevenSegmentParamsJson = sevenSegmentParamsJson;
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

    public String getTrajectoryFileName() {
        return trajectoryFileName;
    }

    public void setTrajectoryFileName(String trajectoryFileName) {
        this.trajectoryFileName = trajectoryFileName;
    }

    @JsonIgnore
    public byte[] getTrajectoryFileContent() {
        return trajectoryFileContent;
    }

    public void setTrajectoryFileContent(byte[] trajectoryFileContent) {
        this.trajectoryFileContent = trajectoryFileContent;
    }

    public Long getTrajectoryFileSize() {
        return trajectoryFileSize;
    }

    public void setTrajectoryFileSize(Long trajectoryFileSize) {
        this.trajectoryFileSize = trajectoryFileSize;
    }

    /** 列表/详情 JSON 中是否已关联 Excel（不含二进制） */
    public boolean isHasTrajectoryExcel() {
        return trajectoryFileName != null && !trajectoryFileName.isEmpty()
                && trajectoryFileContent != null && trajectoryFileContent.length > 0;
    }
}
