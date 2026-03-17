package club.yunzhi.api.workReview.webSocketServer;

import club.yunzhi.api.workReview.entity.Message;
import com.alibaba.fastjson.JSONObject;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.json.JsonMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.websocket.EncodeException;
import javax.websocket.Encoder;
import javax.websocket.EndpointConfig;
import java.util.HashMap;

public class ServerEncoder implements Encoder.Text<Message> {
    private static final Logger log = LoggerFactory.getLogger(ServerEncoder.class);

    @Override
    public void init(EndpointConfig endpointConfig) {
        //可忽略
    }

    @Override
    public void destroy() {
        //可忽略
    }

    @Override
    public String encode(Message message) throws EncodeException {
        try {
            /*
             * 这里是重点，只需要返回Object序列化后的json字符串就行
             * 你也可以使用gosn，fastJson来序列化。
             */
            JsonMapper jsonMapper = new JsonMapper();
            return jsonMapper.writeValueAsString(message);

        } catch ( JsonProcessingException e) {
            e.printStackTrace();
            return null;
        }
    }
}

