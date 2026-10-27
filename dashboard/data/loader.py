"""Excel/CSV 입력을 시트 이름별 원시 DataFrame으로 변환하는 모듈."""
from __future__ import annotations

import csv
from io import BytesIO, StringIO
from os import PathLike
from pathlib import Path
from typing import Union
import zipfile

import pandas as pd

from dashboard.config.settings import AppConfig
from dashboard.utils.exceptions import EmptyDatasetError, InvalidFileFormatError

FileSource = Union[str, PathLike[str], BytesIO]


class ExcelLoader:
    """파일의 읽기(I/O)만 담당한다. 헤더 해석·검증·정제는 다른 클래스의 책임이다.

    입력: AppConfig(허용 확장자, 파일 크기 제한 등).
    반환: 인스턴스. load()/list_sheets()에서 파일을 받는다.
    예외: 생성 시 없음. 파일 오류는 load() 호출 시 발생한다.
    예시: loader = ExcelLoader(AppConfig()); tables = loader.load('sample.csv')
    """

    def __init__(self, config: AppConfig) -> None:
        """설정 객체를 주입받아 보관한다. 반환/예외는 없다.

        예시: ExcelLoader(AppConfig(upload_max_size_mb=5))
        """
        self.config = config

    def load(self, file_path: FileSource) -> dict[str, pd.DataFrame]:
        """파일을 읽어 모든 시트를 사전으로 반환한다.

        입력: 경로(str/PathLike) 또는 BytesIO·Streamlit UploadedFile.
        처리: _detect_format() → 형식에 맞는 _read_excel()/_read_csv().
        출력: {'시트명': 원시 DataFrame}; CSV의 키는 항상 'Sheet1'.
        예외: EmptyDatasetError(0바이트), InvalidFileFormatError(형식/읽기 오류).
        예시: loader.load(BytesIO(b'name,age\\nKim,20\\n'))['Sheet1']

        왜 사전인가? Excel의 여러 시트를 원래 이름으로 보존하고,
        CSV도 동일한 자료형으로 상위 계층(DashboardApp)에 전달하기 위해서다.
        """
        kind = self._detect_format(file_path)
        if kind == "csv":
            return self._read_csv(file_path)
        return self._read_excel(file_path, kind)

    def list_sheets(self, file_path: FileSource) -> list[str]:
        """내용 전체를 DataFrame으로 읽지 않고 시트 이름만 가져온다.

        입력: load()와 동일한 파일 소스.
        처리: CSV는 ['Sheet1']; Excel은 pandas.ExcelFile의 sheet_names 조회.
        출력: list[str]. UI의 시트 선택 드롭다운에 전달된다.
        예외: EmptyDatasetError, InvalidFileFormatError.
        예시: ExcelLoader(AppConfig()).list_sheets('book.xlsx')
        """
        kind = self._detect_format(file_path)
        if kind == "csv":
            return ["Sheet1"]
        engine = "openpyxl" if kind == "xlsx" else "xlrd"
        try:
            # 원본 스트림을 직접 넘기지 않으므로 호출자의 커서/close 상태를 건드리지 않는다.
            with pd.ExcelFile(BytesIO(self._file_bytes(file_path)), engine=engine) as book:
                return list(book.sheet_names)
        except ImportError as exc:
            raise InvalidFileFormatError(self._engine_install_message(kind)) from exc
        except Exception as exc:
            raise InvalidFileFormatError(f"시트 목록을 읽지 못했습니다: {exc}") from exc

    def _file_bytes(self, file_path: FileSource) -> bytes:
        """파일 입력을 독립된 bytes로 복사한다(원본 소유권은 호출자에게 있다).

        입력: 파일 경로 또는 읽을 수 있는 바이너리 스트림.
        처리: 경로면 파일 읽기, 버퍼면 getvalue() 또는 tell/read/seek로 복원.
        출력: bytes. 최대 용량을 넘으면 예외.
        예외: InvalidFileFormatError(접근 실패/과용량/잘못된 입력).
        예시: self._file_bytes(BytesIO(b'a,b')) == b'a,b'
        """
        limit = self.config.upload_max_size_mb * 1024 * 1024
        try:
            if isinstance(file_path, (str, PathLike)):
                path = Path(file_path)
                # 큰 파일은 읽기 전에 크기를 검사해 불필요한 메모리 사용을 방지한다.
                if path.stat().st_size > limit:
                    raise InvalidFileFormatError(f"파일 크기가 {self.config.upload_max_size_mb}MB를 초과합니다.")
                data = path.read_bytes()
            elif hasattr(file_path, "getvalue"):
                # BytesIO/UploadedFile은 getvalue()로 읽으면 현재 커서 위치가 변하지 않는다.
                data = file_path.getvalue()
            elif hasattr(file_path, "read") and hasattr(file_path, "seek") and hasattr(file_path, "tell"):
                # 일반 파일형 객체는 읽기 전 위치를 기억했다가 finally에서 복원한다.
                position = file_path.tell()
                try:
                    file_path.seek(0)
                    data = file_path.read()
                finally:
                    file_path.seek(position)
            else:
                raise InvalidFileFormatError("경로 또는 바이너리 파일 객체가 필요합니다.")
        except InvalidFileFormatError:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise InvalidFileFormatError(f"파일을 읽지 못했습니다: {exc}") from exc
        if not isinstance(data, bytes):
            raise InvalidFileFormatError("바이너리 파일 객체를 입력해 주세요.")
        if len(data) > limit:
            raise InvalidFileFormatError(f"파일 크기가 {self.config.upload_max_size_mb}MB를 초과합니다.")
        return data

    def _detect_format(self, file_path: FileSource) -> str:
        """확장자와 실제 바이트 내용을 함께 검사한다.

        입력: load()와 같은 소스(업로드 객체의 .name도 확인).
        처리: ZIP 기반 xlsx/복합문서 xls 매직바이트 확인 후 텍스트 CSV 판정.
        출력: 'xlsx'/'xls'/'csv'.
        예외: EmptyDatasetError(비었음), InvalidFileFormatError(불일치·손상).
        예시: self._detect_format(BytesIO(b'a,b\\n1,2')) == 'csv'
        """
        data = self._file_bytes(file_path)
        if not data:
            raise EmptyDatasetError("파일이 비어 있습니다(0바이트).")
        name = file_path if isinstance(file_path, (str, PathLike)) else getattr(file_path, "name", "")
        suffix = Path(str(name)).suffix.lower() if name else ""
        allowed = {ext.lower() for ext in self.config.allowed_extensions}
        if suffix and suffix not in allowed:
            raise InvalidFileFormatError(f"허용하지 않는 확장자입니다: {suffix}")

        # xlsx는 ZIP 컨테이너. 단순 ZIP을 엑셀로 오인하지 않도록 내부 구성도 확인한다.
        if data.startswith(b"PK"):
            try:
                with zipfile.ZipFile(BytesIO(data)) as archive:
                    kind = "xlsx" if "xl/workbook.xml" in archive.namelist() else None
            except (zipfile.BadZipFile, OSError):
                kind = None
        elif data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            kind = "xls"
        else:
            kind = "csv" if self._decode_csv(data) is not None else None
        if kind is None:
            raise InvalidFileFormatError("Excel/CSV 형식이 아니거나 파일이 손상되었습니다.")
        if suffix and suffix != f".{kind}":
            raise InvalidFileFormatError(f"확장자({suffix})와 실제 내용({kind})이 일치하지 않습니다.")
        if f".{kind}" not in allowed:
            raise InvalidFileFormatError(f"설정에서 허용하지 않는 파일 형식입니다: {kind}")
        return kind

    @staticmethod
    def _decode_csv(data: bytes) -> str | None:
        """UTF-8 BOM, UTF-8, CP949 순서로 해석 가능한 텍스트를 찾는다.

        입력: bytes. 출력: str 또는 None. 예외: 디코딩 실패를 None으로 처리.
        예시: ExcelLoader._decode_csv('가맹점'.encode('cp949')) == '가맹점'
        """
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                text = data.decode(encoding)
                # NUL 바이트는 바이너리를 텍스트 CSV로 잘못 판단하는 것을 예방한다.
                if "\x00" in text:
                    return None
                if not text.strip():
                    return None
                return text
            except UnicodeDecodeError:
                continue
        return None

    @staticmethod
    def _engine_install_message(kind: str) -> str:
        """필요한 Excel 엔진과 설치 명령을 알려준다."""
        return (".xls 파일에는 xlrd가 필요합니다: python -m pip install xlrd>=2.0.1"
                if kind == "xls" else ".xlsx 파일에는 openpyxl이 필요합니다: python -m pip install openpyxl")

    def _read_excel(self, file_path: FileSource, kind: str = "xlsx") -> dict[str, pd.DataFrame]:
        """모든 Excel 시트를 원시 DataFrame으로 읽는다.

        입력: 파일 소스, 형식('xlsx' 또는 'xls').
        처리: pandas.read_excel(sheet_name=None, header=None)으로 시트들을 읽는다.
        출력: dict[str, DataFrame]. 비어 있는 개별 시트는 빈 DataFrame으로 유지.
        예외: InvalidFileFormatError(손상·엔진 미설치·읽기 실패).
        예시: self._read_excel('book.xlsx')['Sheet1']

        header=None인 이유: 위쪽 제목/설명 행을 pandas가 헤더로 잘못 소비하지
        않도록 하고, 다음 단계인 SheetParser에게 헤더 결정 권한을 주기 위해서다.
        """
        engine = "openpyxl" if kind == "xlsx" else "xlrd"
        try:
            # BytesIO는 파일 내용을 메모리의 파일처럼 다룬다. 지역 변수만 사용해 자동 회수된다.
            tables = pd.read_excel(BytesIO(self._file_bytes(file_path)), sheet_name=None,
                                   header=None, engine=engine)
            if not tables:
                raise EmptyDatasetError("워크북에 시트가 없습니다.")
            return tables
        except (EmptyDatasetError, InvalidFileFormatError):
            raise
        except ImportError as exc:
            raise InvalidFileFormatError(self._engine_install_message(kind)) from exc
        except Exception as exc:
            raise InvalidFileFormatError(f"Excel을 읽지 못했습니다: {exc}") from exc

    def _read_csv(self, file_path: FileSource) -> dict[str, pd.DataFrame]:
        """인코딩·구분자를 판별해 CSV를 한 개의 원시 시트로 반환한다.

        입력: CSV 경로 또는 BytesIO.
        처리: UTF-8/CP949 디코딩 → csv.Sniffer로 구분자 판별 → pandas.read_csv.
        출력: {'Sheet1': DataFrame}.
        예외: EmptyDatasetError(실질적 빈 파일), InvalidFileFormatError(파싱 실패).
        예시: self._read_csv(BytesIO(b'a;b\\n1;2'))['Sheet1']
        """
        text = self._decode_csv(self._file_bytes(file_path))
        if text is None:
            raise EmptyDatasetError("읽을 수 있는 CSV 내용이 없습니다.")
        try:
            sample = text[:8192]
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                # 모호한 파일은 CSV 기본 구분자인 쉼표를 사용한다.
                delimiter = ","

            # 제목 한 줄 + 다열 표처럼 행마다 열 수가 달라도 읽도록 열 개수의 최댓값을 계산한다.
            rows = csv.reader(StringIO(text), delimiter=delimiter)
            width = max((len(row) for row in rows), default=0)
            if width == 0:
                raise EmptyDatasetError("CSV에 읽을 행이 없습니다.")
            # header=None: 첫 행을 자동으로 컬럼명으로 정하지 않는다(헤더는 Parser 책임).
            frame = pd.read_csv(StringIO(text), sep=delimiter, header=None,
                                names=list(range(width)), skip_blank_lines=False, dtype=object)
            return {"Sheet1": frame}
        except (EmptyDatasetError, InvalidFileFormatError):
            raise
        except (csv.Error, pd.errors.ParserError, ValueError, UnicodeError) as exc:
            raise InvalidFileFormatError(f"CSV를 읽지 못했습니다: {exc}") from exc
