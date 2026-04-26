package club.yunzhi.api.workReview.entity;

import javax.persistence.Entity;
import javax.persistence.Lob;

@Entity
public class TrajectoryFile extends BaseEntity {
    /**
     * 井No
     */
    private String wellNo;

    /**
     * 井名称
     */
    private String wellName;

    /**
     * 轨迹文件名
     */
    private String fileName;



    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 文件二进制内容
     */
    @Lob

    private byte[] fileContent;

    public String getWellNo() {
        return wellNo;
    }

    public void setWellNo(String wellNo) {
        this.wellNo = wellNo;
    }

    public String getWellName() {
        return wellName;
    }

    public void setWellName(String wellName) {
        this.wellName = wellName;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }


    public Long getFileSize() {
        return fileSize;
    }

    public void setFileSize(Long fileSize) {
        this.fileSize = fileSize;
    }

    public String getFileType() {
        return fileType;
    }

    public void setFileType(String fileType) {
        this.fileType = fileType;
    }

    public byte[] getFileContent() {
        return fileContent;
    }

    public void setFileContent(byte[] fileContent) {
        this.fileContent = fileContent;
    }
}

