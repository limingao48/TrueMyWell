package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.*;
import club.yunzhi.api.workReview.service.WhileDrillingEvaluationService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("whileDrilling")
public class WhileDrillingController {

    private final WhileDrillingEvaluationService whileDrillingEvaluationService;

    public WhileDrillingController(WhileDrillingEvaluationService whileDrillingEvaluationService) {
        this.whileDrillingEvaluationService = whileDrillingEvaluationService;
    }

    @PostMapping("session/start")
    public WhileDrillingSessionInfo startSession(@RequestBody WhileDrillingSessionStartRequest request) {
        return whileDrillingEvaluationService.startSession(request);
    }

    @PostMapping("session/stop")
    public void stopSession(@RequestBody MapWrapper body) {
        whileDrillingEvaluationService.stopSession(body.getSessionId());
    }

    @GetMapping("session/{sessionId}")
    public WhileDrillingSessionInfo getSession(@PathVariable String sessionId) {
        return whileDrillingEvaluationService.getSessionInfo(sessionId);
    }

    @PostMapping("position")
    public WhileDrillingEvaluationResult submitPosition(@RequestBody WhileDrillingPositionRequest request) {
        return whileDrillingEvaluationService.submitPosition(request);
    }

    /** 简单包装类避免 Map 泛型 */
    public static class MapWrapper {
        private String sessionId;

        public String getSessionId() {
            return sessionId;
        }

        public void setSessionId(String sessionId) {
            this.sessionId = sessionId;
        }
    }
}
