"""코랄핑크 톤 화면 스타일과 요약 카드 HTML (라이트/다크)."""
from __future__ import annotations

from html import escape


class PageStyle:
    TOKENS = {
        "light": {
            "bg": "#FFF6F4",
            "surface": "#FFFFFF",
            "ink": "#3A2626",
            "sub": "#7A5F5C",
            "line": "#F3DAD6",
            "primary": "#C9443F",
            "on_primary": "#FFFFFF",
            "on_primary_sub": "#FFE6E2",
            "accent": "#F0685F",
            "field": "#F6ECEA",
        },
        "dark": {
            "bg": "#1E1415",
            "surface": "#2A1D1E",
            "ink": "#FBEDEA",
            "sub": "#C9A9A5",
            "line": "#4A3336",
            "primary": "#D4524C",
            "on_primary": "#FFFFFF",
            "on_primary_sub": "#FFE6E2",
            "accent": "#F68279",
            "field": "#3A2A2C",
        },
    }

    def tokens(self, mode: str) -> dict[str, str]:
        return self.TOKENS.get(mode, self.TOKENS["light"])

    def inject(self, mode: str) -> None:
        import streamlit as st

        st.markdown(self._css(self.tokens(mode)), unsafe_allow_html=True)

    def style_figure(self, figure, mode: str):
        t = self.tokens(mode)
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=t["ink"],
            legend_font_color=t["ink"],
        )
        for update_axes in (figure.update_xaxes, figure.update_yaxes):
            update_axes(
                gridcolor=t["line"],
                zerolinecolor=t["line"],
                linecolor=t["line"],
                tickfont_color=t["sub"],
                title_font_color=t["sub"],
            )
        return figure

    def kpi_card(self, label: str, value: str, sub: str, primary: bool = False) -> str:
        css_class = "kpi-card primary" if primary else "kpi-card"
        return (
            f'<div class="{css_class}">'
            f'<div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value">{escape(value)}</div>'
            f'<div class="kpi-sub">{escape(sub)}</div>'
            "</div>"
        )

    def _css(self, t: dict[str, str]) -> str:
        return f"""
<style>
.stApp {{ background: {t['bg']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {t['surface']}; }}
.stApp h1 {{ color: {t['primary']}; font-size: 1.9rem; word-break: keep-all; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: {t['surface']}; border-color: {t['line']}; border-radius: 14px; }}
.stApp h2, .stApp h3 {{ color: {t['primary']}; }}
[data-testid="stSidebar"] h1 {{ color: {t['ink']}; font-size: 1.6rem; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ color: {t['sub']}; }}
[data-testid="stWidgetLabel"] p, [data-testid="stRadio"] label p {{ color: {t['sub']}; }}
[data-testid="stRadio"] label p {{ color: {t['ink']}; }}
[data-testid="stMultiSelect"] [role="group"], [data-testid="stSelectbox"] [role="group"] {{ background: {t['field']}; }}
[data-testid="stMultiSelect"] input, [data-testid="stSelectbox"] input {{ color: {t['ink']}; }}
[data-testid="stFileUploaderDropzone"] {{ background: {t['field']}; }}
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileChip"] * {{ color: {t['ink']}; }}
[data-testid="stFileChip"] {{ background: {t['field']}; border-radius: 8px; }}
.kpi-card {{
    background: {t['surface']};
    border: 1px solid {t['line']};
    border-radius: 14px;
    padding: 18px 20px;
    height: 100%;
}}
.kpi-card.primary {{ background: {t['primary']}; border-color: {t['primary']}; }}
.kpi-label {{ font-size: 0.9rem; color: {t['sub']}; }}
.kpi-value {{ font-size: 2.1rem; font-weight: 700; color: {t['ink']}; margin: 6px 0 2px; }}
.kpi-sub {{ font-size: 0.82rem; color: {t['sub']}; }}
.kpi-card.primary .kpi-label, .kpi-card.primary .kpi-sub {{ color: {t['on_primary_sub']}; }}
.kpi-card.primary .kpi-value {{ color: {t['on_primary']}; }}
</style>
"""
