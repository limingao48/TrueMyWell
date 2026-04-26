package club.yunzhi.api.workReview.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

@Configuration
@EnableWebMvc
public class WebMvcConfig implements WebMvcConfigurer {
  /**
   * 静态配置，用于非spring管理的BEAN获取该配置项。注意：spring未启动前，该值为null
   * 适用场景：某此BEAN的代码在spring成功启动以前便执行了
   * 示例代码：LoggerMonitorFilter
   */
  public static AppMonitorConfig appMonitorConfig;

  public static String active;

  /**
   * 配置JsonView.
   *
   * @param converters 转换器
   */
  @Override
  public void configureMessageConverters(final List<HttpMessageConverter<?>> converters) {
    final ObjectMapper mapper = Jackson2ObjectMapperBuilder.json().defaultViewInclusion(true)
        .build();
    converters.add(new MappingJackson2HttpMessageConverter(mapper));
  }

  @Autowired
  public WebMvcConfig(AppMonitorConfig appMonitorConfig) {
    WebMvcConfig.appMonitorConfig = appMonitorConfig;
  }


  @Value("${spring.profiles.active}")
  public void setActive(String active) {
    WebMvcConfig.active = active;
  }
}