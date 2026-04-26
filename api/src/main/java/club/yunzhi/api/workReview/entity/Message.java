package club.yunzhi.api.workReview.entity;

import org.hibernate.annotations.CreationTimestamp;

import java.sql.Timestamp;
import java.util.List;

// websocket传递给前端的信息实体
public class Message {
    @CreationTimestamp
    private Timestamp createTime;
    private List<Long> taskIds;

    private List<TaskIdAndModelId> taskIdAndModelId;

    public List<TaskIdAndModelId> getTaskIdAndModelId() {
        return taskIdAndModelId;
    }

    public void setTaskIdAndModelId(List<TaskIdAndModelId> taskIdAndModelId) {
        this.taskIdAndModelId = taskIdAndModelId;
    }

    public Timestamp getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Timestamp createTime) {
        this.createTime = createTime;
    }

    public List<Long> getTaskIds() {
        return taskIds;
    }

    public void setTaskIds(List<Long> taskIds) {
        this.taskIds = taskIds;
    }

    public static class TaskIdAndModelId {
        public Long taskId;
        public List<Long> ModelIds;
    }
}

