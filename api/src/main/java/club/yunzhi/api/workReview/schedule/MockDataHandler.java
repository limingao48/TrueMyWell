package club.yunzhi.api.workReview.schedule;
import club.yunzhi.api.workReview.entity.*;
import club.yunzhi.api.workReview.repository.FeatherRepository;
import club.yunzhi.api.workReview.repository.TaskRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import com.alibaba.fastjson.JSONObject;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * 用于生成模拟数据，模拟有接口提供数据的实际情况
 */
@Component
public class MockDataHandler {
    private FeatherRepository featherRepository;
    private WellRepository wellRepository;
    private TaskRepository taskRepository;

    private List<Integer> depths = new ArrayList<>();
    private boolean inited = false;
    private int row = 0;

    MockDataHandler(FeatherRepository featherRepository,
                    WellRepository wellRepository,
                    TaskRepository taskRepository) {
        this.featherRepository = featherRepository;
        this.wellRepository = wellRepository;
        this.taskRepository = taskRepository;
    }

//    @Scheduled(cron = "0/5 * * * * *")
    public void generateMockData() throws IOException {
        List<Task> taskList = this.taskRepository.getRunningTask();

        // 使模拟的数据深度递增
        if(taskList.size() != depths.size()){
            while (depths.size() < taskList.size()){
                depths.add(0);
                inited = true;
            }
        }

        // 每隔5秒新增3条数据
        for (int i = 0; i < taskList.size(); i++) {
            System.out.println("每隔5秒新增数据");
            Random random = new Random();
            Well well = taskList.get(i).getWell();
//            ReceiveFeather receiveFeather = setReceiveFeather("src/main/resources/22_feature.xlsx");
            ReceiveFeather receiveFeather = setReceiveFeather("/22_feature.xlsx");
            depths.set(i,depths.get(i)+1);
            row = (row + 1) % 38;
            featherRequest(receiveFeather, well.getUniqueKey());
        }
    }

    public ReceiveFeather setReceiveFeather(String url) throws IOException {
        Random random = new Random();
        XSSFWorkbook xssfWorkbook = new XSSFWorkbook(new FileInputStream(url));
        XSSFSheet sheet = xssfWorkbook.getSheetAt(0);
        ReceiveFeather receiveFeather = new ReceiveFeather();
        receiveFeather.setDepth(Float.parseFloat(sheet.getRow(row).getCell(23).toString()));
        receiveFeather.setOffset(Float.parseFloat(sheet.getRow(row).getCell(16).toString()));
        receiveFeather.setMagnetic_amount(Float.parseFloat(sheet.getRow(row).getCell(18).toString()));
        receiveFeather.setMagnetic_angle(Float.parseFloat(sheet.getRow(row).getCell(17).toString()));
        receiveFeather.setMagnetic_amplitude(Float.parseFloat(sheet.getRow(row).getCell(21).toString()));
        receiveFeather.setRef_distance(random.nextFloat() * 36.0f + 35.0f);
        receiveFeather.setHigh_orientation(Float.parseFloat(sheet.getRow(row).getCell(21).toString()));
        receiveFeather.setNorth_orientation(Float.parseFloat(sheet.getRow(row).getCell(20).toString()));
        ReceiveOneFeather receiveOneFeather = new ReceiveOneFeather();
        List<ReceiveOneFeather> receiveOneFeathers = new ArrayList<>();
        receiveOneFeather.setX0(Float.parseFloat(sheet.getRow(row).getCell(0).toString()));
        receiveOneFeather.setY0(Float.parseFloat(sheet.getRow(row).getCell(1).toString()));
        receiveOneFeather.setZ0(Float.parseFloat(sheet.getRow(row).getCell(2).toString()));
        receiveOneFeather.setX1(Float.parseFloat(sheet.getRow(row).getCell(3).toString()));
        receiveOneFeather.setY1(Float.parseFloat(sheet.getRow(row).getCell(4).toString()));
        receiveOneFeather.setZ1(Float.parseFloat(sheet.getRow(row).getCell(5).toString()));
        receiveOneFeather.setX2(Float.parseFloat(sheet.getRow(row).getCell(6).toString()));
        receiveOneFeather.setY2(Float.parseFloat(sheet.getRow(row).getCell(7).toString()));
        receiveOneFeather.setZ2(Float.parseFloat(sheet.getRow(row).getCell(8).toString()));
        receiveOneFeather.setG_x(Float.parseFloat(sheet.getRow(row).getCell(9).toString()));
        receiveOneFeather.setG_y(Float.parseFloat(sheet.getRow(row).getCell(10).toString()));
        receiveOneFeather.setG_z(Float.parseFloat(sheet.getRow(row).getCell(11).toString()));
        receiveOneFeather.setR_angle(Float.parseFloat(sheet.getRow(row).getCell(12).toString()));
        receiveOneFeather.setL_angle(Float.parseFloat(sheet.getRow(row).getCell(13).toString()));
        receiveOneFeather.setD_angle(Float.parseFloat(sheet.getRow(row).getCell(14).toString()));
        receiveOneFeather.setTemperature(Float.parseFloat(sheet.getRow(row).getCell(15).toString()));
        receiveOneFeathers.add(receiveOneFeather);
        receiveFeather.setOneFeathers(receiveOneFeathers);
        return receiveFeather;
    }

    public void featherRequest(ReceiveFeather receiveFeather, String uniqueKey) {
        String url = "http://10.112.205.113:8003/feather/add/" + uniqueKey;
        // 请求表
        JSONObject paramMap = new JSONObject();
        JSONObject paramMap1 = new JSONObject();
        List<JSONObject> jsonObjects = new ArrayList<JSONObject>();
        // paramMap.put(feather);
        paramMap.put("depth", receiveFeather.getDepth());
        paramMap1.put("x0", receiveFeather.getOneFeathers().get(0).getX0());
        paramMap1.put("x1", receiveFeather.getOneFeathers().get(0).getX1());
        paramMap1.put("x2", receiveFeather.getOneFeathers().get(0).getX2());
        paramMap1.put("y0", receiveFeather.getOneFeathers().get(0).getY0());
        paramMap1.put("y1", receiveFeather.getOneFeathers().get(0).getY1());
        paramMap1.put("y2", receiveFeather.getOneFeathers().get(0).getY2());
        paramMap1.put("z0", receiveFeather.getOneFeathers().get(0).getZ0());
        paramMap1.put("z1", receiveFeather.getOneFeathers().get(0).getZ1());
        paramMap1.put("z2", receiveFeather.getOneFeathers().get(0).getZ2());
        paramMap1.put("g_x", receiveFeather.getOneFeathers().get(0).getG_x());
        paramMap1.put("g_y", receiveFeather.getOneFeathers().get(0).getG_y());
        paramMap1.put("g_z", receiveFeather.getOneFeathers().get(0).getG_z());
        paramMap1.put("r_angle", receiveFeather.getOneFeathers().get(0).getR_angle());
        paramMap1.put("l_angle", receiveFeather.getOneFeathers().get(0).getL_angle());
        paramMap1.put("d_angle", receiveFeather.getOneFeathers().get(0).getD_angle());
        paramMap1.put("temperature", receiveFeather.getOneFeathers().get(0).getTemperature());

        JSONObject paramMap2 = new JSONObject();
        paramMap2.put("x0", receiveFeather.getOneFeathers().get(0).getX0());
        paramMap2.put("x1", receiveFeather.getOneFeathers().get(0).getX1());
        paramMap2.put("x2", receiveFeather.getOneFeathers().get(0).getX2());
        paramMap2.put("y0", receiveFeather.getOneFeathers().get(0).getY0());
        paramMap2.put("y1", receiveFeather.getOneFeathers().get(0).getY1());
        paramMap2.put("y2", receiveFeather.getOneFeathers().get(0).getY2());
        paramMap2.put("z0", receiveFeather.getOneFeathers().get(0).getZ0());
        paramMap2.put("z1", receiveFeather.getOneFeathers().get(0).getZ1());
        paramMap2.put("z2", receiveFeather.getOneFeathers().get(0).getZ2());
        paramMap2.put("g_x", receiveFeather.getOneFeathers().get(0).getG_x());
        paramMap2.put("g_y", receiveFeather.getOneFeathers().get(0).getG_y());
        paramMap2.put("g_z", receiveFeather.getOneFeathers().get(0).getG_z());
        paramMap2.put("r_angle", receiveFeather.getOneFeathers().get(0).getR_angle());
        paramMap2.put("l_angle", receiveFeather.getOneFeathers().get(0).getL_angle());
        paramMap2.put("d_angle", receiveFeather.getOneFeathers().get(0).getD_angle());
        paramMap2.put("temperature", receiveFeather.getOneFeathers().get(0).getTemperature());

        jsonObjects.add(paramMap1);
        jsonObjects.add(paramMap2);

        paramMap.put("oneFeathers", jsonObjects);
//        paramMap.put("relative_north_orientation", receiveFeather.getOffset());
//        paramMap.put("relative_distance", receiveFeather.getOffset());
//        paramMap.put("inclinometer_relative_distance", receiveFeather.getOffset());
        paramMap.put("offset", receiveFeather.getOffset());
        paramMap.put("magnetic_angle", receiveFeather.getMagnetic_angle());
        paramMap.put("magnetic_amount", receiveFeather.getMagnetic_amount());
        paramMap.put("magnetic_amplitude", receiveFeather.getMagnetic_amplitude());
        paramMap.put("north_orientation", receiveFeather.getNorth_orientation());
        paramMap.put("high_orientation", receiveFeather.getHigh_orientation());

        //        请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("user-agent", "Mozilla/5.0 WindSnowLi-Blog");
        //        整合请求头和请求参数
        HttpEntity<JSONObject> httpEntity = new HttpEntity<>(paramMap, headers);
        //         请求客户端
        RestTemplate client = new RestTemplate();
        //      发起请求
        String body = client.postForEntity(url, httpEntity, String.class).getBody();
        System.out.println("******** POST请求 *********");
        assert body != null;
        System.out.println(body);
    }
}
