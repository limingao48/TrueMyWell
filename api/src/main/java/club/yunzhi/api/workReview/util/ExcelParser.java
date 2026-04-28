package club.yunzhi.api.workReview.util;

import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * Excel解析工具类
 */
public class ExcelParser {

    /**
     * 解析Excel文件中的轨迹点数据
     * @param fileContent Excel文件二进制内容
     * @param fileName 文件名（用于判断格式）
     * @return 轨迹点列表
     */
    public static List<TrajectoryDesignResult.TrajectoryPoint> parseTrajectoryFromExcel(byte[] fileContent, String fileName) {
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

            // 查找表头行，确定E、N、D列的位置
            int eCol = -1, nCol = -1, dCol = -1;
            Row headerRow = sheet.getRow(firstRow);
            
            for (int i = firstRow; i <= Math.min(firstRow + 2, lastRow); i++) {
                Row row = sheet.getRow(i);
                if (row != null) {
                    for (int j = 0; j < row.getLastCellNum(); j++) {
                        Cell cell = row.getCell(j);
                        String value = getCellStringValue(cell);
                        if (value != null) {
                            String lowerValue = value.toLowerCase().trim();
                            if (lowerValue.contains("东") || lowerValue.contains("e") || lowerValue.contains("east") || lowerValue.contains("x")) {
                                eCol = j;
                            } else if (lowerValue.contains("北") || lowerValue.contains("n") || lowerValue.contains("north") || lowerValue.contains("y")) {
                                nCol = j;
                            } else if (lowerValue.contains("深") || lowerValue.contains("d") || lowerValue.contains("depth") || lowerValue.contains("z")) {
                                dCol = j;
                            }
                        }
                    }
                }
                if (eCol >= 0 && nCol >= 0 && dCol >= 0) {
                    break;
                }
            }

            // 如果没找到表头，默认使用第1、2、3列
            if (eCol < 0) eCol = 0;
            if (nCol < 0) nCol = 1;
            if (dCol < 0) dCol = 2;

            // 从表头行的下一行开始读取数据
            int startRow = firstRow + 1;
            if (headerRow != null && isHeaderRow(headerRow)) {
                startRow = firstRow + 1;
            }

            // 读取数据行
            for (int i = startRow; i <= lastRow; i++) {
                Row row = sheet.getRow(i);
                if (row == null) continue;

                Double e = getCellNumericValue(row.getCell(eCol));
                Double n = getCellNumericValue(row.getCell(nCol));
                Double d = getCellNumericValue(row.getCell(dCol));

                if (e != null && n != null && d != null) {
                    points.add(new TrajectoryDesignResult.TrajectoryPoint(e, n, d));
                }
            }

        } catch (IOException e) {
            // 如果解析失败，返回空列表
        }

        return points;
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

    private static boolean isHeaderRow(Row row) {
        if (row == null) return false;
        for (int i = 0; i < row.getLastCellNum(); i++) {
            Cell cell = row.getCell(i);
            if (cell != null && cell.getCellType() == CellType.STRING) {
                String value = cell.getStringCellValue().toLowerCase();
                if (value.contains("东") || value.contains("北") || value.contains("深") || 
                    value.contains("e") || value.contains("n") || value.contains("d")) {
                    return true;
                }
            }
        }
        return false;
    }
}
