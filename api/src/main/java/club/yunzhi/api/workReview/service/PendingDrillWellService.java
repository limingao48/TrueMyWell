package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.dto.PendingDrillWellSaveDto;
import club.yunzhi.api.workReview.entity.PendingDrillWell;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface PendingDrillWellService {

    PendingDrillWell save(PendingDrillWellSaveDto dto);

    List<PendingDrillWell> getAll();

    /** 某井场下的待钻井（按 id 倒序） */
    List<PendingDrillWell> getBySiteId(Long siteId);

    PendingDrillWell getById(Long id);

    void delete(Long id);

    void attachTrajectoryExcel(Long id, MultipartFile file);

    byte[] getTrajectoryExcelContent(Long id);

    String getTrajectoryExcelFileName(Long id);
}
