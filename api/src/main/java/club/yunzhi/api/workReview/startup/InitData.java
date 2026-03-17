package club.yunzhi.api.workReview.startup;

import club.yunzhi.api.workReview.entity.Model;
import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.ModelRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.core.Ordered;
import org.springframework.stereotype.Component;

/**
 * 系统数据初始化.
 */
@Component
public class InitData implements ApplicationListener<ContextRefreshedEvent>, Ordered {
  public final static int order = 0;

  private static final Logger logger = LoggerFactory.getLogger(InitData.class);

  private final ModelRepository modelRepository;
  private final WellRepository wellRepository;


  public InitData(ModelRepository modelRepository, WellRepository wellRepository) {
    this.modelRepository = modelRepository;
    this.wellRepository = wellRepository;
  }

  @Override
  public void onApplicationEvent(ContextRefreshedEvent event) {
    String version = "1.0.0";
    if (this.modelRepository.count() == 0) {
      // 新增ann模型
      Model Ann1 = new Model();
      Ann1.setName("人工神经网络(1井)");
      Ann1.setType(Model.ANN1);
      this.modelRepository.save(Ann1);

      Model Ann3 = new Model();
      Ann3.setName("人工神经网络(3井)");
      Ann3.setType(Model.ANN3);
      this.modelRepository.save(Ann3);

      Model Ann5 = new Model();
      Ann5.setName("人工神经网络(5井)");
      Ann5.setType(Model.ANN5);
      this.modelRepository.save(Ann5);

      // 新增SVR模型
      Model Svr1 = new Model();
      Svr1.setName("支持向量回归(1井)");
      Svr1.setType(Model.SVR1);
      this.modelRepository.save(Svr1);

      Model Svr3 = new Model();
      Svr3.setName("支持向量回归(3井)");
      Svr3.setType(Model.SVR3);
      this.modelRepository.save(Svr3);

      Model Svr5 = new Model();
      Svr5.setName("支持向量回归(5井)");
      Svr5.setType(Model.SVR5);
      this.modelRepository.save(Svr5);

      // 新增RNN模型
      Model Rnn1 = new Model();
      Rnn1.setName("循环神经网络(1井)");
      Rnn1.setType(Model.RNN1);
      this.modelRepository.save(Rnn1);

      Model Rnn3 = new Model();
      Rnn3.setName("循环神经网络(3井)");
      Rnn3.setType(Model.RNN3);
      this.modelRepository.save(Rnn3);

      Model Rnn5 = new Model();
      Rnn5.setName("循环神经网络(5井)");
      Rnn5.setType(Model.RNN5);
      this.modelRepository.save(Rnn5);
    }
    if (this.wellRepository.count() == 0) {
      Well well1 = new Well();
      well1.setName("A1井");
      well1.setPredictNumber(0);
      well1.setPredictTotalNumber(0);
      well1.setTaskNumber(0);
      well1.setTodayPredictNumber(0);
      well1.setWeekPredictNumber(0);
      well1.setUniqueKey("1");
      this.wellRepository.save(well1);
    }
  }

  @Override
  public int getOrder() {
    return order;
  }
}
