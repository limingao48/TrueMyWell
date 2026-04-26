package club.yunzhi.api.workReview.entity;

import com.fasterxml.jackson.annotation.JsonView;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.OneToMany;
import java.util.ArrayList;
import java.util.List;

@Entity
@SQLDelete(sql = "update `model` set deleted = 1 where id = ?")
@Where(clause = "deleted = false")
public class Model extends BaseEntity {
    public static final String TABLE_NAME = "model";
    public static Integer ANN1 = 1;
    public static Integer ANN3 = 2;
    public static Integer ANN5 = 3;
    public static Integer RNN1 = 4;
    public static Integer RNN3 = 5;
    public static Integer RNN5 = 6;
    public static Integer SVR1 = 7;
    public static Integer SVR3 = 8;
    public static Integer SVR5 = 9;

    private long type;
    private String name;

//    @OneToMany(mappedBy = "model")
//    @JsonView(TaskJsonView.class)
//    private List<Predict> predicts = new ArrayList<>();

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public long getType() {
        return type;
    }

    public void setType(long type) {
        this.type = type;
    }

    public interface TaskJsonView {}
}
