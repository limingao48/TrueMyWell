package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.annotation.OwnerKey;
import club.yunzhi.api.workReview.annotation.OwnerSecured;
import club.yunzhi.api.workReview.entity.BarData;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.security.YunzhiSecurityRole;
import club.yunzhi.api.workReview.service.TaskService;
import com.fasterxml.jackson.annotation.JsonView;
import com.mengyunzhi.core.exception.AccessDeniedException;
import com.mengyunzhi.core.exception.ValidationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.security.access.annotation.Secured;
import org.springframework.util.Assert;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import static java.util.Date.parse;

/**
 * 任务管理
 */
@RestController
@RequestMapping("task")
public class TaskController {

  private  TaskService taskService;
  public TaskController(TaskService taskService) {
    this.taskService = taskService;
  }

  @GetMapping("page")
  @JsonView(PageJsonView.class)
  public Page<Task> page(@RequestParam(required = false) String taskName,
                         @RequestParam(required = false) String wellId,
                         @RequestParam(required = false) ArrayList<Long> models,
                         @RequestParam(required = false) Integer status,
                         @RequestParam(required = false) String startDate,
                         @RequestParam(required = false) String endDate,
                         @SortDefault(sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
//    System.out.println(models);
    return this.taskService.page(taskName, wellId, models, status, startDate, endDate, pageable);
  }

  @GetMapping("getMonthTaskNumber")
  public List<BarData> getMonthTaskNumber(){
    return this.taskService.getMonthTaskNumber();
  }

  @GetMapping("getAllTask")
  @JsonView(PageJsonView.class)
  public List<Task> getAllTasksByWellId(@RequestParam(required = false) String wellId){
    return this.taskService.getTasksByWell(wellId);
  }

  @GetMapping("getFinishedTaskNumberByWellId{wellId}")
  @JsonView(PageJsonView.class)
  public Integer getFinishedTaskNumberByWellId(@PathVariable Long wellId){
    return this.taskService.getTaskNumberByWellIdAndStatus(wellId, Task.STATUS_FREEZE);
  }

  @GetMapping("getUnfinishedTaskNumberByWellId{wellId}")
  @JsonView(PageJsonView.class)
  public Integer getUnfinishedTaskNumberByWellId(@PathVariable Long wellId){
    return this.taskService.getTaskNumberByWellIdAndStatus(wellId, Task.STATUS_RUNNING);
  }

  @GetMapping("delete/{id}")
  @JsonView(PageJsonView.class)
  public void edit(@PathVariable Long id) {
    this.taskService.delete(id);
  }


  @PostMapping
  @JsonView(PageJsonView.class)
  public Task add(@RequestBody Task task) {
    return this.taskService.add(task);
  }

  @PostMapping("edit/{id}")
  @JsonView(PageJsonView.class)
  public Task edit(@PathVariable Long id, @RequestBody Task task) {
    return this.taskService.edit(id, task);
  }

  @GetMapping("run/{id}")
  @JsonView(PageJsonView.class)
  public Task run(@PathVariable Long id) {
    return this.taskService.run(id);
  }

  @GetMapping("freeze/{id}")
  @JsonView(PageJsonView.class)
  public Task freeze(@PathVariable Long id) {
    return this.taskService.freeze(id);
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

  public interface PageJsonView extends Task.WellJsonView, Task.ModelJsonView {}

}
