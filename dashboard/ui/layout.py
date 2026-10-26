"""전체 페이지 배치 관리."""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

import pandas as pd

from dashboard.models.dataset import Dataset
from dashboard.services.filter import DataFilter, FilterCondition
from dashboard.ui.filter_bar import FilterBar
from dashboard.ui.metrics import ColumnMap, MetricsCalculator
from dashboard.ui.sidebar import SidebarState
from dashboard.ui.style import PageStyle
from dashboard.utils.exceptions import ChartRenderError, EmptyDatasetError
from dashboard.visualization.builders import ChartSpec
from dashboard.visualization.factory import ChartFactory


class PageLayout:
    BAR_TOP_N = 10
    PIE_TOP_N = 6

    def __init__(
        self,
        data_filter: DataFilter,
        chart_factory: ChartFactory,
        metrics: Optional[MetricsCalculator] = None,
        filter_bar: Optional[FilterBar] = None,
        style: Optional[PageStyle] = None,
    ) -> None:
        self.data_filter = data_filter
        self.chart_factory = chart_factory
        self.metrics = metrics or MetricsCalculator(ColumnMap())
        self.filter_bar = filter_bar or FilterBar(self.metrics.columns)
        self.style = style or PageStyle()
        self.mode = "light"

    def render(self, dataset: Optional[Dataset], sidebar_state: SidebarState) -> None:
        """헤더·본문·푸터를 조립한다.

        입력: dataset — 파일이 아직 없으면 None. sidebar_state — 사이드바에서
              모인 설정(SidebarState). 필터는 이 메서드 안에서 FilterBar가 받아 채운다.
        동작: 스타일을 입히고, 왼쪽에 제목·오른쪽 위에 필터를 그린다. dataset이 None이면
              안내 화면만 보여준 뒤 끝낸다. 있으면 필터를 적용해 요약 카드와 차트를 그린다.
        반환: None (화면을 그리는 부수효과만 있음).
        """
        import streamlit as st

        self.mode = sidebar_state.theme_mode
        self.style.inject(self.mode)

        has_data = dataset is not None and not dataset.df.empty
        title_slot, filter_slot = st.columns([5, 4], vertical_alignment="bottom")
        with title_slot:
            self._render_header(dataset)

        filters: list[FilterCondition] = []
        if has_data:
            with filter_slot:
                filters = self.filter_bar.render(dataset)
        sidebar_state = replace(sidebar_state, filters=filters)

        if dataset is None:
            self._render_empty_state()
            return
        if not has_data:
            st.warning("표시할 데이터가 없어요. 파일 내용이나 시트를 확인해 주세요.")
            return

        filtered = self._apply_filters(dataset.df, sidebar_state.filters)
        if filtered.empty:
            st.warning("선택한 조건에 해당하는 가맹점이 없어요. 필터를 바꿔 보세요.")
            return

        self._render_kpi_cards(filtered)
        self._render_charts(filtered)

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
        st.plotly_chart(fig, width="stretch")

    def _apply_filters(self, df: pd.DataFrame, filters: list[FilterCondition]) -> pd.DataFrame:
        try:
            return self.data_filter.apply(df, filters)
        except EmptyDatasetError:
            return df.iloc[0:0]

    def _render_kpi_cards(self, df: pd.DataFrame) -> None:
        import streamlit as st

        summary = self.metrics.summarize(df)
        columns = self.metrics.columns

        total_card = self.style.kpi_card("전체 가맹점 수", f"{summary.total:,}개", "필터에 해당하는 가맹점", primary=True)

        if summary.top_district is not None:
            top = summary.top_district
            district_card = self.style.kpi_card(
                f"가맹점이 가장 많은 {columns.district}",
                top.name,
                f"{top.count:,}개 (선택 범위의 {top.ratio:.1%})",
            )
        else:
            district_card = self.style.kpi_card(f"가맹점이 가장 많은 {columns.district}", "-", f"'{columns.district}' 컬럼 없음")

        if summary.top_category is not None:
            top = summary.top_category
            category_card = self.style.kpi_card("가장 큰 비율의 업종", top.name, f"선택 범위의 {top.ratio:.1%}")
        else:
            category_card = self.style.kpi_card("가장 큰 비율의 업종", "-", f"'{columns.category}' 컬럼 없음")

        for slot, card in zip(st.columns(3), (total_card, district_card, category_card)):
            slot.markdown(card, unsafe_allow_html=True)

    def _render_charts(self, df: pd.DataFrame) -> None:
        import streamlit as st

        columns = self.metrics.columns
        count_column = self.metrics.COUNT_COLUMN

        district_table = self.metrics.count_by(df, columns.district, top_n=self.BAR_TOP_N)
        category_table = self.metrics.count_by(df, columns.category, top_n=self.PIE_TOP_N, merge_rest=True)

        bar_spec = ChartSpec(
            chart_type="bar",
            x=columns.district,
            y=count_column,
            title=f"{columns.district}별 가맹점 현황",
            orientation="h",
        )
        pie_spec = ChartSpec(
            chart_type="pie",
            x=columns.category,
            y=count_column,
            title=f"{columns.category}별 가맹점 비율",
        )

        bar_slot, pie_slot = st.columns([3, 2])
        with bar_slot:
            with st.container(border=True):
                self._render_chart(district_table, bar_spec)
        with pie_slot:
            with st.container(border=True):
                self._render_chart(category_table, pie_spec)

    def _render_chart(self, table: pd.DataFrame, spec: ChartSpec) -> None:
        import streamlit as st

        if table.empty:
            st.info(f"'{spec.x}' 컬럼이 없거나 그릴 데이터가 없어요.")
            return

        try:
            figure = self.chart_factory.create(spec).build(table, spec)
        except (KeyError, ChartRenderError) as error:
            st.error(f"차트를 만들지 못했어요: {error}")
            return

        if len(figure.data) == 0:
            st.info(f"'{spec.title}' 차트 빌더가 아직 그림을 그리지 않았어요. (시각화 담당 구현 필요)")
            return

        self.style.style_figure(figure, self.mode)
        st.plotly_chart(figure, width="stretch", theme=None)
