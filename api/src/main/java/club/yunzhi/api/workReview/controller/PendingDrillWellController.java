package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.dto.PendingDrillWellSaveDto;
import club.yunzhi.api.workReview.entity.PendingDrillWell;
import club.yunzhi.api.workReview.service.PendingDrillWellService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 待钻井：保存设计结果、列表、关联轨迹 Excel。
 */
@RestController
@RequestMapping("pendingDrillWell")
public class PendingDrillWellController {

    private final PendingDrillWellService pendingDrillWellService;

    public PendingDrillWellController(PendingDrillWellService pendingDrillWellService) {
        this.pendingDrillWellService = pendingDrillWellService;
    }

    @PostMapping("save")
    public PendingDrillWell save(@RequestBody PendingDrillWellSaveDto dto) {
        return pendingDrillWellService.save(dto);
    }

    @GetMapping("getAll")
    public List<PendingDrillWell> getAll() {
        return pendingDrillWellService.getAll();
    }

    /** 按井场查询待钻井（基础数据 / 井管理） */
    @GetMapping("getBySiteId")
    public List<PendingDrillWell> getBySiteId(@RequestParam Long siteId) {
        if (siteId == null) {
            throw new IllegalArgumentException("siteId 不能为空");
        }
        return pendingDrillWellService.getBySiteId(siteId);
    }

    @GetMapping("getById")
    public PendingDrillWell getById(@RequestParam Long id) {
        return pendingDrillWellService.getById(id);
    }

    @DeleteMapping("delete")
    public void delete(@RequestParam Long id) {
        pendingDrillWellService.delete(id);
    }

    /**
     * 为已保存的待钻井上传/替换关联轨迹 Excel。
     */
    @PostMapping("uploadTrajectoryExcel")
    public void uploadTrajectoryExcel(@RequestParam Long id, @RequestParam("file") MultipartFile file) {
        pendingDrillWellService.attachTrajectoryExcel(id, file);
    }

    @GetMapping("downloadTrajectoryExcel")
    public ResponseEntity<byte[]> downloadTrajectoryExcel(@RequestParam Long id) {
        byte[] content = pendingDrillWellService.getTrajectoryExcelContent(id);
        String name = pendingDrillWellService.getTrajectoryExcelFileName(id);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + name.replace("\"", "") + "\"")
                .contentType(MediaType.parseMediaType(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
                .body(content);
    }
}
