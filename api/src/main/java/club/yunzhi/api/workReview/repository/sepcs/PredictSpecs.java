package club.yunzhi.api.workReview.repository.sepcs;
import club.yunzhi.api.workReview.entity.Model;
import club.yunzhi.api.workReview.entity.Predict;
import java.sql.Timestamp;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.domain.Sort;

import javax.persistence.criteria.CriteriaBuilder;
import javax.persistence.criteria.Join;
import java.util.ArrayList;

public class PredictSpecs {
    public static Specification<Predict> idWellId(String wellId) {
        if (wellId == null) {
            return Specification.where(null);
        }
        return (root, criteriaQuery, criteriaBuilder)
                -> criteriaBuilder.equal(root.get("feather").get("well").get("id").as(String.class), wellId);
    }

    public static Specification<Predict> taskIsSelectedStatus(Integer status) {
        if (status == null) {
            return Specification.where(null);
        }
        return (root, criteriaQuery, criteriaBuilder)
                -> criteriaBuilder.equal(root.get("task").get("status").as(Integer.class), status);
    }

    public static Specification<Predict> idTaskId(String taskId) {
        if (taskId == null) {
            return Specification.where(null);
        }
        return (root, criteriaQuery, criteriaBuilder)
                -> criteriaBuilder.equal(root.get("task").get("id").as(String.class), taskId);
    }

    public static Specification<Predict> isModels(ArrayList<Long> modelsId) {
        if (modelsId == null) {
            return Specification.where(null);
        }
        return (root, criteriaQuery, criteriaBuilder) -> {
            Join<Predict, Model> modelJoin = root.join("model");
            CriteriaBuilder.In<Long> in = criteriaBuilder.in(
                    modelJoin.get("type").as(Long.class));
            for (Long model : modelsId) {
                in.value(model);
            }
            return in;
        };
    }
    public static Specification<Predict> createTimeBetween(String startTime, String endTime) {
        return (root, query, criteriaBuilder) ->
                criteriaBuilder.between(root.get("createTime").as(Timestamp.class),
                        Timestamp.valueOf(startTime + ":00"), Timestamp.valueOf(endTime + ":00"));
    }

    public static Specification<Predict> createTimeBetweenUseTimeStamp(Timestamp startTime, Timestamp endTime) {
        return (root, query, criteriaBuilder) ->
                criteriaBuilder.between(root.get("createTime").as(Timestamp.class),
                        startTime, endTime);
    }

    public static Sort sortByCreateTimeDesc() {
        return Sort.by(Sort.Direction.DESC, "createTime");
    }


}
