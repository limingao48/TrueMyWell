package club.yunzhi.api.workReview.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * @author panjie
 * 日志监控
 */
@ConfigurationProperties(prefix = "app.monitor")
@Component
public class AppMonitorConfig {
    private boolean enable = false;
    private String url = "localhost";

    public String getUrl() {
        return this.url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public boolean isEnable() {
        return this.enable;
    }

    public void setEnable(boolean enable) {
        this.enable = enable;
    }
}
