package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonView;
import com.mengyunzhi.core.annotation.query.In;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.*;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;

/**
 * 老师实体.
 */
@Entity
@SQLDelete(sql = "update `task` set deleted = 1 where id = ?")
@Where(clause = "deleted = false")
public class Task extends BaseEntity {
    /**
     * 冻结中.
     */
    public static Integer STATUS_FREEZE = 0;
    /**
     * 运行中.
     */
    public static Integer STATUS_RUNNING = 1;
    public static final String TABLE_NAME = "task";

    private String name;

    /**
     * 状态.
     * 0: 冻结
     * 1: 启动中
     */
    private Integer status = STATUS_RUNNING;

    @ManyToOne
    @JoinColumn(nullable = false)
    @JsonView(WellJsonView.class)
    private Well well;

    private Timestamp updateTime;

    private Integer predictNumber;

    @OneToMany(mappedBy = "task")
    @JsonView(PredictsJsonView.class)
    private List<Predict> predicts = new ArrayList<>();


    public List<Predict> getPredicts() {
        return predicts;
    }

    public void setPredicts(List<Predict> predicts) {
        this.predicts = predicts;
    }

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinColumn(nullable = false)
    @JoinTable(name = Model.TABLE_NAME + "_" + Task.TABLE_NAME,
            joinColumns = @JoinColumn(name = Task.TABLE_NAME + "_id"),
            inverseJoinColumns = @JoinColumn(name = Model.TABLE_NAME + "_id"))
    @JsonView(ModelJsonView.class)
    private List<Model> models = new ArrayList<>();

    public Well getWell() {
        return well;
    }

    public void setWell(Well well) {
        this.well = well;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<Model> getModels() {
        return models;
    }

    public void setModels(List<Model> models) {
        this.models = models;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }

    public Timestamp getUpdateTime() {
        return updateTime;
    }

    public void setUpdateTime(Timestamp updateTime) {
        this.updateTime = updateTime;
    }

    public Integer getPredictNumber() {
        return predictNumber;
    }

    public void setPredictNumber(Integer predictNumber) {
        this.predictNumber = predictNumber;
    }

    public interface WellJsonView {
    }
    public interface ModelJsonView {
    }
    public interface TaskJsonView {}

    public interface PredictsJsonView {}
}
