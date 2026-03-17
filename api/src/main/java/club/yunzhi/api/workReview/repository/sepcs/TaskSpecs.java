package club.yunzhi.api.workReview.repository.sepcs;

import club.yunzhi.api.workReview.entity.Model;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.service.TaskService;
import com.mengyunzhi.core.annotation.query.In;
import org.springframework.data.jpa.domain.Specification;

import javax.persistence.criteria.*;
import java.util.ArrayList;
import java.util.Date;

import static antlr.build.ANTLR.root;

public class TaskSpecs {
  /**
   * 包含名字.
   *
   * @param name 名字
   * @return 谓语
   */
  public static Specification<Task> containingName(String name) {
    if (name != null) {
      return (root, criteriaQuery, criteriaBuilder) ->
          criteriaBuilder.like(root.get("name").as(String.class), String.format("%%%s%%", name));
    } else {
      return Specification.where(null);
    }
  }

  public static Specification<Task> idWellId(String wellId) {
    if (wellId == null) {
      return Specification.where(null);
    }
    return (root, criteriaQuery, criteriaBuilder)
            -> criteriaBuilder.equal(root.get("well").get("id").as(String.class), wellId);
  }

  public static Specification<Task> isModels(ArrayList<Long> modelsId) {
    if (modelsId == null) {
      return Specification.where(null);
    }
    return (root, criteriaQuery, criteriaBuilder) -> {
      Join<Task, Model> modelJoin = root.join("models");
      CriteriaBuilder.In<Long> in = criteriaBuilder.in(
        modelJoin.get("type").as(Long.class));
//              root.join("model_task").get("model_id").as(Long.class));
      for (Long model : modelsId) {
        in.value(model);
      }
      return in;
    };
  }

  public static Specification<Task> isStatus(Integer status) {
    if (status == null) {
      return Specification.where(null);
    }
    return (root, criteriaQuery, criteriaBuilder)
            -> criteriaBuilder.equal(root.get("status").as(String.class), status);
  }

  public static Specification<Task> timeBetween(String startDate, String endDate) {
    if (startDate == null) {
      return Specification.where(null);
    } else {
      Date startTime, endTime;
      String[] start = startDate.split("-");
      String[] end = endDate.split("-");
      startTime = TaskService.stringToDate(start);
      endTime = TaskService.stringToDate(end);
      return (root, criteriaQuery, criteriaBuilder)
              -> criteriaBuilder.between(root.get("updateTime"), startTime, endTime);
    }
  }

  public static Specification<Task> idRun() {
    return (root, criteriaQuery, criteriaBuilder)
            -> criteriaBuilder.equal(root.get("status").as(Integer.class), Task.STATUS_RUNNING);
  }
}
