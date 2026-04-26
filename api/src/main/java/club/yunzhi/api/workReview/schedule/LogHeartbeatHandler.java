package club.yunzhi.api.workReview.schedule;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 日志心跳服务
 * @author xiaoqiang
 */
@Component
public class LogHeartbeatHandler {
  private final Logger logger = LoggerFactory.getLogger(this.getClass());

  /**
   * 日志心跳服务，每2分钟触发一次，暂时未找到"每2分30执行一次"秒写法
   */
//  @Scheduled(cron = "0 */1 * * * *")
  public void logHeartbeat() {
    logger.info("");
  }
}
