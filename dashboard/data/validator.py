"""스키마·데이터 타입 검증."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DataValidator:
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """컬럼 존재 여부·타입·필수값을 검증한다 (미구현, 항상 유효 처리).

        입력: df — 검증 대상 DataFrame (정제 전후 어느 쪽이든 호출 가능).
        동작: check_required_columns / check_types를 순서대로 호출해
              각각의 결과를 errors/warnings로 모은다. (check_null_ratio는
              제거되어 결측치 비율 경고는 현재 하지 않는다.)
        반환: ValidationResult — errors가 하나라도 있으면 is_valid=False,
              warnings만 있으면 is_valid=True로 유지(경고는 통과 허용).
        """
        return ValidationResult(is_valid=True)

    def check_required_columns(self, df: pd.DataFrame, required: list[str]) -> list[str]:
        """누락된 필수 컬럼 목록을 반환한다 (미구현).

        입력: df — 검증 대상. required — 필수 컬럼명 목록 (예: ["주문일", "매출", "지역"]).
        동작: required 각각이 df.columns에 실제로 존재하는지 확인한다.
        반환: df에 없는 필수 컬럼명 리스트. 빈 리스트면 문제 없음
              (validate()에서 errors에 그대로 합쳐진다).
        """
        return []

    def check_types(self, df: pd.DataFrame, type_map: dict[str, str]) -> list[str]:
        """타입이 맞지 않는 컬럼에 대한 오류 메시지를 반환한다 (미구현).

        입력: df — 검증 대상. type_map — {컬럼명: 기대 dtype 문자열}
              (예: {"매출": "float64", "주문일": "datetime64[ns]"}).
        동작: 각 컬럼의 실제 df[col].dtype과 기대 dtype을 비교한다.
        반환: 타입이 불일치하는 컬럼마다 사람이 읽을 수 있는 오류 문자열 리스트
              (예: ["'매출' 컬럼은 float64여야 하는데 object입니다"]).
        """
        return []
