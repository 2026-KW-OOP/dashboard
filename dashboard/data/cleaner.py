"""DataFrame 컬럼명, 결측치, 중복 행을 정제한다."""
from __future__ import annotations

import re

import pandas as pd


class DataCleaner:
    """검증된 DataFrame을 분석 가능한 새 객체로 바꾼다.

    입력: missing_strategy ('keep'/'drop'/'fill_zero'/'fill_mean').
    출력: clean()이 정제된 DataFrame을 반환. 원본은 수정하지 않는다.
    예외: 알 수 없는 전략(ValueError).
    예시: DataCleaner(missing_strategy='fill_zero').clean(df)

    보수적인 기본값 'keep'은 결측 행을 임의로 지우지 않기 위한 선택이다.
    """

    def __init__(self, missing_strategy: str = "keep") -> None:
        """결측치 처리 전략을 주입받는다. 예: DataCleaner('drop')."""
        self.missing_strategy = missing_strategy

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 정규화 → 결측치 처리 → 중복 제거 순서로 적용한다.

        입력: pd.DataFrame(주로 Parser/Validator 통과 결과).
        처리: 각 메서드가 돌려주는 새 DataFrame을 다음 메서드에 전달한다.
        출력: 새 pd.DataFrame; 원본은 그대로 남는다.
        예외: 알 수 없는 결측치 전략이면 ValueError.
        예시: cleaned = DataCleaner().clean(df)
        """
        # pandas 메서드에서 inplace=True를 사용하지 않아 원본 재사용 시 부작용이 없다.
        result = self.normalize_column_names(df)
        result = self.handle_missing(result, self.missing_strategy)
        result = self.remove_duplicates(result, None)
        return result.reset_index(drop=True)

    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명만 snake_case로 정규화하고 한글 이름은 보존한다.

        입력: pd.DataFrame(컬럼에 공백·기호가 포함될 수 있음).
        처리: camelCase 분리, 기호를 '_'로 통일, 소문자화, 중복 시 접미사 부여.
        출력: 컬럼명만 바뀐 새 DataFrame. 셀 값은 유지한다.
        예외: 일반적인 DataFrame 입력에서는 없음.
        예시: 'Sales Amount' → 'sales_amount', '자치구' → '자치구'.

        UI의 ColumnMap이 '자치구', '업종'을 찾으므로 한글 자체는 제거하지 않는다.
        """
        result = df.copy(deep=True)
        names = []
        used: set[str] = set()
        for index, column in enumerate(result.columns):
            name = str(column).strip()
            name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
            name = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_").lower()
            base = name or f"column_{index + 1}"
            candidate = base
            counter = 2
            while candidate in used:
                candidate = f"{base}_{counter}"
                counter += 1
            used.add(candidate)
            names.append(candidate)
        result.columns = names
        return result

    def handle_missing(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """데이터 타입을 고려해 결측치를 처리한다.

        입력: pd.DataFrame, 전략 문자열.
        처리: keep(유지) / drop(결측 행 제거) / fill_zero(숫자 열만 0)
              / fill_mean(숫자 열만 해당 열 평균). 문자열/날짜 결측은 자동 숫자화 금지.
        출력: 정제된 새 DataFrame; 숫자 열이 전부 NaN이면 평균 대체가 불가해 NaN 유지.
        예외: 잘못된 전략일 때 ValueError.
        예시: handle_missing(df, 'fill_mean')

        주의: drop은 행이 영구히 빠질 수 있으므로 서비스 정책 없이 자동 선택하지 않는다.
        """
        if strategy not in {"keep", "drop", "fill_zero", "fill_mean"}:
            raise ValueError(f"알 수 없는 결측치 처리 전략입니다: {strategy}")
        result = df.copy(deep=True)
        if strategy == "drop":
            return result.dropna().copy()
        if strategy in {"fill_zero", "fill_mean"}:
            for column in result.columns:
                # bool도 수치 계산 대상으로 오인하지 않도록 배제한다.
                if not pd.api.types.is_numeric_dtype(result[column].dtype) or pd.api.types.is_bool_dtype(result[column].dtype):
                    continue
                if strategy == "fill_zero":
                    value = 0
                else:
                    value = result[column].mean()
                if pd.notna(value):
                    result[column] = result[column].fillna(value)
        return result

    def remove_duplicates(self, df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
        """기준 컬럼에서 값이 같은 중복 행의 첫 번째 행만 남긴다.

        입력: pd.DataFrame, 중복 판단 컬럼 리스트 또는 None(모든 컬럼).
        처리: drop_duplicates(keep='first')을 실행한다.
        출력: 중복이 빠진 새 DataFrame. 원본 불변.
        예외: subset 컬럼이 존재하지 않으면 pandas KeyError.
        예시: remove_duplicates(df, ['가맹점명'])

        주의: subset을 좁히면 서로 다른 가맹점도 합쳐질 위험이 있다.
        """
        return df.copy(deep=True).drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
