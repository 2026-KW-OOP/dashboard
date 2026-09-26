"""정제·전처리."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd


class DataCleaner:
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """정제 파이프라인을 실행한다 (미구현, 원본 반환).

        입력: df — SheetParser.parse()를 거쳐 헤더·인덱스는 정리됐지만
              컬럼명 형식·타입·결측치·중복은 아직 손대지 않은 DataFrame.
        동작: normalize_column_names → handle_missing
              → remove_duplicates 를 이 순서로 누적 호출한다.
        반환: 위 4단계를 모두 거쳐 분석·시각화에 바로 쓸 수 있는 DataFrame.
        """
        return df.copy()

    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """공백·특수문자 제거, snake_case 변환 (미구현, 원본 반환).

        입력: df — 컬럼명에 공백·특수문자·대소문자가 섞여 있을 수 있는 DataFrame
              (예: "매출 금액 (원)", "Sales Amount").
        동작: 각 컬럼명을 소문자/snake_case 형태로 통일한다
              (예: "Sales Amount" → "sales_amount").
        반환: 컬럼명만 바뀌고 값(데이터)은 그대로인, 동일한 shape의 DataFrame.
        """
        return df.copy()

    def handle_missing(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """결측치 처리 (drop, fill_zero, fill_mean 등) (미구현, 원본 반환).

        입력: df — NaN/빈 값이 섞여 있을 수 있는 DataFrame.
              strategy — "drop"(결측 행 제거) | "fill_zero"(0으로 채움)
              | "fill_mean"(컬럼 평균으로 채움) 중 하나.
        동작: strategy에 맞는 방식으로 결측치를 제거하거나 채운다.
        반환: strategy가 "drop"이면 행 수가 줄어들고, 그 외에는 shape은
              같지만 결측치가 없는 DataFrame.
        """
        return df.copy()

    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """중복 제거 (미구현, 원본 반환).

        입력: df — 중복 행이 있을 수 있는 DataFrame.
              subset — 중복 판단 기준 컬럼 목록 (None이면 모든 컬럼 값이 같아야 중복으로 판단).
        동작: subset 기준으로 완전히 같은 첫 번째 행만 남기고 이후 중복 행을 제거한다.
        반환: 중복이 제거되어 행 수가 같거나 줄어든 DataFrame.
        """
        return df.copy()
