"""업종별 비중을 보여 주는 파이/도넛 차트 빌더."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from dashboard.utils.exceptions import ChartRenderError
from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class PieChartBuilder(ChartBuilder):
    """spec.x(또는 color)를 범주로 삼아 도넛 차트를 생성한다.

    spec.y가 있으면 해당 값의 합계를 비중으로 보여 주고,
    없으면 각 범주의 행 개수를 계산한다.
    """

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        if not isinstance(df, pd.DataFrame):
            raise ChartRenderError("도넛 차트에는 pandas DataFrame이 필요합니다.")
        if df.empty:
            raise ChartRenderError("도넛 차트에 표시할 데이터가 없습니다.")
        if spec.chart_type != "pie":
            raise ChartRenderError("PieChartBuilder에는 chart_type='pie'가 필요합니다.")

        category = spec.x or spec.color
        if not category or category not in df.columns:
            raise ChartRenderError(f"업종 등 범주 컬럼을 찾을 수 없습니다: {category!r}")
        if spec.y is not None:
            if not isinstance(spec.y, str) or spec.y not in df.columns:
                raise ChartRenderError("도넛 차트의 y는 숫자 컬럼명 하나여야 합니다.")
            if not pd.api.types.is_numeric_dtype(df[spec.y]):
                raise ChartRenderError("도넛 차트 값 컬럼은 숫자여야 합니다.")
            if df[spec.y].dropna().lt(0).any():
                raise ChartRenderError("비율을 나타내는 값은 음수일 수 없습니다.")
            if df[spec.y].fillna(0).sum() <= 0:
                raise ChartRenderError("비율을 계산할 양수 값이 없습니다.")
            values = spec.y
            # 같은 업종이 여러 행에 등장하면 하나의 조각으로 합친다.
            data = df.groupby(category, dropna=False, as_index=False)[values].sum()
        else:
            count_col = "가맹점 수"
            while count_col in df.columns:
                count_col += "_"
            data = df.groupby(category, dropna=False).size().reset_index(name=count_col)
            values = count_col

        palette = getattr(self.theme, "palette", None)
        fig = px.pie(
            data,
            names=category,
            values=values,
            hole=0.55,
            title=spec.title,
            template=getattr(self.theme, "chart_template", "plotly_white"),
            color_discrete_sequence=palette or None,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(font_family=getattr(self.theme, "font_family", "sans-serif"))
        return self._apply_theme(fig)
