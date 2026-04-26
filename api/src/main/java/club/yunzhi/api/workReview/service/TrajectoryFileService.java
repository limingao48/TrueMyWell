package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryFile;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;


public interface TrajectoryFileService {
    List<TrajectoryFile> getAll();

    Long getAllNumber();

    TrajectoryFile getById(String trajectoryFileId);

    Page<TrajectoryFile> page(String trajectoryFileId, Pageable pageable);

    String add(TrajectoryFile trajectoryFile);

    String update(TrajectoryFile trajectoryFile);
    @Transactional(rollbackFor = Exception.class)
    String delete(Long id);

    TrajectoryFile upload(MultipartFile file, String wellNo);

    String linkWell(Long id, String wellNo);

    byte[] getLatestFileContentByWellNo(String wellNo);

    @Transactional(rollbackFor = Exception.class)
    TrajectoryFile addWellWithFile(String wellNo, String wellName, MultipartFile file);
}
