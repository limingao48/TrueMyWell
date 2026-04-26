package club.yunzhi.api.workReview.entity;

import javax.persistence.Entity;

/**
 * 任务实体
 */
@Entity
public class Task extends BaseEntity {
    /**
     * 任务名称
     */
    private String name;

    /**
     * 任务编号
     */
    private String code;

    /**
     * 任务描述
     */
    private String description;

    /**
     * 任务状态
     */
    private Integer status = 1;

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

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }
}
