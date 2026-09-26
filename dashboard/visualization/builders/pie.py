from __future__ import annotations

import pandas as pd
from plotly.graph_objects import Figure

from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class PieChartBuilder(ChartBuilder):
    """파이·도넛 차트 (비중 시각화)."""

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        """미구현: 빈 Figure 반환.

        입력: df — 그릴 데이터. spec.x(또는 spec.color) — 비중을 나눌
              범주 컬럼(예: "상품군"), spec.y — 각 범주의 크기를 나타낼
              값 컬럼(예: "매출").
        동작(완성판 기준): plotly.express.pie(df, names=spec.x, values=spec.y)로
              범주별 합계 비중을 계산해 그린다.
        반환: 파이(또는 도넛) 차트 Figure.
        """
        return Figure()
