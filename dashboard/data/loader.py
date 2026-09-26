"""Excel/CSV 파일을 원시 DataFrame으로 읽는다. 검증·정제는 하지 않는다."""
from __future__ import annotations

from io import BytesIO
from typing import Union

import pandas as pd

from dashboard.config.settings import AppConfig

FileSource = Union[str, BytesIO]


class ExcelLoader:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def load(self, file_path: FileSource) -> dict[str, pd.DataFrame]:
        """모든 시트를 {시트명: DataFrame}으로 반환한다 (미구현).

        입력: file_path — 로컬 파일 경로(str) 또는 업로드된 파일의 바이트 스트림(BytesIO).
        동작: _detect_format()으로 xlsx/xls/csv 여부를 먼저 판정하고,
              결과에 따라 _read_excel() 또는 _read_csv()로 위임한다.
        반환: {시트명: DataFrame} 딕셔너리. CSV처럼 시트 개념이 없는 포맷은
              단일 키(예: "Sheet1")로 감싸서 반환한다.
        """
        return {}

    def list_sheets(self, file_path: FileSource) -> list[str]:
        """시트 목록만 미리 조회한다 (미구현).

        입력: file_path — load()와 동일.
        동작: 전체 데이터를 읽지 않고 워크북 메타정보만 열어 시트 이름들을 확인한다
              (예: openpyxl로 열되 data_only 없이 sheet_names만 조회).
        반환: 시트 이름 리스트. UI의 "시트 선택" 드롭다운([ui/sidebar.py](../ui/sidebar.py))에
              바로 넘겨질 값이다.
        """
        return []

    def _detect_format(self, file_path: FileSource) -> str:
        """확장자·매직바이트로 포맷을 판정한다 (미구현).

        입력: file_path — load()와 동일.
        동작: 파일 확장자(.xlsx/.xls/.csv)를 우선 확인하고, 확장자가 없거나
              신뢰할 수 없는 경우(예: 업로드 스트림) 매직바이트로 재확인한다.
        반환: "xlsx" | "xls" | "csv" 중 하나. 지원하지 않는 포맷이면
              utils/exceptions.py의 InvalidFileFormatError를 발생시켜야 한다.
        """
        return ""

    def _read_excel(self, file_path: FileSource) -> dict[str, pd.DataFrame]:
        """openpyxl 엔진 기반 실제 읽기 (미구현).

        입력: file_path — _detect_format()이 "xlsx"/"xls"로 판정한 파일.
        동작: pandas.read_excel(file_path, sheet_name=None, engine="openpyxl")처럼
              모든 시트를 한 번에 읽는다.
        반환: {시트명: DataFrame}. 각 DataFrame은 아직 헤더 위치나 타입이
              정리되지 않은 원시 상태 그대로다 (그건 SheetParser/DataCleaner의 몫).
        """
        return {}

    def _read_csv(self, file_path: FileSource) -> dict[str, pd.DataFrame]:
        """인코딩·구분자 자동 탐지 후 CSV 읽기 (미구현).

        입력: file_path — _detect_format()이 "csv"로 판정한 파일.
        동작: 인코딩(utf-8, cp949 등)과 구분자(",", ";", tab)를 자동 탐지해
              pandas.read_csv(...)로 읽는다.
        반환: CSV는 시트 개념이 없으므로 {"Sheet1": DataFrame} 형태로,
              load()의 반환 형식({시트명: DataFrame})과 통일해서 감싸 반환한다.
        """
        return {}
