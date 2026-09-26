"""모든 차트 빌더의 공통 인터페이스."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

import pandas as pd
from plotly.graph_objects import Figure

from dashboard.config.theme import ThemeConfig


@dataclass
class ChartSpec:
    chart_type: str
    x: Optional[str] = None
    y: Union[str, List[str], None] = None
    color: Optional[str] = None
    size: Optional[str] = None
    title: str = ""
    agg_func: Optional[str] = None
    orientation: str = "v"


class ChartBuilder(ABC):
    def __init__(self, theme: ThemeConfig) -> None:
        self.theme = theme

    @abstractmethod
    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        """Plotly Figure를 생성한다 (하위 클래스 구현 몫).

        입력: df — 이미 필터·집계를 마친, 차트에 바로 그릴 데이터.
              spec — 어떤 컬럼을 x/y/color/size로 쓸지, 제목·orientation 등
              차트 구성을 담은 ChartSpec.
        동작: spec을 해석해 plotly.express 또는 graph_objects로 trace를
              만들고, 보통 마지막에 self._apply_theme(fig)로 스타일을 입힌다.
        반환: 완성된 plotly.graph_objects.Figure.
        """

    def _apply_theme(self, fig: Figure) -> Figure:
        """공통 스타일(색상·폰트·여백)을 적용한다 (미구현, 원본 반환).

        입력: fig — build()가 만든, 아직 테마가 안 입혀진 Figure.
        동작: self.theme(ThemeConfig)의 palette/font_family/chart_template을
              fig.update_layout(...)에 반영한다.
        반환: 스타일이 적용된 동일한 Figure 객체.
        """
        return fig

    def _validate_spec(self, spec: ChartSpec) -> None:
        """스펙 유효성 검사 (미구현).

        입력: spec — build()에 전달될 ChartSpec.
        동작: 이 빌더가 그림을 그리는 데 필수인 필드(예: BarChartBuilder는
              x, y가 필수)가 채워져 있는지 확인한다.
        반환: 없음. 필수 필드가 비어 있으면 utils/exceptions.py의
              ChartRenderError를 발생시켜야 한다.
        """
        pass
