"""전체 페이지 배치 관리."""
from __future__ import annotations

from typing import Optional

from dashboard.models.dataset import Dataset
from dashboard.ui.sidebar import SidebarState


class PageLayout:

    def render(self, dataset: Optional[Dataset], sidebar_state: SidebarState) -> None:
        """헤더·본문·푸터를 조립한다.

        입력: dataset — 파일이 아직 없으면 None. sidebar_state — 사이드바에서
              모인 필터·설정(SidebarState, .filters를 각 Page에 그대로 전달).
        동작: 헤더를 그리고, dataset이 None이면 안내 화면만 보여준 뒤 끝낸다.
              dataset이 있으면 dataset을 표현하는 화면을 그린다.
        반환: None (화면을 그리는 부수효과만 있음).
        """
        self._render_header(dataset)

        if dataset is None:
            self._render_empty_state()
            return

    def _render_header(self, dataset: Optional[Dataset]) -> None:
        """파일명·마지막 업데이트 시간 표시.

        입력: dataset — 있으면 dataset.source_file/loaded_at을 표시에 쓴다.
        동작: 페이지 제목을 그리고, dataset이 있으면 그 아래 캡션으로
              파일명과 로드 시각을 덧붙인다.
        반환: None.
        """
        import streamlit as st

        st.title("📊 서울사랑상품권 가맹점 현황 시각화 대시보드")
        if dataset is not None:
            st.caption(f"파일: {dataset.source_file} · 로드 시각: {dataset.loaded_at:%Y-%m-%d %H:%M:%S}")

    def _render_empty_state(self) -> None:
        """파일 미업로드 시 안내 화면. 예시로 샘플 차트를 보여준다.

        입력: 없음.
        동작: 안내 문구를 띄우고, 실제 데이터 대신 하드코딩된 샘플
              DataFrame으로 예시 막대 차트를 그려 "차트가 이렇게 보인다"를
              시연한다.
        반환: None.
        """
        import pandas as pd
        import plotly.express as px
        import streamlit as st

        st.info("왼쪽 사이드바에서 엑셀 파일을 업로드하면 대시보드가 표시됩니다.")
        st.caption("아래는 실제 데이터 대신 보여주는 예시 차트입니다 (샘플 데이터).")

        sample = pd.DataFrame({"월": ["1월", "2월", "3월", "4월"], "매출": [120, 150, 90, 200]})
        fig = px.bar(sample, x="월", y="매출", title="예시 매출 차트")
        st.plotly_chart(fig, use_container_width=True)
