"""DataFrame을 Plotly 데이터 테이블로 변환한다."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure

from dashboard.utils.exceptions import ChartRenderError
from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class TableBuilder(ChartBuilder):
    """주어진 DataFrame의 모든 열과 행을 표 형태로 표시한다."""

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        if not isinstance(df, pd.DataFrame):
            raise ChartRenderError("테이블에는 pandas DataFrame이 필요합니다.")
        if df.empty:
            raise ChartRenderError("테이블에 표시할 데이터가 없습니다.")
        if spec.chart_type != "table":
            raise ChartRenderError("TableBuilder에는 chart_type='table'이 필요합니다.")

        # df 자체를 변경하지 않고 출력용 복사본만 문자열로 변환한다.
        display = df.astype(object).where(pd.notna(df), "")
        display = display.astype(str)
        is_dark = getattr(self.theme, "mode", "light") == "dark"
        header_color = getattr(self.theme, "primary_color", "#1f77b4")
        cell_color = "#252a34" if is_dark else "#ffffff"
        text_color = "#ffffff" if is_dark else "#222222"

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(map(str, display.columns)),
                        fill_color=header_color,
                        font=dict(color="white", size=13),
                        align="left",
                        height=32,
                    ),
                    cells=dict(
                        values=[display[col].tolist() for col in display.columns],
                        fill_color=cell_color,
                        font=dict(color=text_color, size=12),
                        align="left",
                        height=28,
                    ),
                )
            ]
        )
        fig.update_layout(
            title=spec.title,
            template=getattr(self.theme, "chart_template", "plotly_white"),
            font_family=getattr(self.theme, "font_family", "sans-serif"),
            margin=dict(l=10, r=10, t=55 if spec.title else 15, b=10),
        )
        return self._apply_theme(fig)
