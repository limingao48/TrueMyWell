package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.Site;
import club.yunzhi.api.workReview.service.SiteService;
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 井场管理
 */
@RestController
@RequestMapping("site")
public class SiteController {

  private SiteService siteService;
  public SiteController(SiteService siteService) {
    this.siteService = siteService;
  }

  @GetMapping("getAll")
  @JsonView(GetAllJsonView.class)
  public List<Site> getAll() {
    return siteService.getAll();
  }

  @GetMapping("page")
  @JsonView(PageJsonView.class)
  public Page<Site> page(@RequestParam(required = false) String siteId,
                         @SortDefault(sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
    return siteService.page(siteId, pageable);
  }

  @GetMapping("getById")
  @JsonView(PageJsonView.class)
  public Site getById(@RequestParam(required = false) String siteId) {
    return siteService.getById(siteId);
  }

  @PostMapping("add")
  @JsonView(PageJsonView.class)
  public String add(@RequestBody Site site) {
    return siteService.add(site);
  }

  @PutMapping("update")
  @JsonView(PageJsonView.class)
  public String update(@RequestBody Site site) {
    return siteService.update(site);
  }

  @DeleteMapping("delete")
  public String delete(@RequestParam Long id) {
    return siteService.delete(id);
  }

  public interface GetAllJsonView {}
  public interface PageJsonView {}
}