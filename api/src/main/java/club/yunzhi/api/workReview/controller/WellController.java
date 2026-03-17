package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.service.TaskService;
import club.yunzhi.api.workReview.service.WellService;
import com.fasterxml.jackson.annotation.JsonView;
import com.mengyunzhi.core.annotation.query.In;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

/**
 * 任务管理
 */
@RestController
@RequestMapping("well")
public class WellController {

  private WellService wellService;
  private TaskService taskService;
  public WellController(WellService wellService,
                        TaskService taskService) {
    this.wellService = wellService;
    this.taskService = taskService;
  }

  @GetMapping("getAll")
  @JsonView(GetAllJsonView.class)
  public List<Well> getAll() {
    List<Well> wells = this.wellService.getAll();
    return wells;
  }

  @GetMapping("getAllNumber")
  public ArrayList<Long> getAllNumber() {
    ArrayList<Long> arrayList = new ArrayList<>();
    long wellsNumber = this.wellService.getAllNumber();
    long tasksNumber = this.taskService.getAllNumber();
    long monthTaskNumber = this.taskService.monthTaskNumber();
    long todayTaskNumber = this.taskService.todayTaskNumber();
//    Integer
    arrayList.add(wellsNumber);
    arrayList.add(tasksNumber);
    arrayList.add(monthTaskNumber);
    arrayList.add(todayTaskNumber);
    return arrayList;
  }

  @GetMapping("page")
  @JsonView(PageJsonView.class)
  public Page<Well> page(@RequestParam(required = false) String wellId,
                         @SortDefault(sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
    return this.wellService.page(wellId, pageable);
  }

  @GetMapping("getById")
  @JsonView(PageJsonView.class)
  public Well getById(@RequestParam(required = false) String wellId) {
    return this.wellService.getById(wellId);
  }

  @PostMapping("add")
  @JsonView(PageJsonView.class)
  public String add(@RequestBody Well well) {
    return this.wellService.add(well);
  }

//  /**
//   * 将状态设置为评阅中.
//   *
//   * @param id id
//   * @return
//   */
//  @PatchMapping("setStatusToReviewing/{id}")
//  @JsonView(SetStatusToReviewingJsonView.class)
//  @Secured(YunzhiSecurityRole.ROLE_TEACHER)
//  public Review setStatusToReviewing(@PathVariable Long id) {
//    return this.reviewService.setStatusToReviewing(id);
//  }

  public interface GetAllJsonView {}
  public interface PageJsonView {}
}
