package club.yunzhi.api.workReview.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "while-drilling")
public class WhileDrillingProperties {

    /** TCP 监听端口，接收实时钻进坐标 */
    private int tcpPort = 9010;

    /** 水平偏移告警阈值(m) */
    private double alertDistanceM = 30.0;

    /** 蒙特卡洛抽样次数 */
    private int monteCarloSamples = 100;

    /** 蒙特卡洛综合概率达到该值(%)时建议停钻 */
    private double monteCarloStopProbabilityThreshold = 70.0;

    /** 蒙特卡洛综合偏差判定：外推下一步水平偏移需超过该值(m) */
    private double monteCarloComprehensiveThresholdM = 35.0;

    /** ISCWSA MWD 测深 1σ (m) */
    private double iscwsaSigmaMd = 0.6;

    /** ISCWSA MWD 井斜 1σ (°) */
    private double iscwsaSigmaIncDeg = 0.2;

    /** ISCWSA MWD 方位 1σ (°) */
    private double iscwsaSigmaAziDeg = 0.3;

    public int getTcpPort() {
        return tcpPort;
    }

    public void setTcpPort(int tcpPort) {
        this.tcpPort = tcpPort;
    }

    public double getAlertDistanceM() {
        return alertDistanceM;
    }

    public void setAlertDistanceM(double alertDistanceM) {
        this.alertDistanceM = alertDistanceM;
    }

    public int getMonteCarloSamples() {
        return monteCarloSamples;
    }

    public void setMonteCarloSamples(int monteCarloSamples) {
        this.monteCarloSamples = monteCarloSamples;
    }

    public double getMonteCarloStopProbabilityThreshold() {
        return monteCarloStopProbabilityThreshold;
    }

    public void setMonteCarloStopProbabilityThreshold(double monteCarloStopProbabilityThreshold) {
        this.monteCarloStopProbabilityThreshold = monteCarloStopProbabilityThreshold;
    }

    public double getMonteCarloComprehensiveThresholdM() {
        return monteCarloComprehensiveThresholdM;
    }

    public void setMonteCarloComprehensiveThresholdM(double monteCarloComprehensiveThresholdM) {
        this.monteCarloComprehensiveThresholdM = monteCarloComprehensiveThresholdM;
    }

    public double getIscwsaSigmaMd() {
        return iscwsaSigmaMd;
    }

    public void setIscwsaSigmaMd(double iscwsaSigmaMd) {
        this.iscwsaSigmaMd = iscwsaSigmaMd;
    }

    public double getIscwsaSigmaIncDeg() {
        return iscwsaSigmaIncDeg;
    }

    public void setIscwsaSigmaIncDeg(double iscwsaSigmaIncDeg) {
        this.iscwsaSigmaIncDeg = iscwsaSigmaIncDeg;
    }

    public double getIscwsaSigmaAziDeg() {
        return iscwsaSigmaAziDeg;
    }

    public void setIscwsaSigmaAziDeg(double iscwsaSigmaAziDeg) {
        this.iscwsaSigmaAziDeg = iscwsaSigmaAziDeg;
    }
}
