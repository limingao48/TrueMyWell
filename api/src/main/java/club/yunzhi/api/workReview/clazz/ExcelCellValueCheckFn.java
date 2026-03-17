package club.yunzhi.api.workReview.clazz;

import java.util.Optional;

public interface ExcelCellValueCheckFn<T> {
  Optional<String> checkFn(T value);
}
