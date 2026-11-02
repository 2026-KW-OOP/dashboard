"""모든 차트 빌더가 공유하는 ChartSpec, 인터페이스, 유효성 검사 및 테마."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

import pandas as pd
from plotly.graph_objects import Figure

from dashboard.config.theme import ThemeConfig
from dashboard.utils.exceptions import ChartRenderError


@dataclass
class ChartSpec:
    """차트 생성에 필요한 설정. 팀 저장소의 기존 필드/순서를 유지한다."""

    chart_type: str
    x: Optional[str] = None
    y: Union[str, List[str], None] = None
    color: Optional[str] = None
    size: Optional[str] = None
    title: str = ""
    agg_func: Optional[str] = None
    orientation: str = "v"


class ChartBuilder(ABC):
    """Plotly 차트 빌더의 공통 추상 부모 클래스."""

    def __init__(self, theme: ThemeConfig) -> None:
        self.theme = theme

    @abstractmethod
    def build(self, df: pd.DataFrame, spec: ChartSpec) -> Figure:
        """DataFrame과 설정을 받아 Plotly Figure를 반환한다."""

    def _validate_spec(self, spec: ChartSpec) -> None:
        """차트 종류별로 공통 설정을 검증하고 잘못된 설정은 예외로 알린다.

        데이터 컬럼 유무, 값의 자료형 등 데이터 의존 검증은 구체적인 빌더가 담당한다.
        """
        if not isinstance(spec, ChartSpec):
            raise ChartRenderError("차트 설정은 ChartSpec이어야 합니다.")
        if spec.chart_type not in ("bar", "pie", "table"):
            raise ChartRenderError(f"지원하지 않는 차트 종류입니다: {spec.chart_type!r}")
        if spec.chart_type == "bar":
            if not isinstance(spec.x, str) or not spec.x:
                raise ChartRenderError("막대 차트에는 x 범주 컬럼명이 필요합니다.")
            if spec.orientation not in ("v", "h"):
                raise ChartRenderError("orientation은 'v' 또는 'h'여야 합니다.")
            if spec.agg_func not in (None, "sum", "mean", "count", "min", "max"):
                raise ChartRenderError("지원하지 않는 agg_func입니다.")
        elif spec.chart_type == "pie":
            if not (isinstance(spec.x, str) and spec.x) and not (
                isinstance(spec.color, str) and spec.color
            ):
                raise ChartRenderError("도넛 차트에는 x 또는 color 범주 컬럼명이 필요합니다.")
            if spec.y is not None and not isinstance(spec.y, str):
                raise ChartRenderError("도넛 차트의 y는 숫자 컬럼명 하나여야 합니다.")
        # 표는 x/y 없는 ChartSpec(chart_type='table')도 허용한다.

    def _apply_theme(self, fig: Figure) -> Figure:
        """ThemeConfig를 Plotly Figure에 적용한 뒤 같은 Figure를 돌려준다.

        가변 설정을 쓰지 않으며, TableBuilder가 정한 표 여백·셀 색상은 보존한다.
        """
        if not isinstance(fig, Figure):
            raise ChartRenderError("테마를 적용할 대상은 Plotly Figure여야 합니다.")

        mode = getattr(self.theme, "mode", "light")
        template = getattr(self.theme, "chart_template", "plotly_white") or "plotly_white"
        # ThemeConfig.for_mode('dark')가 아직 mode 필드만 바꾸므로 보완한다.
        if mode == "dark" and template == "plotly_white":
            template = "plotly_dark"

        font_family = getattr(self.theme, "font_family", "sans-serif") or "sans-serif"
        palette = getattr(self.theme, "palette", None)
        primary_color = getattr(self.theme, "primary_color", "#1f77b4")
        settings = {
            "template": template,
            "font_family": font_family,
        }
        if palette:
            settings["colorway"] = list(palette)
        if primary_color:
            settings["title_font_color"] = primary_color
        fig.update_layout(**settings)
        return fig
