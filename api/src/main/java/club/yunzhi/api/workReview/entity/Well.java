package club.yunzhi.api.workReview.entity;

import javax.persistence.Entity;

/**
 * 井实体
 */
@Entity
public class Well extends BaseEntity {
    /**
     * 井场ID
     */
    private Long siteId;

    /**
     * 井号
     */
    private String wellNo;

    /**
     * 井名
     */
    private String name;

    /**
     * 井口东坐标
     */
    private Double wellheadE;

    /**
     * 井口北坐标
     */
    private Double wellheadN;

    /**
     * 井口海拔
     */
    private Double wellheadD;

    /**
     * 井径
     */
    private Double wellDiameter;

    public Long getSiteId() {
        return siteId;
    }

    public void setSiteId(Long siteId) {
        this.siteId = siteId;
    }

    public String getWellNo() {
        return wellNo;
    }

    public void setWellNo(String wellNo) {
        this.wellNo = wellNo;
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

    public Double getWellDiameter() {
        return wellDiameter;
    }

    public void setWellDiameter(Double wellDiameter) {
        this.wellDiameter = wellDiameter;
    }
}
