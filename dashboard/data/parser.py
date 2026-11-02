"""ExcelLoader가 읽어 온 원시 DataFrame에서 표의 헤더와 실제 데이터 영역을 구분한다."""
from __future__ import annotations

import pandas as pd


class SheetParser:
    """표 구조만 정리한다. 검증/값 변환/중복 제거는 담당하지 않는다.

    입력: Loader가 header=None으로 읽은 DataFrame 또는 이미 헤더가 있는 DataFrame.
    출력: 컬럼명과 인덱스를 정리한 새 DataFrame.
    예외: 명시적인 파일 오류 없음. 헤더 추론에는 휴리스틱 한계가 있다.
    예시: parsed = SheetParser().parse(raw_df)
    """

    @staticmethod
    def _has_raw_columns(df: pd.DataFrame) -> bool:
        """0,1,2,... 자동 컬럼이면 아직 헤더가 승격되지 않았다고 판단한다."""
        return list(df.columns) == list(range(len(df.columns)))

    @staticmethod
    def _blank_to_na(df: pd.DataFrame) -> pd.DataFrame:
        """빈 문자열/공백만 있는 셀을 결측치로 바꾼 복사본을 만든다."""
        result = df.copy(deep=True)
        for column in result.columns:
            if pd.api.types.is_object_dtype(result[column].dtype) or pd.api.types.is_string_dtype(result[column].dtype):
                result[column] = result[column].replace(r"^\s*$", pd.NA, regex=True)
        return result

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """메타데이터/빈 행·열을 제거하고 헤더를 한 번만 적용한다.

        입력: pd.DataFrame. 자동 생성된 정수 컬럼이면 원시 데이터로 판단한다.
        처리: 빈 셀 정리 → 메타데이터 제거 → 필요 시 첫 행을 헤더로 승격 → 재인덱싱.
        출력: 새 pd.DataFrame. 원본 DataFrame/인덱스를 직접 수정하지 않는다.
        예외: 입력이 DataFrame이 아니면 TypeError.
        예시: SheetParser().parse(pd.DataFrame([['지역','업종'], ['중구','음식']]))

        Loader는 header=None으로 읽는다. 그러나 별도로 이미 헤더를 설정해 둔
        DataFrame도 들어올 수 있으므로, 문자열 컬럼이 있으면 다시 헤더를 뽑지 않는다.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("SheetParser.parse는 DataFrame을 입력받아야 합니다.")
        raw_columns = self._has_raw_columns(df)
        result = self._blank_to_na(df).dropna(how="all").dropna(axis=1, how="all")
        if raw_columns:
            # 원래 자동 생성 컬럼이었으면 중간의 빈 열을 지운 후에도 원시 표로 취급한다.
            result.columns = range(len(result.columns))
        if result.empty:
            return result.reset_index(drop=True).copy()

        if self._has_raw_columns(result):
            # 첫 번째 유효한 행을 컬럼명으로 승격한 후 데이터에서는 삭제한다.
            result = self.strip_metadata_rows(result)
            if result.empty:
                return result.reset_index(drop=True).copy()
            headers = []
            seen: dict[str, int] = {}
            for index, value in enumerate(result.iloc[0]):
                name = str(value).strip() if pd.notna(value) else f"column_{index + 1}"
                # 헤더 이름이 중복되면 _2, _3을 붙여 다음 단계에서 안전하게 접근하도록 한다.
                count = seen.get(name, 0) + 1
                seen[name] = count
                headers.append(name if count == 1 else f"{name}_{count}")
            result = result.iloc[1:].copy()
            result.columns = headers

        # 헤더를 소비한 뒤의 빈 데이터/빈 열만 정리한다.
        return result.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True).copy()

    def detect_header_row(self, df: pd.DataFrame) -> int:
        """표의 헤더로 추정되는 행 위치를 0부터 시작하는 정수로 반환한다.

        입력: 원시 pd.DataFrame.
        처리: 상위 25개 행에서 2개 이상 서로 다른 문자열 셀이 있는 행을 우선 선택.
              열이 하나면 최초의 비어 있지 않은 행을 사용한다.
        출력: 헤더의 상대적 위치(int). 확실하지 않으면 첫 비어 있지 않은 행.
        예외: 없음(비어 있으면 0 반환).
        예시: detect_header_row(pd.DataFrame([['보고서', None], ['자치구', '업종']])) == 1

        주의: 자동 판정은 휴리스틱이다. 모든 데이터가 문자열인 표, 다단 헤더,
        병합 셀, 헤더가 숫자인 표는 완벽하게 판별할 수 없다.
        """
        if not self._has_raw_columns(df):
            return 0
        fallback = 0
        found = False
        # 검사 범위를 제한하면 데이터가 매우 길어도 헤더 탐색 비용이 일정하다.
        for position in range(min(len(df), 25)):
            values = [value for value in df.iloc[position] if pd.notna(value) and str(value).strip()]
            if not values:
                continue
            if not found:
                fallback, found = position, True
            texts = [str(value).strip() for value in values]
            textual_count = sum(isinstance(value, str) for value in values)
            if len(values) >= 2 and len(set(texts)) == len(texts) and textual_count / len(values) >= 0.6:
                return position
        return fallback

    def strip_metadata_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """탐지한 헤더 위쪽의 제목·설명 행을 제거한다.

        입력: 원시 pd.DataFrame.
        처리: detect_header_row() 위치 앞부분을 iloc로 건너뛴다.
        출력: 헤더 행을 포함하는 새 DataFrame (헤더 승격은 parse에서 수행).
        예외: 없음.
        예시: strip_metadata_rows(raw).iloc[0, 0] == '자치구'
        """
        result = df.copy(deep=True)
        if not self._has_raw_columns(result):
            return result
        return result.iloc[self.detect_header_row(result):].copy()
