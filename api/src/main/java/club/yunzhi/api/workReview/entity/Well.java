package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonView;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.List;

/**
 * 井实体.
 */
@Entity
@SQLDelete(sql = "update `well` set deleted = 1 where id = ?")
@Where(clause = "deleted = false")
@EntityListeners(AuditingEntityListener.class)
public class Well extends BaseEntity {
//
//    @OneToOne
//    @JsonView(UserJsonView.class)
//    private User user;

//    @ManyToOne
//    @JoinColumn(nullable = false)
//    @JsonView(ClazzJsonView.class)
//    private Clazz clazz;
    private String name;

    private String uniqueKey;

    @OneToMany(mappedBy = "well")
    @JsonView(TasksJsonView.class)
    private List<Task> tasks = new ArrayList<>();

    private Integer predictNumber;

    private Integer taskNumber;

    private Integer predictTotalNumber;

    private Integer weekPredictNumber;

    private Integer todayPredictNumber;

//    public Clazz getClazz() {
//        return clazz;
//    }
//
//    public void setClazz(Clazz clazz) {
//        this.clazz = clazz;
//    }

    public List<Task> getTasks() {
        return tasks;
    }

    public void setTasks(List<Task> tasks) {
        this.tasks = tasks;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Integer getPredictNumber() {
        return predictNumber;
    }

    public void setPredictNumber(Integer predictNumber) {
        this.predictNumber = predictNumber;
    }

    public Integer getTaskNumber() {
        return taskNumber;
    }

    public void setTaskNumber(Integer taskNumber) {
        this.taskNumber = taskNumber;
    }

    public Integer getPredictTotalNumber() {
        return predictTotalNumber;
    }

    public void setPredictTotalNumber(Integer predictTotalNumber) {
        this.predictTotalNumber = predictTotalNumber;
    }

    public Integer getWeekPredictNumber() {
        return weekPredictNumber;
    }

    public void setWeekPredictNumber(Integer weekPredictNumber) {
        this.weekPredictNumber = weekPredictNumber;
    }

    public Integer getTodayPredictNumber() {
        return todayPredictNumber;
    }

    public void setTodayPredictNumber(Integer todayPredictNumber) {
        this.todayPredictNumber = todayPredictNumber;
    }

    public String getUniqueKey() {
        return uniqueKey;
    }

    public void setUniqueKey(String uniqueKey) {
        this.uniqueKey = uniqueKey;
    }

    public interface UserJsonView {
    }

    public interface ClazzJsonView {
    }

    public interface TasksJsonView {
    }
}
