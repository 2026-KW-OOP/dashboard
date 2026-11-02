# 시각화 모듈 (Visualization)

서울사랑상품권 가맹점 데이터를 Plotly 차트 및 표로 변환하는 모듈입니다. `build(df, spec)`의 반환값은 Plotly `Figure`이며, 화면 출력은 Streamlit UI 담당 코드에서 수행합니다.

## 담당 클래스

| 파일 | 클래스 | 역할 |
| --- | --- | --- |
| `builders/base.py` | `ChartSpec`, `ChartBuilder` | 차트 설정, 추상 인터페이스, 공통 설정 검사와 테마 적용 |
| `builders/bar.py` | `BarChartBuilder` | 자치구별 막대그래프(원본 행 수 또는 집계된 수치) |
| `builders/pie.py` | `PieChartBuilder` | 업종별 비율 도넛 차트 |
| `builders/table.py` | `TableBuilder` | 가맹점 목록 Plotly 테이블 |

`ChartBuilder`는 추상 클래스이므로 직접 인스턴스를 생성하지 않고, 각 하위 클래스의 `build()` 메서드를 사용합니다. `_validate_spec(spec)`는 필요할 때 호출하는 공통 검사 메서드입니다. 기존 하위 클래스 세 개는 자체적으로도 설정/데이터 검증을 수행하므로 코드를 그대로 유지했습니다.

## 실행 예시

저장소 최상위 디렉터리에서 Python을 실행한 경우:

```python
import pandas as pd
from dashboard.config.theme import ThemeConfig
from dashboard.visualization.builders.base import ChartSpec
from dashboard.visualization.builders.bar import BarChartBuilder
from dashboard.visualization.builders.pie import PieChartBuilder
from dashboard.visualization.builders.table import TableBuilder

df = pd.DataFrame({
    "자치구": ["강남구", "강남구", "마포구"],
    "업종": ["음식점", "카페", "음식점"],
})

theme = ThemeConfig()
bar = BarChartBuilder(theme).build(df, ChartSpec(chart_type="bar", x="자치구"))
pie = PieChartBuilder(theme).build(df, ChartSpec(chart_type="pie", x="업종"))
table = TableBuilder(theme).build(df, ChartSpec(chart_type="table", title="가맹점 목록"))
```

Streamlit 화면에서는 `st.plotly_chart(bar, use_container_width=True)`처럼 Figure를 전달합니다. 집계된 DataFrame의 경우 `ChartSpec(chart_type="bar", x="자치구", y="가맹점 수")` 또는 `ChartSpec(chart_type="pie", x="업종", y="가맹점 수")`를 사용합니다.

## 주의 사항

- `pandas`, `plotly`와 팀 프로젝트의 `dashboard/config/theme.py`, `dashboard/utils/exceptions.py`가 필요합니다.
- `base.py`는 팀 저장소에 이미 존재하는 파일이므로 **기존 파일의 변경 사항과 비교한 뒤** 덮어쓰세요. 공통 필드와 기존 `build(df, spec)` 호출 형식은 유지했습니다.
- `ChartBuilder._apply_theme()`는 `ThemeConfig`의 템플릿·폰트·팔레트를 사용하며, 다크 모드에서는 Plotly 다크 템플릿을 적용합니다.
- 데이터 처리나 파일 읽기 및 Streamlit UI는 다른 담당자의 코드와 연결해야 합니다.
- 표는 `go.Table`이므로 `st.dataframe()`의 정렬 UI를 지원하지 않습니다.
- 네 파일의 단위 동작은 별도 테스트 가능하지만, 저장소 전체 통합 실행은 팀 환경에서 최종 확인해야 합니다.
