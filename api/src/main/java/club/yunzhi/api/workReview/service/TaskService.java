package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.BarData;
import club.yunzhi.api.workReview.entity.Task;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.text.SimpleDateFormat;
import java.util.*;


public interface TaskService {
    Page<Task> page(String name, String wellId, ArrayList<Long> models, Integer status, String startDate, String endDate, Pageable pageable);

    List<Task> getTasksByWell(String wellId);

    Task add(Task task);

    Task run(Long taskId);

    Task freeze(Long taskId);

    Task edit(Long id, Task task);

    Long getAllNumber();

    Long monthTaskNumber();

    public static Date getDateAfterTime(String dateStr, int time, int timeType) {
        try {
            SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            Calendar cal = Calendar.getInstance();
            cal.setTime(df.parse(dateStr));
            cal.add(timeType, time);
            return cal.getTime();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    /*
        获取当天0点时间戳
     */
    public static Long dayTimeInMillis() {
        Calendar calendar = Calendar.getInstance();// 获取当前日期
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        Long time = calendar.getTimeInMillis();
        return time;
    }

    public static void requestSubOrUnSub(String uniqueKey, String status) {
        RestTemplate restTemplate = new RestTemplate();
        String apiURL = "http://localhost:8003/subcrible/" + uniqueKey;
        HttpHeaders headers = new HttpHeaders();
        headers.add("status",status);
        headers.setContentType(MediaType.APPLICATION_JSON);
        Map<String, Object> requestParam = new HashMap<>();
        HttpEntity<Map<String, Object>> request = new HttpEntity<Map<String, Object>>(requestParam, headers);
        ResponseEntity<String> entity2 = restTemplate.exchange(apiURL, HttpMethod.GET, request, String.class);
        String body = entity2.getBody();
        System.out.println("接收到的信息为：" + body);
    }

    public static Date stringToDate(String[] times) {
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.YEAR, Integer.parseInt(times[0]));
        calendar.set(Calendar.MONTH, Integer.parseInt(times[1]) - 1);
        calendar.set(Calendar.DAY_OF_MONTH, Integer.parseInt(times[2]));
        calendar.set(Calendar.HOUR, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        Long time = calendar.getTimeInMillis();
        Date date = new Date(time);
        return date;
    }

    long todayTaskNumber();

    List<BarData> getMonthTaskNumber();

    void delete(Long id);

    Integer getTaskNumberByWellIdAndStatus(Long wellId, Integer status);
}
