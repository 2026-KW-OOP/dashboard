"""화면에 보여줄 요약 수치와 집계 표를 계산한다 (UI 계층 보조 클래스)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class ColumnMap:
    district: str = "자치구"
    category: str = "업종"


@dataclass(frozen=True)
class TopItem:
    name: str
    count: int
    ratio: float


@dataclass(frozen=True)
class SummaryMetrics:
    total: int
    top_district: Optional[TopItem]
    top_category: Optional[TopItem]


class MetricsCalculator:
    COUNT_COLUMN = "가맹점 수"
    OTHER_LABEL = "기타"

    def __init__(self, columns: Optional[ColumnMap] = None) -> None:
        self.columns = columns or ColumnMap()

    def summarize(self, df: pd.DataFrame) -> SummaryMetrics:
        return SummaryMetrics(
            total=len(df),
            top_district=self._top_item(df, self.columns.district),
            top_category=self._top_item(df, self.columns.category),
        )

    def count_by(
        self,
        df: pd.DataFrame,
        column: str,
        top_n: Optional[int] = None,
        merge_rest: bool = False,
    ) -> pd.DataFrame:
        empty = pd.DataFrame({column: pd.Series(dtype="object"), self.COUNT_COLUMN: pd.Series(dtype="int64")})
        if column not in df.columns or df.empty:
            return empty

        counts = df[column].dropna().astype(str).value_counts()
        if counts.empty:
            return empty

        table = counts.rename_axis(column).reset_index(name=self.COUNT_COLUMN)
        if top_n is None or len(table) <= top_n:
            return table

        head = table.head(top_n)
        if not merge_rest:
            return head.reset_index(drop=True)

        rest_total = int(table.iloc[top_n:][self.COUNT_COLUMN].sum())
        rest = pd.DataFrame({column: [self.OTHER_LABEL], self.COUNT_COLUMN: [rest_total]})
        return pd.concat([head, rest], ignore_index=True)

    def has_column(self, df: pd.DataFrame, column: str) -> bool:
        return column in df.columns

    def _top_item(self, df: pd.DataFrame, column: str) -> Optional[TopItem]:
        table = self.count_by(df, column)
        if table.empty:
            return None
        total = int(table[self.COUNT_COLUMN].sum())
        first = table.iloc[0]
        count = int(first[self.COUNT_COLUMN])
        return TopItem(name=str(first[column]), count=count, ratio=count / total if total else 0.0)
