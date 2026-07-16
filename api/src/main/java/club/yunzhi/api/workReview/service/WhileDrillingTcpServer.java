package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.WhileDrillingPositionRequest;
import club.yunzhi.api.workReview.properties.WhileDrillingProperties;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * TCP 端口监听：接收外部钻进设备推送的坐标 JSON。
 * 格式：{"sessionId":"xxx","x":1.0,"y":2.0,"z":3.0}
 */
@Component
public class WhileDrillingTcpServer {

    private static final Logger log = LoggerFactory.getLogger(WhileDrillingTcpServer.class);

    private final WhileDrillingProperties properties;
    private final WhileDrillingEvaluationService evaluationService;
    private final ExecutorService executor = Executors.newCachedThreadPool();
    private ServerSocket serverSocket;
    private volatile boolean running;

    public WhileDrillingTcpServer(WhileDrillingProperties properties,
                                  WhileDrillingEvaluationService evaluationService) {
        this.properties = properties;
        this.evaluationService = evaluationService;
    }

    @PostConstruct
    public void start() {
        int port = properties.getTcpPort();
        executor.submit(() -> {
            try {
                serverSocket = new ServerSocket(port);
                running = true;
                log.info("随钻评估 TCP 服务已启动，端口 {}", port);
                while (running) {
                    try {
                        Socket client = serverSocket.accept();
                        executor.submit(() -> handleClient(client));
                    } catch (IOException e) {
                        if (running) {
                            log.warn("TCP accept 异常: {}", e.getMessage());
                        }
                    }
                }
            } catch (IOException e) {
                log.error("随钻评估 TCP 服务启动失败，端口 {}: {}", port, e.getMessage());
            }
        });
    }

    @PreDestroy
    public void stop() {
        running = false;
        if (serverSocket != null && !serverSocket.isClosed()) {
            try {
                serverSocket.close();
            } catch (IOException ignored) {
            }
        }
        executor.shutdownNow();
    }

    private void handleClient(Socket client) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) {
                    continue;
                }
                processLine(line);
            }
        } catch (IOException e) {
            log.debug("TCP 客户端断开: {}", e.getMessage());
        } finally {
            try {
                client.close();
            } catch (IOException ignored) {
            }
        }
    }

    private void processLine(String line) {
        try {
            JSONObject json = JSON.parseObject(line);
            WhileDrillingPositionRequest req = new WhileDrillingPositionRequest();
            req.setSessionId(json.getString("sessionId"));
            req.setX(json.getDouble("x"));
            req.setY(json.getDouble("y"));
            req.setZ(json.getDouble("z"));
            evaluationService.submitPosition(req);
        } catch (Exception e) {
            log.warn("TCP 坐标解析/评估失败: {} | {}", line, e.getMessage());
        }
    }
}
