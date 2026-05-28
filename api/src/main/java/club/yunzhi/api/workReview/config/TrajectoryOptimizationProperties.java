package club.yunzhi.api.workReview.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.nio.file.Path;
import java.nio.file.Paths;

@Component
@ConfigurationProperties(prefix = "trajectory.optimization")
public class TrajectoryOptimizationProperties {

    /** Python 可执行文件，如 python、python3 或虚拟环境路径 */
    private String pythonExecutable = "python";

    /**
     * optimization 目录（含 run_ga_optigan_design_cli.py）。
     * 默认：api 模块上一级下的 ant-design-vue-pro-master/optimization
     */
    private String scriptDir = "../ant-design-vue-pro-master/optimization";

    /** GA-optiGAN 单次任务超时（秒），默认 2 小时 */
    private long gaOptiganTimeoutSeconds = 7200L;

    public String getPythonExecutable() {
        return pythonExecutable;
    }

    public void setPythonExecutable(String pythonExecutable) {
        this.pythonExecutable = pythonExecutable;
    }

    public String getScriptDir() {
        return scriptDir;
    }

    public void setScriptDir(String scriptDir) {
        this.scriptDir = scriptDir;
    }

    public long getGaOptiganTimeoutSeconds() {
        return gaOptiganTimeoutSeconds;
    }

    public void setGaOptiganTimeoutSeconds(long gaOptiganTimeoutSeconds) {
        this.gaOptiganTimeoutSeconds = gaOptiganTimeoutSeconds;
    }

    public Path resolveScriptDir() {
        Path p = Paths.get(scriptDir);
        if (p.isAbsolute()) {
            return p.normalize();
        }
        return Paths.get(System.getProperty("user.dir")).resolve(p).normalize();
    }

    public Path resolveCliScript() {
        return resolveScriptDir().resolve("run_ga_optigan_design_cli.py");
    }
}
