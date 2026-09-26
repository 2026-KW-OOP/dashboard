"""정제된 데이터 + 메타데이터 컨테이너."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

@dataclass
class Dataset:
    df: pd.DataFrame
    source_file: str
    loaded_at: datetime = field(default_factory=datetime.now)

    def get_unique_values(self, column: str) -> list[str]:
        """특정 컬럼의 중복 없는 값 목록을 반환한다.

        입력: column — 조회할 컬럼명 (보통 범주형 컬럼 중 하나, 예: "지역").
        동작: self.df[column]의 결측치를 제외하고, 문자열로 변환한 뒤
              중복을 제거한다.
        반환: 중복 없는 값 리스트, 오름차순 정렬 (예: ["대구", "부산", "서울"]).
              UI 필터 위젯(예: st.multiselect)의 선택지 목록으로 바로 쓰인다.
        """
        return sorted(self.df[column].dropna().astype(str).unique().tolist())
