"""막대 차트 빌더: 수직/수평 막대 및 그룹/누적 비교."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from dashboard.utils.exceptions import ChartRenderError
from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class BarChartBuilder(ChartBuilder):
    """DataFrame을 Plotly 막대 차트로 변환한다.

    spec.x: 범주 컬럼 (예: '자치구')
    spec.y: 숫자 컬럼 또는 숫자 컬럼명 리스트. 없으면 행 개수를 센다.
    spec.color: 비교 집단 컬럼 (선택)
    spec.orientation: 'v' 또는 'h'
    spec.agg_func: 'sum', 'mean', 'count', 'min', 'max' (선택)
    spec.barmode: 'group' 또는 'stack' (선택적인 확장 속성)
    """

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        if not isinstance(df, pd.DataFrame):
            raise ChartRenderError("막대 차트에는 pandas DataFrame이 필요합니다.")
        if df.empty:
            raise ChartRenderError("막대 차트에 표시할 데이터가 없습니다.")
        if spec.chart_type != "bar":
            raise ChartRenderError("BarChartBuilder에는 chart_type='bar'가 필요합니다.")
        if not spec.x or spec.x not in df.columns:
            raise ChartRenderError(f"범주 컬럼을 찾을 수 없습니다: {spec.x!r}")
        if spec.orientation not in ("v", "h"):
            raise ChartRenderError("orientation은 'v' 또는 'h'여야 합니다.")
        if spec.color is not None and spec.color not in df.columns:
            raise ChartRenderError(f"색상 구분 컬럼을 찾을 수 없습니다: {spec.color!r}")

        mode = getattr(spec, "barmode", "group")
        if mode not in ("group", "stack"):
            raise ChartRenderError("barmode는 'group' 또는 'stack'이어야 합니다.")

        data = df.copy()
        y = spec.y
        if y is None:
            # 원시 가맹점 목록: 자치구·업종별 행 개수 세기.
            keys = [spec.x] + ([spec.color] if spec.color and spec.color != spec.x else [])
            count_col = "가맹점 수"
            while count_col in data.columns:
                count_col += "_"
            data = data.groupby(keys, dropna=False).size().reset_index(name=count_col)
            y = count_col
        else:
            y_cols = [y] if isinstance(y, str) else list(y)
            if not y_cols or any(col not in data.columns for col in y_cols):
                raise ChartRenderError(f"값 컬럼을 찾을 수 없습니다: {y_cols}")
            if any(not pd.api.types.is_numeric_dtype(data[col]) for col in y_cols):
                raise ChartRenderError("막대 차트 값 컬럼은 숫자여야 합니다.")
            if len(y_cols) > 1 and spec.color:
                raise ChartRenderError("여러 값 컬럼과 color를 동시에 지정할 수 없습니다.")
            if spec.agg_func:
                if spec.agg_func not in {"sum", "mean", "count", "min", "max"}:
                    raise ChartRenderError("지원하지 않는 집계 함수입니다.")
                keys = [spec.x] + ([spec.color] if spec.color and spec.color != spec.x else [])
                data = data.groupby(keys, dropna=False, as_index=False)[y_cols].agg(spec.agg_func)

        # Plotly의 수평 막대는 수치축이 x, 범주축이 y이다.
        x_axis, y_axis = (y, spec.x) if spec.orientation == "h" else (spec.x, y)
        palette = getattr(self.theme, "palette", None)
        fig = px.bar(
            data,
            x=x_axis,
            y=y_axis,
            color=spec.color,
            orientation=spec.orientation,
            title=spec.title,
            barmode=mode,
            template=getattr(self.theme, "chart_template", "plotly_white"),
            color_discrete_sequence=palette or None,
        )
        fig.update_layout(font_family=getattr(self.theme, "font_family", "sans-serif"))
        return self._apply_theme(fig)
