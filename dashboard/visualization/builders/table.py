from __future__ import annotations

import pandas as pd
from plotly.graph_objects import Figure

from dashboard.visualization.builders.base import ChartBuilder, ChartSpec


class TableBuilder(ChartBuilder):
    """인터랙티브 데이터 테이블."""

    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        """미구현: 빈 Figure 반환.

        입력: df — 표로 보여줄 데이터 그 자체 (컬럼 전체를 그대로 표시).
              spec.title — 표 위에 붙일 제목 정도만 사용.
        동작(완성판 기준): go.Figure(data=[go.Table(header=..., cells=...)])로
              df의 컬럼/값을 그대로 표 형태 trace에 담는다.
        반환: 테이블 Figure.
              (참고: 실제 화면에서는 이보다 [visualization/components.py](../components.py)의
              TableRenderer.render()로 st.dataframe을 쓰는 편이 정렬·검색 등에서
              더 실용적일 수 있다 — 설계서에는 둘 다 존재한다.)
        """
        return Figure()
