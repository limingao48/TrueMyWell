package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryFile;
import club.yunzhi.api.workReview.repository.TrajectoryFileRepository;
import club.yunzhi.api.workReview.repository.sepcs.TrajectoryFileSpecs;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.PostConstruct;
import javax.persistence.EntityManager;
import javax.persistence.EntityNotFoundException;
import javax.persistence.PersistenceContext;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;

/**
 * 井服务实现
 */
@Service
public class TrajectoryFilempl implements TrajectoryFileService {
    @PersistenceContext
    private EntityManager entityManager;


    @Value("${trajectory.file.storage.dir:/ant-design-vue-pro-master/public/trajectory}")
    private String storageDir;
    private final TrajectoryFileRepository trajectoryFileRepository;

    public TrajectoryFilempl(TrajectoryFileRepository trajectoryFileRepository) {
        this.trajectoryFileRepository = trajectoryFileRepository;
    }

    @PostConstruct
    public void initStorageDir() throws IOException {
        Path path = Paths.get(storageDir);
        if (!Files.exists(path)) {
            Files.createDirectories(path);
        }
    }

    @Override
    public List<TrajectoryFile> getAll() {
        return (List<TrajectoryFile>) trajectoryFileRepository.findAll();
    }

    @Override
    public Long getAllNumber() {
        return trajectoryFileRepository.count();
    }

    @Override
    public TrajectoryFile getById(String trajectoryFileId) {
        try {
            Long id = Long.parseLong(trajectoryFileId);
            return trajectoryFileRepository.findById(id)
                    .orElseThrow(() -> new EntityNotFoundException("井轨迹文件不存在"));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("无效的井轨迹文件ID");
        }
    }

    @Override
    public Page<TrajectoryFile> page(String trajectoryFileId, Pageable pageable) {
        return trajectoryFileRepository.findAll(TrajectoryFileSpecs.equalTrajectoryFileIdId(trajectoryFileId), pageable);
    }

    @Override
    public String add(TrajectoryFile trajectoryFile) {
        trajectoryFileRepository.save(trajectoryFile);
        return "添加成功";
    }

    @Override
    public String update(TrajectoryFile trajectoryFile) {
        if (trajectoryFile.getId() == null) {
            throw new IllegalArgumentException("井轨迹文件ID不能为空");
        }
        if (!trajectoryFileRepository.existsById(trajectoryFile.getId())) {
            throw new EntityNotFoundException("井轨迹文件不存在");
        }
        trajectoryFileRepository.save(trajectoryFile);
        return "更新成功";
    }

    @Override
    public String delete(Long id) {
        if (!trajectoryFileRepository.existsById(id)) {
            throw new EntityNotFoundException("井轨迹文件不存在");
        }
        trajectoryFileRepository.deleteById(id);
        return "删除成功";
    }

    @Override
    public TrajectoryFile upload(MultipartFile file, String wellNo) {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("上传的文件不能为空");
        }
        String originalFilename = file.getOriginalFilename();
        String fileExtension = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            fileExtension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        // 生成唯一文件名，避免重名覆盖
        String storedFileName = fileExtension;
        Path targetPath = Paths.get(storageDir, storedFileName);
        try {
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new RuntimeException("保存文件失败: " + e.getMessage(), e);
        }
        // 构建实体
        TrajectoryFile trajectoryFile = new TrajectoryFile();
        trajectoryFile.setFileName(originalFilename);
        trajectoryFile.setFileSize(file.getSize());
        trajectoryFile.setFileType(file.getContentType());
        trajectoryFile.setWellNo(wellNo); // 可为空
        trajectoryFile.setCreateTime(Timestamp.from(Instant.now()));
        trajectoryFile.setDeleted(false);
        return trajectoryFileRepository.save(trajectoryFile);
    }

    public String linkWell(Long id, String wellNo) {
        TrajectoryFile file = trajectoryFileRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("井轨迹文件不存在"));
        file.setWellNo(wellNo);
        trajectoryFileRepository.save(file);
        return "关联成功";
    }

    @Override
    public byte[] getLatestFileContentByWellNo(String wellNo) {
        if (wellNo == null || wellNo.trim().isEmpty()) {
            throw new IllegalArgumentException("wellNo不能为空");
        }
        TrajectoryFile trajectoryFile = trajectoryFileRepository.findFirstByWellNoOrderByIdDesc(wellNo.trim())
                .orElseThrow(() -> new EntityNotFoundException("未找到该井的轨迹文件"));
        byte[] fileContent = trajectoryFile.getFileContent();
        if (fileContent == null || fileContent.length == 0) {
            throw new EntityNotFoundException("该井轨迹文件内容为空");
        }
        return fileContent;
    }

    @Override
    public TrajectoryFile addWellWithFile(String wellNo, String wellName, MultipartFile file) {
        try {
            TrajectoryFile trajectoryFile = new TrajectoryFile();
            trajectoryFile.setWellNo(wellNo);
            trajectoryFile.setWellName(wellName == null || wellName.isEmpty() ? wellNo : wellName);
            trajectoryFile.setFileName(file.getOriginalFilename());
            trajectoryFile.setFileSize(file.getSize());
            trajectoryFile.setFileType(file.getContentType());

            trajectoryFile.setFileContent(file.getBytes()); // 核心：存储文件二进制到数据库
            // 持久化到MySQL
            entityManager.persist(trajectoryFile);
            return trajectoryFile;
        } catch (Exception e) {
            throw new RuntimeException("新增井并保存轨迹文件失败：" + e.getMessage(), e);
        }


    }
}