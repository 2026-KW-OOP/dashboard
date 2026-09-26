"""사이드바 필터 조건을 DataFrame에 적용한다."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

FilterOperator = Literal["in", "contains"]


@dataclass(frozen=True)
class FilterCondition:
    column: str
    operator: FilterOperator
    value: Any


class DataFilter:
    def apply(self, df: pd.DataFrame, filters: list[FilterCondition]) -> pd.DataFrame:
        """모든 필터를 순차 적용한다 (미구현, 원본 반환).

        입력: df — 필터링 대상 DataFrame. filters — 사이드바에서 사용자가
              설정한 FilterCondition 리스트 (여러 개면 AND 조건).
        동작: filters를 하나씩 순회하며 operator("in"/"contains")에 맞는
              filter_by_categories/filter_by_search로 위임해 df를 누적으로
              좁혀나간다. ("range" 연산자는 filter_by_range가 제거되어
              현재는 처리되지 않는다 — 필요해지면 다시 추가.)
        반환: 모든 조건을 통과한 행만 남은 DataFrame (필터가 없으면 원본과 동일).
        """
        return df.copy()

    def filter_by_categories(self, df: pd.DataFrame, column: str, values: list[Any]) -> pd.DataFrame:
        """다중 선택 필터 (미구현, 원본 반환).

        입력: df — 대상 DataFrame. column — 범주형 컬럼명.
              values — 사용자가 멀티셀렉트로 고른 값 목록 (예: ["서울", "부산"]).
        동작: column 값이 values 중 하나와 일치하는 행만 남긴다 (OR 조건).
        반환: 조건을 만족하는 행만 남은 DataFrame.
        """
        return df.copy()

    def filter_by_search(self, df: pd.DataFrame, column: str, keyword: str) -> pd.DataFrame:
        """문자열 부분 일치 (미구현, 원본 반환).

        입력: df — 대상 DataFrame. column — 문자열 컬럼명.
              keyword — 사용자가 입력한 검색어.
        동작: column 값에 keyword가 (대소문자 무시하고) 부분적으로
              포함된 행만 남긴다.
        반환: 조건을 만족하는 행만 남은 DataFrame.
        """
        return df.copy()
