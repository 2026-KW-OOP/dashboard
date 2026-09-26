"""시각적 테마 정의."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThemeConfig:
    """컬러 팔레트, 폰트, 차트 기본 스타일. 모든 ChartBuilder가 참조한다."""

    primary_color: str = "#1f77b4"
    palette: list[str] = field(default_factory=list)
    font_family: str = "sans-serif"
    chart_template: str = "plotly_white"
    mode: str = "light"

    @classmethod
    def for_mode(cls, mode: str) -> "ThemeConfig":
        """라이트/다크 모드에 맞는 테마를 반환한다.

        입력: mode — "light" 또는 "dark" (SidebarComponent._render_theme_toggle()의
              반환값).
        동작: mode에 맞는 palette/chart_template 조합(예: dark면
              chart_template="plotly_dark")으로 ThemeConfig를 만든다.
        반환: 해당 모드의 ThemeConfig 인스턴스.
              (지금은 palette/chart_template은 그대로 두고 mode 필드만 반영.)
        """
        return cls(mode=mode)
