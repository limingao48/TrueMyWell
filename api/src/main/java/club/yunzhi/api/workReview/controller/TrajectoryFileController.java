package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.TrajectoryFile;
import club.yunzhi.api.workReview.service.TrajectoryFileService;
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 井管理
 */
@RestController
@RequestMapping("trajectoryFile")
public class TrajectoryFileController {

  private TrajectoryFileService trajectoryFileService;
  public TrajectoryFileController(TrajectoryFileService trajectoryFileService) {
    this.trajectoryFileService = trajectoryFileService;
  }
  /**
   * 新增井并关联轨迹文件（文件存储到MySQL）
   * @param wellNo 井号
   * @param wellName 井名称
   * @param file 轨迹Excel文件
   * @return 保存后的TrajectoryFile
   */
  @PostMapping("addWellWithFile")
  @JsonView(PageJsonView.class)
  public TrajectoryFile addWellWithFile(
          @RequestParam String wellNo,
          @RequestParam(required = false) String wellName,
          @RequestParam("file") MultipartFile file) {
    return this.trajectoryFileService.addWellWithFile(wellNo, wellName, file);
  }



  @GetMapping("getAll")
  @JsonView(GetAllJsonView.class)
  public List<TrajectoryFile> getAll() {
    List<TrajectoryFile> trajectoryFiles = this.trajectoryFileService.getAll();
    return trajectoryFiles;
  }

  @GetMapping("getAllNumber")
  public long getAllNumber() {
    return this.trajectoryFileService.getAllNumber();
  }

  @GetMapping("page")
  @JsonView(PageJsonView.class)
  public Page<TrajectoryFile> page(@RequestParam(required = false) String trajectoryFileId,
                         @SortDefault(sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
    return this.trajectoryFileService.page(trajectoryFileId, pageable);
  }

  @GetMapping("getById")
  @JsonView(PageJsonView.class)
  public TrajectoryFile getById(@RequestParam(required = false) String trajectoryFileId) {
    return this.trajectoryFileService.getById(trajectoryFileId);
  }

  @PostMapping("add")
  @JsonView(PageJsonView.class)
  public String add(@RequestBody TrajectoryFile trajectoryFile) {
    return this.trajectoryFileService.add(trajectoryFile);
  }

  /**
   * 上传轨迹文件（同时保存记录到数据库）
   * @param file 上传的文件
   * @param wellNo 关联井号（可选）
   * @return 保存后的 TrajectoryFile 对象
   */
  @PostMapping("upload")
  @JsonView(PageJsonView.class)
  public TrajectoryFile upload(@RequestParam("file") MultipartFile file,
                               @RequestParam(value = "wellNo", required = false) String wellNo) {
    return this.trajectoryFileService.upload(file, wellNo);
  }

  @PutMapping("update")
  @JsonView(PageJsonView.class)
  public String update(@RequestBody TrajectoryFile trajectoryFile) {
    return this.trajectoryFileService.update(trajectoryFile);
  }

  /**
   * 仅更新轨迹文件的关联井号
   * @param id 轨迹文件ID
   * @param wellNo 井号（可为空，表示解除关联）
   * @return 操作结果
   */
  @PutMapping("linkWell")
  public String linkWell(@RequestParam Long id, @RequestParam(required = false) String wellNo) {
    return this.trajectoryFileService.linkWell(id, wellNo);
  }

  @DeleteMapping("delete")
  public String delete(@RequestParam Long id) {
    return this.trajectoryFileService.delete(id);
  }

  public interface GetAllJsonView {}
  public interface PageJsonView {}
}
