package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.WhileDrillingEvaluationResult;
import com.alibaba.fastjson.JSON;

import javax.websocket.Session;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 随钻评估 WebSocket 推送：前端订阅 sessionId 接收实时评估结果。
 */
public final class WhileDrillingWebSocketNotifier {

    private static final Map<String, Session> SESSIONS = new ConcurrentHashMap<>();

    private WhileDrillingWebSocketNotifier() {
    }

    public static void register(String sessionId, Session wsSession) {
        SESSIONS.put(sessionId, wsSession);
    }

    public static void unregister(String sessionId) {
        SESSIONS.remove(sessionId);
    }

    public static void notifySession(String sessionId, WhileDrillingEvaluationResult result) {
        Session ws = SESSIONS.get(sessionId);
        if (ws == null || !ws.isOpen()) {
            return;
        }
        try {
            ws.getBasicRemote().sendText(JSON.toJSONString(result));
        } catch (IOException ignored) {
            SESSIONS.remove(sessionId);
        }
    }
}
