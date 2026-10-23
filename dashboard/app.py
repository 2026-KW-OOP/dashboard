"""애플리케이션 진입점.

실행: python3 -m dashboard.app                          (임시 확인용, run()은 최소 배선만 수행)
     python3 -m streamlit run dashboard/app.py           (저장소 루트에서, 실제 웹앱)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import pandas as pd

from dashboard.config.settings import AppConfig
from dashboard.config.theme import ThemeConfig
from dashboard.data.cleaner import DataCleaner
from dashboard.data.loader import ExcelLoader
from dashboard.data.parser import SheetParser
from dashboard.data.validator import DataValidator
from dashboard.models.dataset import Dataset
from dashboard.services.filter import DataFilter
from dashboard.ui.filter_bar import FilterBar
from dashboard.ui.layout import PageLayout
from dashboard.ui.metrics import ColumnMap, MetricsCalculator
from dashboard.ui.sidebar import SidebarComponent
from dashboard.ui.style import PageStyle
from dashboard.utils.exceptions import DashboardError
from dashboard.visualization.factory import ChartFactory

SHEETS_FILE_KEY = "sheets_file_key"
SHEET_NAMES_KEY = "sheet_names"
DATASET_KEY = "dataset_key"
DATASET_VALUE = "dataset_value"


class DashboardApp:
    def __init__(self, config: AppConfig) -> None:
        """의존성 조립 (DI 컨테이너 역할).

        입력: config — 업로드 크기 제한, 캐시 TTL 등을 담은 AppConfig.
        동작: 계층별로 필요한 객체를 만들고, 상위 계층(Page)에는 그 Page가
              실제로 쓸 서비스/시각화 객체만 생성자로 주입한다.
        반환: 없음 (self.* 속성들로 조립 결과를 보관).
        """
        self.config = config
        self.theme = ThemeConfig()
        self.columns = ColumnMap()

        self.loader = ExcelLoader(config)
        self.parser = SheetParser()
        self.validator = DataValidator()
        self.cleaner = DataCleaner()

        self.data_filter = DataFilter()

        self.chart_factory = ChartFactory(self.theme)

        self.metrics = MetricsCalculator(self.columns)
        self.sidebar = SidebarComponent()
        self.layout = PageLayout(
            data_filter=self.data_filter,
            chart_factory=self.chart_factory,
            metrics=self.metrics,
            filter_bar=FilterBar(self.columns),
            style=PageStyle(),
        )

    def run(self) -> None:
        """앱 실행 루프.

        입력: 없음.
        동작: 페이지 설정 → 사이드바 렌더(업로드 위젯 포함) → 테마 반영
              → 파일이 올라왔으면 _handle_file_upload()로 파이프라인 실행
              → 그 결과(dataset)와 sidebar_state를 layout에 넘겨 최종 렌더.
        반환: None. streamlit run으로 실행될 때마다(상호작용마다) 이 메서드가
              다시 처음부터 호출된다.
        """
        import streamlit as st

        st.set_page_config(page_title="서울사랑상품권 가맹점 현황 대시보드", page_icon="📊", layout="wide")

        sidebar_state = self.sidebar.render(None, st.session_state.get(SHEET_NAMES_KEY))
        self._apply_theme(sidebar_state.theme_mode)

        dataset = None
        if sidebar_state.uploaded_file is not None:
            self._remember_sheets(sidebar_state.uploaded_file)
            dataset = self._handle_file_upload(sidebar_state.uploaded_file, sidebar_state.selected_sheet)
        else:
            self._forget_file()

        self.layout.render(dataset, sidebar_state)

    def _handle_file_upload(self, file: Any, sheet: Optional[str] = None) -> Dataset:
        """업로드 → Loader → Parser → Validator → Cleaner → Dataset 파이프라인을 조율한다.

        입력: file — 사용자가 사이드바에서 올린 파일 객체(UploadedFile/BytesIO).
              sheet — 사용자가 고른 시트명(없으면 첫 시트 사용).
        동작: self.loader.load(file) → self.parser.parse(고른 시트)
              → self.validator.validate(...)(실패 시 st.error로 안내) →
              self.cleaner.clean(...) 순서로 실행해 최종 DataFrame을 만든다.
              성공한 결과는 같은 파일·시트에 대해 session_state에 보관해 재사용한다.
        반환: 파이프라인 결과(df)와 파일명, 로드 시각을 담은 Dataset.
              실패하면 빈 DataFrame으로 채운 Dataset을 반환한다.
        """
        import streamlit as st

        file_name = getattr(file, "name", "")
        cache_key = (self._file_key(file), sheet)
        if st.session_state.get(DATASET_KEY) == cache_key:
            return st.session_state[DATASET_VALUE]

        try:
            self._rewind(file)
            tables = self.loader.load(file)
            if not tables:
                st.warning("파일에서 읽을 수 있는 시트가 없어요.")
                return self._empty_dataset(file_name)

            sheet_names = list(tables)
            if sheet in tables:
                chosen = sheet
            else:
                chosen = sheet_names[min(self.config.default_sheet_index, len(sheet_names) - 1)]

            parsed = self.parser.parse(tables[chosen])

            result = self.validator.validate(parsed)
            for message in result.warnings:
                st.warning(message)
            if not result.is_valid:
                for message in result.errors:
                    st.error(message)
                return self._empty_dataset(file_name)

            cleaned = self.cleaner.clean(parsed)
        except DashboardError as error:
            st.error(str(error))
            return self._empty_dataset(file_name)

        dataset = Dataset(df=cleaned, source_file=file_name, loaded_at=datetime.now())
        st.session_state[DATASET_KEY] = cache_key
        st.session_state[DATASET_VALUE] = dataset
        return dataset

    def _apply_theme(self, mode: str) -> None:
        self.theme = ThemeConfig.for_mode(mode)
        self.chart_factory.theme = self.theme

    def _remember_sheets(self, file: Any) -> None:
        import streamlit as st

        file_key = self._file_key(file)
        if st.session_state.get(SHEETS_FILE_KEY) == file_key:
            return

        self._rewind(file)
        try:
            names = self.loader.list_sheets(file)
        except DashboardError:
            names = []
        self._rewind(file)

        st.session_state[SHEETS_FILE_KEY] = file_key
        st.session_state[SHEET_NAMES_KEY] = names
        if len(names) > 1:
            st.rerun()

    def _forget_file(self) -> None:
        import streamlit as st

        for key in (SHEETS_FILE_KEY, SHEET_NAMES_KEY, DATASET_KEY, DATASET_VALUE):
            st.session_state.pop(key, None)

    def _file_key(self, file: Any) -> tuple:
        return (getattr(file, "name", ""), getattr(file, "size", None))

    def _rewind(self, file: Any) -> None:
        seek = getattr(file, "seek", None)
        if callable(seek):
            seek(0)

    def _empty_dataset(self, file_name: str) -> Dataset:
        return Dataset(df=pd.DataFrame(), source_file=file_name, loaded_at=datetime.now())


def main() -> None:
    DashboardApp(AppConfig()).run()


if __name__ == "__main__":
    main()
