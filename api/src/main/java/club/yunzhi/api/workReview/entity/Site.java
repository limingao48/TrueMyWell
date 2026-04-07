package club.yunzhi.api.workReview.entity;

import javax.persistence.Entity;

/**
 * 井场实体
 */
@Entity
public class Site extends BaseEntity {
    /**
     * 井场名称
     */
    private String name;

    /**
     * 井场编号
     */
    private String code;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }
}
