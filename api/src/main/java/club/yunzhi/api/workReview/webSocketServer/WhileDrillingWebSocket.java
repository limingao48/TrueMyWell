package club.yunzhi.api.workReview.webSocketServer;

import club.yunzhi.api.workReview.service.WhileDrillingWebSocketNotifier;
import cn.hutool.log.Log;
import cn.hutool.log.LogFactory;
import org.springframework.stereotype.Component;

import javax.websocket.*;
import javax.websocket.server.PathParam;
import javax.websocket.server.ServerEndpoint;

@ServerEndpoint("/whileDrilling/ws/{sessionId}")
@Component
public class WhileDrillingWebSocket {

    private static final Log log = LogFactory.get(WhileDrillingWebSocket.class);
    private String sessionId;

    @OnOpen
    public void onOpen(Session session, @PathParam("sessionId") String sessionId) {
        this.sessionId = sessionId;
        WhileDrillingWebSocketNotifier.register(sessionId, session);
        log.info("随钻评估 WebSocket 连接: {}", sessionId);
    }

    @OnClose
    public void onClose() {
        WhileDrillingWebSocketNotifier.unregister(sessionId);
        log.info("随钻评估 WebSocket 断开: {}", sessionId);
    }

    @OnError
    public void onError(Session session, Throwable error) {
        log.error("随钻评估 WebSocket 错误: {}", error.getMessage());
        WhileDrillingWebSocketNotifier.unregister(sessionId);
    }
}
