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
from dashboard.ui.layout import PageLayout
from dashboard.ui.sidebar import SidebarComponent
from dashboard.visualization.factory import ChartFactory


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

        # Data layer
        self.loader = ExcelLoader(config)
        self.parser = SheetParser()
        self.validator = DataValidator()
        self.cleaner = DataCleaner()

        # Service layer
        self.data_filter = DataFilter()

        # Visualization layer
        self.chart_factory = ChartFactory(self.theme)

        # Presentation layer
        self.sidebar = SidebarComponent()
        self.layout = PageLayout()

    def run(self) -> None:
        """앱 실행 루프.

        입력: 없음.
        동작: 페이지 설정 → 사이드바 렌더(업로드 위젯 포함)
              → 파일이 올라왔으면 _handle_file_upload()로 파이프라인 실행
              → 그 결과(dataset)와 sidebar_state를 layout에 넘겨 최종 렌더.
        반환: None. streamlit run으로 실행될 때마다(상호작용마다) 이 메서드가
              다시 처음부터 호출된다.
        """
        import streamlit as st

        st.set_page_config(page_title="서울사랑상품권 가맹점 현황 대시보드", page_icon="📊", layout="wide")

        sidebar_state = self.sidebar.render(None)

        dataset = None
        if sidebar_state.uploaded_file is not None:
            dataset = self._handle_file_upload(sidebar_state.uploaded_file, sidebar_state.selected_sheet)

        self.layout.render(dataset, sidebar_state)

    def _handle_file_upload(self, file: Any, sheet: Optional[str] = None) -> Dataset:
        """업로드 → Loader → Parser → Validator → Cleaner → Dataset 파이프라인을 조율한다 (미구현, 빈 Dataset 반환).

        입력: file — 사용자가 사이드바에서 올린 파일 객체(UploadedFile/BytesIO).
              sheet — 사용자가 고른 시트명(없으면 첫 시트 사용).
        동작(완성판 기준): self.loader.load(file) → self.parser.parse(원하는 시트)
              → self.validator.validate(...)(실패 시 st.error로 안내) →
              self.cleaner.clean(...) 순서로 실행해 최종 DataFrame을 만든다.
        반환: 위 파이프라인 결과(df)와 추론된 schema, 파일명, 로드 시각을 담은
              Dataset. 지금은 빈 DataFrame으로 채운 Dataset을 반환.
        """
        return Dataset(df=pd.DataFrame(), source_file="", loaded_at=datetime.now())


def main() -> None:
    DashboardApp(AppConfig()).run()


if __name__ == "__main__":
    main()
