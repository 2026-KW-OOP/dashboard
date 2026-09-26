"""좌측 사이드바: 파일 업로드·필터·설정."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from dashboard.models.dataset import Dataset
from dashboard.services.filter import FilterCondition


@dataclass
class SidebarState:
    uploaded_file: Optional[Any] = None
    selected_sheet: Optional[str] = None
    filters: list[FilterCondition] = field(default_factory=list)
    theme_mode: str = "light"


class SidebarComponent:
    def render(self, dataset: Optional[Dataset], sheets: Optional[List[str]] = None) -> SidebarState:
        """사이드바 위젯을 그리고 사용자 입력을 반환한다.

        입력: dataset — 현재 로드된 데이터(아직 없으면 None, 이 경우 필터
              위젯은 그리지 않음). sheets — 방금 업로드된 파일의 시트 목록
              (아직 없으면 None, 이 경우 시트 선택 위젯은 그리지 않음).
        동작: 파일 업로더 → (sheets가 있으면) 시트 선택 → (dataset이 있으면)
              컬럼별 필터 위젯 → 테마 토글 순서로 그리고, 각 위젯의 반환값을 모은다.
        반환: 이번 렌더링 시점에 사용자가 고른 값들을 담은 SidebarState
              (업로드 파일, 선택 시트, 필터 목록, 테마 모드).
        """
        import streamlit as st

        st.sidebar.title("⚙️ 설정")
        uploaded_file = self._render_file_uploader()
        selected_sheet = self._render_sheet_selector(sheets) if sheets else None
        filters = self._render_filters(dataset) if dataset is not None else []
        theme_mode = self._render_theme_toggle()

        return SidebarState(
            uploaded_file=uploaded_file,
            selected_sheet=selected_sheet,
            filters=filters,
            theme_mode=theme_mode,
        )

    def _render_file_uploader(self) -> Optional[Any]:
        """업로드 UI.

        입력: 없음.
        동작: st.sidebar.file_uploader로 업로드 위젯을 그린다.
        반환: 사용자가 올린 파일 객체(Streamlit의 UploadedFile, ExcelLoader.load()에
              그대로 넘길 수 있는 BytesIO 호환 객체). 아무것도 안 올렸으면 None.
        """
        import streamlit as st

        return st.sidebar.file_uploader("엑셀/CSV 파일 업로드", type=["xlsx", "xls", "csv"])

    def _render_sheet_selector(self, sheets: list[str]) -> Optional[str]:
        """시트 선택 드롭다운.

        입력: sheets — ExcelLoader.list_sheets()가 반환한 시트 이름 리스트.
        동작: st.sidebar.selectbox로 드롭다운을 그린다.
        반환: 사용자가 고른 시트명(str). sheets가 비어 있으면 None.
        """
        import streamlit as st

        return st.sidebar.selectbox("시트 선택", sheets)

    def _render_filters(self, dataset: Dataset) -> list[FilterCondition]:
        """컬럼별 필터 위젯을 동적으로 생성한다 (미구현, 아직 필터 없음).

        입력: dataset — dataset.df.select_dtypes(...)로 "이 컬럼에 어떤
              위젯을 그릴지" 직접 판단할 대상 (숫자/범주/날짜 dtype 확인).
        동작(완성판 기준): 숫자 컬럼 → st.slider(범위), 범주 컬럼 →
              st.multiselect(dataset.get_unique_values(col)로 얻은 값 목록),
              날짜 컬럼 → date range picker를 그리고, 사용자가 실제로 값을
              바꾼 컬럼만 FilterCondition으로 변환한다.
        반환: FilterCondition 리스트 (사용자가 아무 필터도 안 건드리면 빈 리스트).
              이 값이 DataFilter.apply()의 filters 인자로 그대로 들어간다.
        """
        return []

    def _render_theme_toggle(self) -> str:
        """라이트/다크 모드 전환.

        입력: 없음.
        동작: st.sidebar.radio로 두 모드 중 하나를 고르게 한다.
        반환: "light" 또는 "dark". SidebarState.theme_mode에 담기고,
              추후 ThemeConfig.for_mode()로 이어질 값이다.
        """
        import streamlit as st

        return st.sidebar.radio("테마", ["light", "dark"], horizontal=True)
