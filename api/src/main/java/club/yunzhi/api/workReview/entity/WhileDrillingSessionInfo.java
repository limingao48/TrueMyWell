package club.yunzhi.api.workReview.entity;

public class WhileDrillingSessionInfo {
    private String sessionId;
    private Long siteId;
    private Long pendingWellId;
    private String wellName;
    private Integer tcpPort;
    private String wsPath;
    private String restPositionUrl;
    private Double alertDistanceM;
    private Boolean active;

    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public Long getSiteId() { return siteId; }
    public void setSiteId(Long siteId) { this.siteId = siteId; }
    public Long getPendingWellId() { return pendingWellId; }
    public void setPendingWellId(Long pendingWellId) { this.pendingWellId = pendingWellId; }
    public String getWellName() { return wellName; }
    public void setWellName(String wellName) { this.wellName = wellName; }
    public Integer getTcpPort() { return tcpPort; }
    public void setTcpPort(Integer tcpPort) { this.tcpPort = tcpPort; }
    public String getWsPath() { return wsPath; }
    public void setWsPath(String wsPath) { this.wsPath = wsPath; }
    public String getRestPositionUrl() { return restPositionUrl; }
    public void setRestPositionUrl(String restPositionUrl) { this.restPositionUrl = restPositionUrl; }
    public Double getAlertDistanceM() { return alertDistanceM; }
    public void setAlertDistanceM(Double alertDistanceM) { this.alertDistanceM = alertDistanceM; }
    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }
}
