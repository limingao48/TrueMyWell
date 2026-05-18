package club.yunzhi.api.workReview.util;

import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * 将设计轨迹 E/N/D 折线反算为测深、井斜、网格方位（与 BasicData 列名一致），写入「井斜数据表」工作表并输出 xlsx。
 * 测深为沿轨迹弦长累计；井斜、方位由相邻点弦向与垂深分量得到。
 */
public final class SurveyTrajectoryExcelBuilder {

    private SurveyTrajectoryExcelBuilder() {
    }

    /** 工作簿内工作表名称（井斜数据表） */
    public static final String SHEET_NAME = "井斜数据表";

    /** 与 {@link ExcelParser} 表头一致，便于基础数据页再导入 */
    public static final String HEADER_MD = "测深(m)";
    public static final String HEADER_INC = "井斜角(°)";
    public static final String HEADER_AZI = "网格方位(°)";

    /**
     * @param trajEnd 设计轨迹 [3][n]，[0]=E，[1]=N，[2]=D（垂深向下为正）
     */
    public static byte[] buildFromTrajectoryEnd(double[][] trajEnd) throws IOException {
        if (trajEnd == null || trajEnd.length != 3 || trajEnd[0] == null || trajEnd[0].length < 2) {
            throw new IllegalArgumentException("轨迹点不足，无法生成 Excel");
        }
        int n = trajEnd[0].length;
        if (trajEnd[1].length != n || trajEnd[2].length != n) {
            throw new IllegalArgumentException("E/N/D 数组长度不一致");
        }

        List<double[]> rows = computeSurveyRows(trajEnd);
        try (XSSFWorkbook wb = new XSSFWorkbook();
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            Sheet sheet = wb.createSheet(SHEET_NAME);
            Row h = sheet.createRow(0);
            setCell(h.createCell(0), HEADER_MD);
            setCell(h.createCell(1), HEADER_INC);
            setCell(h.createCell(2), HEADER_AZI);
            int r = 1;
            for (double[] row : rows) {
                Row data = sheet.createRow(r++);
                setNumeric(data.createCell(0), row[0]);
                setNumeric(data.createCell(1), row[1]);
                setNumeric(data.createCell(2), row[2]);
            }
            for (int c = 0; c < 3; c++) {
                sheet.autoSizeColumn(c);
            }
            wb.write(bos);
            return bos.toByteArray();
        }
    }

    private static void setCell(Cell c, String v) {
        c.setCellValue(v);
    }

    private static void setNumeric(Cell c, double v) {
        c.setCellValue(v);
    }

    /**
     * 首点 MD=0、井斜=0、方位=0；之后每个相邻折线段反算一组测深（累计弦长）、井斜、网格方位。
     */
    static List<double[]> computeSurveyRows(double[][] trajEnd) {
        int n = trajEnd[0].length;
        List<double[]> out = new ArrayList<>();
        out.add(new double[]{0.0, 0.0, 0.0});

        double md = 0.0;
        for (int i = 1; i < n; i++) {
            double dE = trajEnd[0][i] - trajEnd[0][i - 1];
            double dN = trajEnd[1][i] - trajEnd[1][i - 1];
            double dD = trajEnd[2][i] - trajEnd[2][i - 1];
            double ds = Math.sqrt(dE * dE + dN * dN + dD * dD);
            if (ds < 1e-9) {
                continue;
            }
            md += ds;
            double cosRatio = dD / ds;
            cosRatio = Math.max(-1.0, Math.min(1.0, cosRatio));
            double incDeg = Math.toDegrees(Math.acos(cosRatio));
            double aziDeg = Math.toDegrees(Math.atan2(dE, dN));
            aziDeg = normalizeAzimuthDeg(aziDeg);
            out.add(new double[]{md, incDeg, aziDeg});
        }
        return out;
    }

    private static double normalizeAzimuthDeg(double deg) {
        double a = deg % 360.0;
        if (a < 0) {
            a += 360.0;
        }
        return a;
    }
}
