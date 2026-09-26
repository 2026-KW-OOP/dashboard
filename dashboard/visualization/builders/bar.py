from __future__ import annotations

import pandas as pd
from plotly.graph_objects import Figure

from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class BarChartBuilder(ChartBuilder):
    """막대 차트 (수직/수평, 스택/그룹)."""

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        """미구현: 빈 Figure 반환.

        입력: df — 그릴 데이터. spec.x — 카테고리 컬럼(예: "지역"),
              spec.y — 값 컬럼(예: "매출", 여러 개면 멀티 시리즈),
              spec.color — 계열 구분 컬럼(있으면 그룹/스택 막대),
              spec.orientation — "v"(수직, 기본) | "h"(수평).
        동작(완성판 기준): plotly.express.bar(df, x=spec.x, y=spec.y,
              color=spec.color, orientation=spec.orientation)로 그린다.
        반환: 막대 차트 Figure.
        """
        return Figure()
