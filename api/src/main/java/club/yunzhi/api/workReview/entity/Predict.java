package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonView;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import javax.persistence.*;

@Entity
@SQLDelete(sql = "update `predict` set deleted = 1 where id = ?")
@Where(clause = "deleted = false")
public class Predict extends BaseEntity implements Comparable<Predict>{

    private float distance;
    @ManyToOne
    @JoinColumn(nullable = false)
    @JsonView(FeatherJsonView.class)
    private Feather feather;
    @ManyToOne
    @JoinColumn(nullable = false)
    @JsonView(TaskJsonView.class)
    private Task task;
    @OneToOne
    @JoinColumn(nullable = false)
    @JsonView(ModelJsonView.class)
    private Model model;

    public float getDistance() {
        return distance;
    }

    public void setDistance(float distance) {
        this.distance = distance;
    }

    public Feather getFeather() {
        return feather;
    }

    public void setFeather(Feather feather) {
        this.feather = feather;
    }

    public Task getTask() {
        return task;
    }

    public void setTask(Task task) {
        this.task = task;
    }

    public Model getModel() {
        return model;
    }

    public void setModel(Model model) {
        this.model = model;
    }

    @Override
    public int compareTo(Predict o) {
        return Float.compare(this.getFeather().getDepth(), o.getFeather().getDepth());
    }

    public interface TaskJsonView {
    }

    public interface ModelJsonView {
    }

    public interface FeatherJsonView {
    }

}
