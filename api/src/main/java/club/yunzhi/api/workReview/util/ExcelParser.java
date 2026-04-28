package club.yunzhi.api.workReview.util;

import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Excel解析工具类
 */
public class ExcelParser {
    // 与前端 BasicData 保持一致的列别名
    private static final String[] MD_ALIASES = {"测深(m)", "测深（m）", "测深", "md"};
    private static final String[] INC_ALIASES = {"井斜角(°)", "井斜角（°）", "井斜角", "井斜", "inclination"};
    private static final String[] AZI_ALIASES = {"网格方位(°)", "网格方位（°）", "网格方位", "方位", "azimuth"};

    /**
     * 解析Excel文件中的轨迹点数据
     * @param fileContent Excel文件二进制内容
     * @param fileName 文件名（用于判断格式）
     * @return 轨迹点列表
     */
    public static List<TrajectoryDesignResult.TrajectoryPoint> parseTrajectoryFromExcel(
            byte[] fileContent, String fileName, Double wellheadE, Double wellheadN, Double wellheadD) {
        List<TrajectoryDesignResult.TrajectoryPoint> points = new ArrayList<>();

        if (fileContent == null || fileContent.length == 0) {
            return points;
        }

        try (InputStream is = new ByteArrayInputStream(fileContent);
             Workbook workbook = createWorkbook(is, fileName)) {
            Sheet sheet = workbook.getSheetAt(0);
            if (sheet == null) {
                return points;
            }

            int firstRow = sheet.getFirstRowNum();
            int lastRow = sheet.getLastRowNum();
            if (lastRow < firstRow) {
                return points;
            }

            int mdCol = -1;
            int incCol = -1;
            int aziCol = -1;
            int dataStartRow = firstRow;

            for (int i = firstRow; i <= Math.min(firstRow + 3, lastRow); i++) {
                Row row = sheet.getRow(i);
                if (row != null) {
                    for (int j = 0; j < row.getLastCellNum(); j++) {
                        String value = getCellStringValue(row.getCell(j));
                        if (value == null) {
                            continue;
                        }
                        String normalized = normalizeHeader(value);
                        if (isAlias(normalized, MD_ALIASES)) {
                            mdCol = j;
                        } else if (isAlias(normalized, INC_ALIASES)) {
                            incCol = j;
                        } else if (isAlias(normalized, AZI_ALIASES)) {
                            aziCol = j;
                        }
                    }
                }
                if (mdCol >= 0 && incCol >= 0 && aziCol >= 0) {
                    dataStartRow = i + 1;
                    break;
                }
            }

            if (mdCol < 0 || incCol < 0 || aziCol < 0) {
                mdCol = 0;
                incCol = 1;
                aziCol = 2;
                dataStartRow = firstRow;
            }

            List<double[]> surveyRows = new ArrayList<>();
            for (int i = dataStartRow; i <= lastRow; i++) {
                Row row = sheet.getRow(i);
                if (row == null) {
                    continue;
                }
                Double md = getCellNumericValue(row.getCell(mdCol));
                Double inc = getCellNumericValue(row.getCell(incCol));
                Double azi = getCellNumericValue(row.getCell(aziCol));
                if (md == null && inc == null && azi == null) {
                    continue;
                }
                if (md == null || inc == null || azi == null) {
                    continue;
                }
                surveyRows.add(new double[]{md, inc, azi});
            }

            if (surveyRows.isEmpty()) {
                return points;
            }

            surveyRows.sort((a, b) -> Double.compare(a[0], b[0]));

            double startE = wellheadE == null ? 0d : wellheadE;
            double startN = wellheadN == null ? 0d : wellheadN;
            double startD = wellheadD == null ? 0d : wellheadD;
            points.add(new TrajectoryDesignResult.TrajectoryPoint(startE, startN, startD));

            for (int i = 1; i < surveyRows.size(); i++) {
                double[] p1 = surveyRows.get(i - 1);
                double[] p2 = surveyRows.get(i);
                double dmd = p2[0] - p1[0];
                if (dmd <= 0) {
                    continue;
                }
                double inc1 = Math.toRadians(p1[1]);
                double inc2 = Math.toRadians(p2[1]);
                double az1 = Math.toRadians(p1[2]);
                double az2 = Math.toRadians(p2[2]);

                double cosDogleg = Math.cos(inc1) * Math.cos(inc2)
                        + Math.sin(inc1) * Math.sin(inc2) * Math.cos(az2 - az1);
                cosDogleg = Math.max(-1.0, Math.min(1.0, cosDogleg));
                double dogleg = Math.acos(cosDogleg);
                double rf = dogleg < 1e-12 ? 1.0 : (2.0 / dogleg) * Math.tan(dogleg / 2.0);

                double dN = 0.5 * dmd * (Math.sin(inc1) * Math.cos(az1) + Math.sin(inc2) * Math.cos(az2)) * rf;
                double dE = 0.5 * dmd * (Math.sin(inc1) * Math.sin(az1) + Math.sin(inc2) * Math.sin(az2)) * rf;
                double dD = 0.5 * dmd * (Math.cos(inc1) + Math.cos(inc2)) * rf;

                TrajectoryDesignResult.TrajectoryPoint prev = points.get(points.size() - 1);
                points.add(new TrajectoryDesignResult.TrajectoryPoint(
                        prev.getX() + dE,
                        prev.getY() + dN,
                        prev.getZ() + dD
                ));
            }
        } catch (IOException e) {
            return points;
        }

        return points;
    }

    private static boolean isAlias(String normalized, String[] aliases) {
        return Arrays.stream(aliases)
                .map(ExcelParser::normalizeHeader)
                .anyMatch(alias -> normalized.equals(alias));
    }

    private static String normalizeHeader(String value) {
        return value.toLowerCase()
                .replace("（", "(")
                .replace("）", ")")
                .replace(" ", "")
                .trim();
    }

    private static Workbook createWorkbook(InputStream is, String fileName) throws IOException {
        if (fileName != null && fileName.toLowerCase().endsWith(".xlsx")) {
            return new XSSFWorkbook(is);
        } else {
            return new HSSFWorkbook(is);
        }
    }

    private static String getCellStringValue(Cell cell) {
        if (cell == null) return null;
        
        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue();
            case NUMERIC:
                return String.valueOf(cell.getNumericCellValue());
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            case FORMULA:
                try {
                    return cell.getStringCellValue();
                } catch (Exception e) {
                    return String.valueOf(cell.getNumericCellValue());
                }
            default:
                return null;
        }
    }

    private static Double getCellNumericValue(Cell cell) {
        if (cell == null) return null;
        
        switch (cell.getCellType()) {
            case NUMERIC:
                return cell.getNumericCellValue();
            case STRING:
                try {
                    return Double.parseDouble(cell.getStringCellValue().trim());
                } catch (NumberFormatException e) {
                    return null;
                }
            case FORMULA:
                try {
                    return cell.getNumericCellValue();
                } catch (Exception e) {
                    return null;
                }
            default:
                return null;
        }
    }

}
