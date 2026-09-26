"""로드된 시트에서 헤더·데이터 영역을 식별한다."""
from __future__ import annotations

import pandas as pd


class SheetParser:
    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """빈 행/열 제거, 헤더 행 탐지, 인덱스 정규화 (미구현, 원본 반환).

        입력: df — ExcelLoader가 읽어온 원시 시트 하나. 제목 행, 빈 행,
              병합 셀의 흔적 등이 위쪽에 남아있을 수 있다.
        동작: detect_header_row()로 실제 헤더가 시작되는 행을 찾고,
              strip_metadata_rows()로 그 위의 메타데이터 행들을 제거한 뒤
              인덱스를 0부터 다시 매긴다.
        반환: 첫 행이 실제 컬럼명이고 인덱스가 0..n-1로 정리된 DataFrame.
        """
        return df.copy()

    def detect_header_row(self, df: pd.DataFrame) -> int:
        """실제 헤더가 시작되는 행 번호를 반환한다 (미구현).

        입력: df — parse()에 들어온 원시 시트.
        동작: 위에서부터 각 행을 검사하며, "값 대부분이 문자열이고 그 아래
              행들이 일관된 데이터 타입 패턴을 보이는" 첫 행을 헤더로 판단한다.
        반환: 헤더 행의 0-indexed 행 번호. 판단 실패 시 0(첫 행을 헤더로 가정).
        """
        return 0

    def strip_metadata_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """상단 메타데이터(제목·설명 등)를 제거한다 (미구현, 원본 반환).

        입력: df — 원시 시트, detect_header_row()가 찾은 헤더 행 번호를 함께 참고.
        동작: 헤더 행보다 위에 있는, 문서 제목·작성일 같은 메타데이터 행들을
              잘라낸다.
        반환: 메타데이터 행이 제거되어 행 수가 줄어든 DataFrame
              (헤더 이후 데이터는 그대로 유지).
        """
        return df.copy()
