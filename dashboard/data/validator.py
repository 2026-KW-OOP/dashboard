"""DataFrame의 필수 컬럼·타입·결측치를 검사하고 오류/경고를 반환한다."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationResult:
    """검증 결과: is_valid(통과 여부), errors(실패 원인), warnings(참고사항).

    예시: ValidationResult(False, ['필수 컬럼 없음: 자치구'], [])
    """
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DataValidator:
    """검사만 수행한다. 원본 데이터를 변경하지 않는다.

    입력: 필수 컬럼 목록(required_columns), 기대 dtype 맵(type_map)을 선택적으로 지정.
    출력: validate() 호출 시 ValidationResult 반환.
    예외: dtype 표현이 잘못되면 ValueError.
    예시: DataValidator(['자치구'], {'금액': 'numeric'}).validate(df)

    DashboardApp의 DataValidator() 기본 호출도 그대로 지원한다.
    특정 업로드 스키마가 정해지지 않았으므로 기본 필수 컬럼/타입은 강제하지 않는다.
    """

    def __init__(self, required_columns: list[str] | None = None,
                 type_map: dict[str, str] | None = None) -> None:
        """선택적 검증 규칙을 보관한다. 기본값은 빈 규칙이다."""
        self.required_columns = list(required_columns or [])
        self.type_map = dict(type_map or {})

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """DataFrame을 수정하지 않고 오류와 경고를 수집한다.

        입력: pd.DataFrame.
        처리: 빈 데이터 → 필수 컬럼 확인 → 타입 비교 → 필수 결측/기타 결측 검사.
        출력: ValidationResult. errors가 있으면 is_valid=False, 경고만 있으면 True.
        예외: 잘못된 인수에 TypeError, 잘못된 dtype 설정에 ValueError.
        예시: DataValidator(['자치구']).validate(pd.DataFrame({'업종':['음식']}))
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("DataValidator.validate는 DataFrame을 입력받아야 합니다.")
        errors: list[str] = []
        warnings: list[str] = []
        if df.empty:
            errors.append("데이터가 비어 있습니다(행 또는 열이 없습니다).")
        if not df.columns.is_unique:
            errors.append("중복된 컬럼명이 존재합니다.")
            return ValidationResult(False, errors, warnings)

        missing = self.check_required_columns(df, self.required_columns)
        if missing:
            errors.append("필수 컬럼 누락: " + ", ".join(missing))
        errors.extend(self.check_types(df, self.type_map))

        # 반드시 필요한 컬럼의 누락된 값은 데이터 품질 오류로 취급한다.
        for name in self.required_columns:
            if name not in df.columns:
                continue
            count = int(df[name].isna().sum())
            if count:
                errors.append(f"필수 컬럼 '{name}'에 결측치 {count}개가 있습니다.")

        # 나머지 컬럼의 결측치는 작업을 차단하지 않고 정제 전략 선택을 위한 경고로 남긴다.
        for name in df.columns:
            if name in self.required_columns:
                continue
            count = int(df[name].isna().sum())
            if count:
                warnings.append(f"'{name}' 컬럼에 결측치 {count}개가 있습니다.")
        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)

    def check_required_columns(self, df: pd.DataFrame, required: list[str]) -> list[str]:
        """필요하지만 존재하지 않는 컬럼의 이름 목록을 반환한다.

        입력: DataFrame과 컬럼명 리스트.
        처리: 각 required 이름이 df.columns에 포함되는지 검사한다.
        출력: 누락된 컬럼명 list[str]; 모두 있으면 빈 리스트.
        예외: 없음.
        예시: check_required_columns(df, ['자치구', '업종']) → ['업종']
        """
        return [column for column in required if column not in df.columns]

    def check_types(self, df: pd.DataFrame, type_map: dict[str, str]) -> list[str]:
        """컬럼의 실제 dtype과 기대 dtype을 비교해 오류 메시지를 만든다.

        입력: DataFrame, {'컬럼명': 'float64'|'object'|'numeric'|'string' 등}.
        처리: 'numeric'/'datetime'은 문자열 값의 변환 가능성도 검사(값은 변경하지 않음).
              'string'은 문자열 계열 dtype, 나머지는 엄격한 dtype으로 비교.
        출력: 오류 메시지 list[str]. 타입을 자동 변환하지 않는다.
        예외: 지원하지 않는 dtype 표현은 ValueError.
        예시: check_types(df, {'매출': 'numeric'}) → ["'매출' ..."]
        """
        errors: list[str] = []
        for column, expected in type_map.items():
            if column not in df.columns:
                errors.append(f"타입 검사 대상 컬럼 '{column}'이(가) 없습니다.")
                continue
            dtype = df[column].dtype
            if expected == "numeric":
                # CSV는 Loader에서 dtype=object로 보존한다. 따라서 dtype이 object라도
                # 실제 값이 모두 수치로 해석되면 타입 검사만 통과시킨다(원본 변환은 하지 않음).
                values = df[column].dropna()
                matches = (pd.api.types.is_numeric_dtype(dtype) and not pd.api.types.is_bool_dtype(dtype))
                if not matches and not values.empty and not pd.api.types.is_bool_dtype(dtype):
                    matches = bool(pd.to_numeric(values, errors="coerce").notna().all())
            elif expected == "string":
                # 문자열/혼합 object 타입은 허용하지만 순수 숫자 dtype은 허용하지 않는다.
                matches = pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype)
            elif expected == "datetime":
                # 원본이 문자열이면 파싱 가능 여부만 검사한다. DataFrame은 수정하지 않는다.
                matches = pd.api.types.is_datetime64_any_dtype(dtype)
                if not matches and (pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype)):
                    values = df[column].dropna()
                    matches = not values.empty and bool(pd.to_datetime(values, errors="coerce").notna().all())
            else:
                try:
                    expected_dtype = pd.api.types.pandas_dtype(expected)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"지원하지 않는 dtype 설정: {expected}") from exc
                matches = pd.api.types.is_dtype_equal(dtype, expected_dtype)
            if not matches:
                errors.append(f"'{column}' 컬럼은 {expected} 타입이어야 하지만 실제로는 {dtype}입니다.")
        return errors
