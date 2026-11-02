"""개인정보가 없는 가상 데이터를 메모리와 임시 파일로 생성하여 검사한다."""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from dashboard.config.settings import AppConfig
from dashboard.data.loader import ExcelLoader
from dashboard.data.parser import SheetParser
from dashboard.data.validator import DataValidator
from dashboard.data.cleaner import DataCleaner
from dashboard.utils.exceptions import EmptyDatasetError, InvalidFileFormatError
from dashboard.models.dataset import Dataset
from dashboard.services.filter import DataFilter, FilterCondition


class NamedBytesIO(BytesIO):
    """Streamlit의 UploadedFile처럼 .name이 있는 바이너리 스트림 대역."""

    def __init__(self, payload: bytes, name: str):
        super().__init__(payload)
        self.name = name


def excel_data(**tables):
    """header=False로 작성하여 첫 번째 행이 실제 데이터임을 시뮬레이션한다."""
    stream = BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, header=False, index=False)
    return stream.getvalue()


def test_xlsx_one_sheet_and_parser(tmp_path):
    payload = excel_data(가맹점=pd.DataFrame([['자치구', '업종'], ['강남구', '음식점']]))
    path = tmp_path / 'merchants.xlsx'
    path.write_bytes(payload)
    loader = ExcelLoader(AppConfig())
    assert loader.list_sheets(str(path)) == ['가맹점']
    parsed = SheetParser().parse(loader.load(str(path))['가맹점'])
    assert list(parsed.columns) == ['자치구', '업종']
    assert parsed.loc[0, '자치구'] == '강남구'


def test_excel_multiple_sheets_and_empty_sheet():
    data = excel_data(첫시트=pd.DataFrame([['자치구', '업종'], ['마포구','카페']]),
                      둘째시트=pd.DataFrame([['자치구','업종'], ['종로구','식당']]),
                      빈시트=pd.DataFrame())
    stream = NamedBytesIO(data, 'sample.xlsx')
    loader = ExcelLoader(AppConfig())
    tables = loader.load(stream)
    assert list(tables) == ['첫시트', '둘째시트', '빈시트']
    assert tables['빈시트'].empty
    assert not DataValidator().validate(SheetParser().parse(tables['빈시트'])).is_valid


def test_csv_path_and_separator(tmp_path):
    path = tmp_path / 'stores.csv'
    path.write_text('자치구;업종\n중구;음식\n', encoding='utf-8')
    loader = ExcelLoader(AppConfig())
    assert loader.list_sheets(str(path)) == ['Sheet1']
    df = SheetParser().parse(loader.load(str(path))['Sheet1'])
    assert df.loc[0, '업종'] == '음식'


@pytest.mark.parametrize('encoding', ['utf-8', 'utf-8-sig', 'cp949'])
def test_korean_csv_encodings(encoding):
    payload = '자치구,업종\n서초구,음식점\n'.encode(encoding)
    stream = NamedBytesIO(payload, 'korean.csv')
    df = SheetParser().parse(ExcelLoader(AppConfig()).load(stream)['Sheet1'])
    assert df.iloc[0].tolist() == ['서초구','음식점']


def test_bytesio_without_filename_and_cursor_is_preserved():
    stream = BytesIO('자치구\t업종\n강동구\t카페\n'.encode('utf-8'))
    stream.seek(3)
    out = ExcelLoader(AppConfig()).load(stream)['Sheet1']
    assert stream.tell() == 3 and not stream.closed
    assert SheetParser().parse(out).loc[0, '업종'] == '카페'


def test_uploaded_file_like_buffer_and_cursor():
    stream = NamedBytesIO(b'a,b\n1,2\n', 'file.csv')
    stream.seek(4)
    assert ExcelLoader(AppConfig()).list_sheets(stream) == ['Sheet1']
    assert stream.tell() == 4


def test_wrong_extension_and_bad_binary(tmp_path):
    loader = ExcelLoader(AppConfig())
    with pytest.raises(InvalidFileFormatError, match='일치'):
        loader.load(NamedBytesIO(b'a,b\n1,2', 'spoof.xlsx'))
    with pytest.raises(InvalidFileFormatError):
        loader.load(NamedBytesIO(b'\x00\x01\x02', 'broken.csv'))
    path = tmp_path / 'not_allowed.txt'
    path.write_text('a,b\n1,2')
    with pytest.raises(InvalidFileFormatError, match='허용하지'):
        loader.load(str(path))


def test_bad_excel_zip():
    with pytest.raises(InvalidFileFormatError):
        ExcelLoader(AppConfig()).load(NamedBytesIO(b'PK\x03\x04not-a-zip', 'bad.xlsx'))


def test_empty_file_and_empty_csv_content():
    with pytest.raises(EmptyDatasetError):
        ExcelLoader(AppConfig()).load(BytesIO())
    with pytest.raises(InvalidFileFormatError):
        ExcelLoader(AppConfig()).load(NamedBytesIO(b'  \n  ', 'empty.csv'))


def test_upload_size_limit():
    loader = ExcelLoader(AppConfig(upload_max_size_mb=0))
    with pytest.raises(InvalidFileFormatError, match='초과'):
        loader.load(BytesIO(b'a,b\n1,2'))


def test_parser_metadata_and_blank_columns():
    raw = pd.DataFrame([
        ['서울 가맹점 현황', None, None, None],
        [None, None, None, None],
        ['자치구', '업종', None, None],
        ['송파구', '미용', None, None],
    ])
    parser = SheetParser()
    assert parser.detect_header_row(raw) == 2
    result = parser.parse(raw)
    assert list(result.columns) == ['자치구','업종']
    assert len(result) == 1 and result.index.tolist() == [0]
    pd.testing.assert_frame_equal(raw, pd.DataFrame([
        ['서울 가맹점 현황', None, None, None], [None]*4,
        ['자치구', '업종', None, None], ['송파구','미용',None,None]
    ]))


def test_parser_does_not_promote_existing_header():
    df = pd.DataFrame({'자치구': ['강남구','강북구'], '업종': ['카페','음식']})
    result = SheetParser().parse(df)
    assert list(result.columns) == ['자치구','업종']
    assert len(result) == 2


def test_parser_nonfirst_raw_columns_are_still_parsed():
    raw = pd.DataFrame([[None, '자치구', '업종'], [None,'중구','음식']])
    assert list(SheetParser().parse(raw).columns) == ['자치구','업종']


def test_validator_missing_required_columns_and_dtypes():
    df = pd.DataFrame({'자치구': ['동작구'], '매출': ['오천원']})
    result = DataValidator(['자치구','업종'], {'매출': 'numeric'}).validate(df)
    assert not result.is_valid
    assert '업종' in ' '.join(result.errors)
    assert 'numeric' in ' '.join(result.errors)


def test_validator_required_missing_value_and_optional_warning_no_mutation():
    df = pd.DataFrame({'자치구': [None, '중구'], '업종': ['카페',None]})
    original = df.copy(deep=True)
    result = DataValidator(['자치구']).validate(df)
    assert not result.is_valid
    assert any('자치구' in e for e in result.errors)
    assert result.warnings and '업종' in result.warnings[0]
    pd.testing.assert_frame_equal(df, original)


def test_validator_empty_data():
    assert not DataValidator().validate(pd.DataFrame()).is_valid


def test_cleaner_normalizes_keeps_korean_and_copies():
    df = pd.DataFrame({'자치구':['중구'],'업종':['카페'],'Sales Amount':[3], '매출 금액 (원)': [4]})
    clean = DataCleaner().clean(df)
    assert list(clean.columns) == ['자치구','업종','sales_amount','매출_금액_원']
    assert list(df.columns) == ['자치구','업종','Sales Amount','매출 금액 (원)']


def test_cleaner_missing_strategies_and_duplicates():
    df = pd.DataFrame({'자치구': ['종로구','종로구', None], '금액': [10.0,10.0,None]})
    cleaner = DataCleaner()
    assert len(cleaner.clean(df)) == 2
    dropped = cleaner.handle_missing(df, 'drop')
    assert len(dropped) == 2
    zero = cleaner.handle_missing(df, 'fill_zero')
    assert zero.loc[2,'금액'] == 0 and pd.isna(zero.loc[2,'자치구'])
    mean = cleaner.handle_missing(df, 'fill_mean')
    assert mean.loc[2,'금액'] == 10 and pd.isna(mean.loc[2,'자치구'])
    assert pd.isna(df.loc[2,'금액'])
    with pytest.raises(ValueError):
        cleaner.handle_missing(df, 'unknown')


def test_missing_mean_all_nan_stays_nan():
    df = pd.DataFrame({'금액': pd.Series([float('nan')], dtype='float64')})
    assert pd.isna(DataCleaner().handle_missing(df, 'fill_mean').loc[0,'금액'])


def test_complete_pipeline_with_existing_model_and_service():
    stream = NamedBytesIO('자치구,업종\n강서구,음식점\n중구,카페\n'.encode(), 'stores.csv')
    loader, parser, validator, cleaner = ExcelLoader(AppConfig()), SheetParser(), DataValidator(['자치구','업종']), DataCleaner()
    raw = loader.load(stream)
    parsed = parser.parse(raw['Sheet1'])
    result = validator.validate(parsed)
    assert result.is_valid
    from datetime import datetime
    dataset = Dataset(df=cleaner.clean(parsed), source_file='stores.csv', loaded_at=datetime.now())
    assert dataset.get_unique_values('자치구') == ['강서구', '중구']
    filtered = DataFilter().apply(dataset.df, [FilterCondition('자치구','in',['중구'])])
    assert filtered['업종'].tolist() == ['카페']


def test_csv_metadata_row_with_different_width():
    stream = NamedBytesIO('서울 가맹점 현황\n자치구,업종,상호\n중구,음식,예시가게\n'.encode(), 'report.csv')
    parsed = SheetParser().parse(ExcelLoader(AppConfig()).load(stream)['Sheet1'])
    assert list(parsed.columns) == ['자치구','업종','상호']
    assert parsed.loc[0,'상호'] == '예시가게'


def test_xls_reports_missing_optional_package():
    # .xls의 OLE 매직 바이트는 맞더라도 엔진이 없는 환경에서는 안내 오류를 준다.
    import importlib.util
    if importlib.util.find_spec('xlrd') is None:
        stream = NamedBytesIO(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'0' * 256, 'legacy.xls')
        with pytest.raises(InvalidFileFormatError, match='xlrd'):
            ExcelLoader(AppConfig()).load(stream)
    else:
        pytest.skip('xlrd 설치 환경에서는 실제 .xls 파일 별도 통합 검사 필요')


def test_csv_numeric_strings_pass_semantic_validation_without_conversion():
    """CSV 원본 문자열 수치라도 검사는 통과할 수 있지만 타입을 바꾸지는 않는다."""
    stream = BytesIO('자치구,매출\n중구,120\n마포구,450\n'.encode())
    frame = SheetParser().parse(ExcelLoader(AppConfig()).load(stream)['Sheet1'])
    before = frame.copy(deep=True)
    result = DataValidator(type_map={'매출': 'numeric'}).validate(frame)
    assert result.is_valid
    assert frame['매출'].dtype == object
    pd.testing.assert_frame_equal(frame, before)


def test_csv_semicolon_quotes_and_cp949():
    stream = NamedBytesIO('자치구;상호\n강남구;"식당;예시"\n'.encode('cp949'), 'semi.csv')
    frame = SheetParser().parse(ExcelLoader(AppConfig()).load(stream)['Sheet1'])
    assert frame.iloc[0]['상호'] == '식당;예시'


def test_cleaner_normalization_name_collision():
    frame = pd.DataFrame({'Sales Amount': [1], 'sales-amount': [2]})
    result = DataCleaner().normalize_column_names(frame)
    assert list(result.columns) == ['sales_amount', 'sales_amount_2']


def test_renamed_xlsx_to_csv_is_rejected():
    payload = excel_data(첫시트=pd.DataFrame([['자치구','업종'],['용산구','음식']]))
    with pytest.raises(InvalidFileFormatError, match='일치'):
        ExcelLoader(AppConfig()).load(NamedBytesIO(payload, 'fake.csv'))
