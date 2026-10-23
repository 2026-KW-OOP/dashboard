"""화면 오른쪽 위 필터 영역 (자치구·업종 등 범주형 컬럼 다중 선택)."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from dashboard.models.dataset import Dataset
from dashboard.services.filter import FilterCondition
from dashboard.ui.metrics import ColumnMap


class FilterBar:
    MAX_AUTO_COLUMNS = 2
    MAX_AUTO_UNIQUE = 40

    def __init__(self, columns: Optional[ColumnMap] = None) -> None:
        self.columns = columns or ColumnMap()

    def render(self, dataset: Dataset) -> list[FilterCondition]:
        """필터 위젯을 그리고 사용자가 고른 조건을 반환한다.

        입력: dataset — 필터 선택지(get_unique_values)를 뽑을 데이터.
        동작: 자치구·업종 컬럼이 있으면 그 둘을, 없으면 값 종류가 적은 범주형
              컬럼 몇 개를 자동으로 골라 multiselect로 나란히 그린다.
        반환: 값을 하나라도 고른 컬럼만 FilterCondition("in")으로 담은 리스트.
              아무것도 안 골랐으면 빈 리스트(전체 보기).
        """
        import streamlit as st

        targets = self._resolve_columns(dataset)
        if not targets:
            return []

        slots = st.columns(len(targets))
        filters: list[FilterCondition] = []
        for slot, column in zip(slots, targets):
            condition = self._render_multiselect(slot, dataset, column)
            if condition is not None:
                filters.append(condition)
        return filters

    def _render_multiselect(self, slot, dataset: Dataset, column: str) -> Optional[FilterCondition]:
        options = dataset.get_unique_values(column)
        selected = slot.multiselect(column, options, default=[], placeholder="전체", key=f"filter_{column}")
        if not selected:
            return None
        return FilterCondition(column=column, operator="in", value=list(selected))

    def _resolve_columns(self, dataset: Dataset) -> list[str]:
        df = dataset.df
        preferred = [c for c in (self.columns.district, self.columns.category) if c in df.columns]
        if preferred:
            return preferred
        return self._detect_categorical_columns(df)

    def _detect_categorical_columns(self, df: pd.DataFrame) -> list[str]:
        found: list[str] = []
        for column in df.columns:
            series = df[column]
            is_text = pd.api.types.is_string_dtype(series) or isinstance(series.dtype, pd.CategoricalDtype)
            if not is_text:
                continue
            if 1 < series.nunique() <= self.MAX_AUTO_UNIQUE:
                found.append(str(column))
            if len(found) >= self.MAX_AUTO_COLUMNS:
                break
        return found
