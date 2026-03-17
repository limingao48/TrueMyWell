package club.yunzhi.api.workReview.logger;

import ch.qos.logback.core.filter.AbstractMatcherFilter;
import ch.qos.logback.core.spi.FilterReply;
import club.yunzhi.api.workReview.config.WebMvcConfig;

/**
 * @author panjie
 * 日志过滤器
 */
public class LoggerConsoleFilter extends AbstractMatcherFilter {
  @Override
  public FilterReply decide(Object event) {
    String active = WebMvcConfig.active;

    // 机器人环境不输出任何日志
    if (active != null) {
      if (active.equals("ci")) {
        return FilterReply.DENY;
      }
    }
    return FilterReply.NEUTRAL;
  }
}
