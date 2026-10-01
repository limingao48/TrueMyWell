package club.yunzhi.api.workReview.entity;

import java.util.List;

public class WhileDrillingSessionStartRequest {
    private Long siteId;
    private Long pendingWellId;

    public Long getSiteId() {
        return siteId;
    }

    public void setSiteId(Long siteId) {
        this.siteId = siteId;
    }

    public Long getPendingWellId() {
        return pendingWellId;
    }

    public void setPendingWellId(Long pendingWellId) {
        this.pendingWellId = pendingWellId;
    }
}
