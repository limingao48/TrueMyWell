package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.service.WellService;
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 井管理
 */
@RestController
@RequestMapping("well")
public class WellController {

  private WellService wellService;
  public WellController(WellService wellService) {
    this.wellService = wellService;
  }

  @GetMapping("getAll")
  @JsonView(GetAllJsonView.class)
  public List<Well> getAll() {
    List<Well> wells = this.wellService.getAll();
    return wells;
  }

  @GetMapping("getAllNumber")
  public long getAllNumber() {
    return this.wellService.getAllNumber();
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

  @PutMapping("update")
  @JsonView(PageJsonView.class)
  public String update(@RequestBody Well well) {
    return this.wellService.update(well);
  }

  @DeleteMapping("delete")
  public String delete(@RequestParam Long id) {
    return this.wellService.delete(id);
  }

  public interface GetAllJsonView {}
  public interface PageJsonView {}
}
