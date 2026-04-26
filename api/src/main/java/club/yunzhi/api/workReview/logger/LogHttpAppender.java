package club.yunzhi.api.workReview.logger;

import ch.qos.logback.ext.loggly.LogglyAppender;
import club.yunzhi.api.workReview.config.WebMvcConfig;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

@Component
public class LogHttpAppender<E> extends LogglyAppender<E> {
    public static final String ENDPOINT_URL_PATH = "inputs/";
    public static Calendar lastSendTime = Calendar.getInstance();
    public static List<String> events = new ArrayList<>();

    public LogHttpAppender() {
    }

    @Override
    protected void append(E eventObject) {
        String active = WebMvcConfig.active;
        if (active != null && active.equals("pro")) {
            String msg = this.layout.doLayout(eventObject);
            this.postToLoggly(msg);
        }
    }

    private void postToLoggly(final String event) {
        events.add(event);
        Calendar calendar = Calendar.getInstance();
        if (events.size() >= 100 || (calendar.getTimeInMillis() - lastSendTime.getTimeInMillis() >= 120000)) {
            try {
                System.out.println(calendar.getTimeInMillis() - lastSendTime.getTimeInMillis());
                lastSendTime = calendar;
                List<String> sendEvents = events;
                events = new ArrayList<>();

                assert this.endpointUrl != null;
                URL endpoint = new URL(this.endpointUrl);
                final HttpURLConnection connection;
                if (this.proxy == null) {
                    connection = (HttpURLConnection) endpoint.openConnection();
                } else {
                    connection = (HttpURLConnection) endpoint.openConnection(this.proxy);
                }
                connection.setRequestMethod("POST");
                connection.setDoOutput(true);
                connection.addRequestProperty("Content-Type", this.layout.getContentType());
                connection.connect();
                this.sendAndClose(sendEvents, connection.getOutputStream());
                connection.disconnect();
                final int responseCode = connection.getResponseCode();
                if (responseCode != 200) {
                    final String message = this.readResponseBody(connection.getInputStream());
                    this.addError("Loggly post failed (HTTP " + responseCode + ").  Response body:\n" + message);
                }
            } catch (final IOException e) {
                this.addError("IOException while attempting to communicate with Loggly", e);
            }
        }
    }

    private void sendAndClose(final List<String> events, final OutputStream output) throws IOException {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write('[');
            boolean first = true;
            for (String event : events) {
                if (event.length() > 65535) {
                    System.out.println("日志长度大于65535，该记录不发送至服务器");
                    continue;
                }

                if (first) {
                    first = false;
                } else {
                    out.write(',');
                }

                out.write(event.getBytes());
            }
            out.write(']');
            final byte[] data = out.toByteArray();
            output.write(data);
        } finally {
            output.close();
        }
    }

    @Override
    protected String getEndpointPrefix() {
        return ENDPOINT_URL_PATH;
    }


}
