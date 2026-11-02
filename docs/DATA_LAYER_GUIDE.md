# Data Layer 구현·테스트·발표 가이드

> 대상: `2026-KW-OOP/dashboard`의 `main` 브랜치에서 확인한 스켈레톤 구조  
> 작업 범위: `dashboard/data/`의 네 파일 + 관련 자동화 테스트 + `.xls` 의존성  
> 안전 원칙: `app.py`, `models/`, `services/`, `ui/`, `visualization/`, `config/`, `utils/`는 변경하지 않음

## 1. 현재 프로젝트 구조와 설계 관계

```text
dashboard/
├─ app.py                       DashboardApp: 전체 과정 조립·UI 연동
├─ config/settings.py           AppConfig: 허용 확장자·최대 업로드 크기
├─ data/
│  ├─ loader.py                 ExcelLoader
│  ├─ parser.py                 SheetParser
│  ├─ validator.py              DataValidator + ValidationResult
│  └─ cleaner.py                DataCleaner
├─ models/dataset.py            Dataset: DataFrame + 소스명 + 시각
├─ services/filter.py           DataFilter: 결과 DataFrame을 필터링
├─ ui/metrics.py                ColumnMap: 자치구, 업종
└─ utils/exceptions.py          DashboardError와 하위 예외
```

확인 당시 `dashboard/app.py`에는 다음 호출이 이미 있었다.

```python
self.loader = ExcelLoader(config)
self.parser = SheetParser()
self.validator = DataValidator()
self.cleaner = DataCleaner()

# 업로드 처리 중
raw_tables = self.loader.load(file)
parsed = self.parser.parse(raw_tables[selected_sheet])
result = self.validator.validate(parsed)
if not result.is_valid:
    # 앱이 result.errors를 사용자에게 보여 주고 중단
    ...
cleaned = self.cleaner.clean(parsed)
# Dataset(df=cleaned, ...)으로 상위 계층에 전달
```

**설계 문서와의 해석상 주의점**

- Loader가 첫 행을 `pandas` 기본 헤더로 소비하면 Parser가 제목·메타데이터 행을 판별할 수 없다. 이 구현은 Excel/CSV 모두 `header=None`으로 읽고 Parser만 헤더를 결정한다.
- CSV는 시트가 없지만 앱은 항상 시트 선택을 하므로 `{ 'Sheet1': df }`를 반환한다.
- `ui/metrics.py`의 `ColumnMap`이 `자치구`, `업종`을 찾으므로 Cleaner는 한글 글자를 보존한다. 예: `자치구`는 그대로, `매출 금액 (원)`은 `매출_금액_원`.
- 실제 앱이 `DataValidator()`를 인수 없이 생성하기 때문에 기본은 특정 파일의 필수 컬럼을 강제하지 않는다. 업로드 형식이 고정된다면 `DataValidator(required_columns=['자치구', '업종'])`로 객체 생성 규칙을 상위 계층에서 정할 수 있다. **이번 작업은 app.py를 변경하지 않았다.**
- `.xls`는 `openpyxl`이 읽지 못한다. 오래된 BIFF 형식은 `xlrd` 엔진이 필요하므로 요구사항에 의존성을 한 줄 추가했다.

## 2. 변경 파일 목록

| 파일 | 변경 이유 |
|---|---|
| `dashboard/data/loader.py` | 포맷 검증, 업로드 스트림 처리, Excel/CSV 읽기, 시트 목록, 인코딩 처리 |
| `dashboard/data/parser.py` | 빈 행·열 제거, 제목 행 제거, 헤더 감지 및 승격 |
| `dashboard/data/validator.py` | 검증 결과 데이터클래스, 필수 컬럼/결측치/타입 검사 |
| `dashboard/data/cleaner.py` | 컬럼명 정규화, 결측치 전략, 중복 제거 |
| `requirements.txt` | `.xls` 지원을 위한 `xlrd>=2.0.1` 추가 |
| `tests/test_data_layer.py` | 합성 데이터 기반 pytest 자동화 테스트 |
| `docs/DATA_LAYER_GUIDE.md` | 설계·메서드 I/O·테스트·Git·발표 자료 |

다른 팀원이 작성한 UI, Service, Visualization 코드는 수정하지 않았다.

## 3. 메서드별 Input → Process → Output → Exception → Dependency

| 클래스.메서드 | Input | Process | Output | Exception / Dependency |
|---|---|---|---|---|
| `ExcelLoader.__init__` | `AppConfig` | 설정 보관(DI) | 인스턴스 | `AppConfig` |
| `ExcelLoader.load` | 경로 / `BytesIO` / `UploadedFile` | 포맷 확인 → 형식별 읽기 | `dict[str, DataFrame]` | `EmptyDatasetError`, `InvalidFileFormatError`; DashboardApp |
| `ExcelLoader.list_sheets` | 같은 파일 소스 | CSV: 기본 시트명; Excel: 시트 이름만 조회 | `list[str]` | Excel 읽기 오류; Sidebar |
| `ExcelLoader._detect_format` | 경로 / 버퍼 | 확장자·매직바이트·허용 형식 비교 | `str` (`xlsx/xls/csv`) | 확장자/내용 불일치 |
| `ExcelLoader._read_excel` | 경로 / 버퍼, 형식 | `read_excel(sheet_name=None, header=None)` | 시트별 DataFrame 사전 | `openpyxl`/`xlrd` 필요 |
| `ExcelLoader._read_csv` | 경로 / 버퍼 | UTF-8 BOM/UTF-8/CP949 → 구분자 추정 → `read_csv` | `{'Sheet1': DataFrame}` | 포맷/파싱 오류 |
| `SheetParser.detect_header_row` | 원시 `DataFrame` | 상위 25행 문자열/열 개수 기반 휴리스틱 | 0 기반 헤더 행 번호 `int` | 추정 실패 시 최초 유효 행 |
| `SheetParser.strip_metadata_rows` | 원시 `DataFrame` | 헤더 앞 제목·메타데이터 행 제외 | 헤더를 포함하는 새 `DataFrame` | Parser 내부 |
| `SheetParser.parse` | Loader의 원시 `DataFrame` | 빈 행·열 정리 → 헤더 승격 → 인덱스 초기화 | 새 `DataFrame` | 비-DataFrame이면 TypeError; Validator |
| `DataValidator.check_required_columns` | `df`, 필수 컬럼명 `list[str]` | `df.columns`와 비교 | 누락 컬럼 `list[str]` | validate에서 사용 |
| `DataValidator.check_types` | `df`, 타입 설정 `dict` | 실제 dtype 또는 문자열 값의 변환 가능 여부 검사(원본 미변경) | 오류 메시지 `list[str]` | 잘못된 기대 dtype이면 ValueError |
| `DataValidator.validate` | `DataFrame` | 빈 데이터·컬럼·필수 결측·타입·선택 컬럼 결측 확인 | `ValidationResult` | `is_valid`/`errors`/`warnings`를 DashboardApp 사용 |
| `DataCleaner.normalize_column_names` | `DataFrame` | 공백/기호 snake_case, 한글 보존, 중복 이름 구별 | 복제한 `DataFrame` | Cleaner 내부 |
| `DataCleaner.handle_missing` | `df`, 전략 문자열 | `keep`, `drop`, `fill_zero`, `fill_mean` | 복제한 `DataFrame` | 미지원 전략이면 ValueError |
| `DataCleaner.remove_duplicates` | `df`, subset 또는 None | 첫 중복만 유지, 인덱스 초기화 | 복제한 `DataFrame` | 잘못된 subset이면 KeyError |
| `DataCleaner.clean` | `DataFrame` | 정규화 → 결측 처리 → 중복 제거 | 최종 새 `DataFrame` | Dataset / DataFilter / ChartFactory |

### 파일 처리 핵심 문법 해설

1. `pd.read_excel(..., sheet_name=None, header=None)` : `None`으로 지정한 `sheet_name`은 워크북 안의 **모든 시트**를 `{이름: DataFrame}`으로 읽는다. `header=None`은 파일 첫 행이 무조건 컬럼명이라고 가정하지 않는다.
2. `pd.read_csv(..., header=None, sep=delimiter)` : CSV 텍스트를 행·열 구조로 파싱한다. 인코딩은 미리 후보별로 디코딩하며 `csv.Sniffer`로 쉼표·세미콜론·탭·파이프를 판별한다.
3. `BytesIO(raw_bytes)` : 디스크 임시 파일을 쓰지 않고, 메모리의 bytes를 마치 파일처럼 pandas에 전달한다.
4. 버퍼 커서: 원본 업로드 스트림의 `tell()`과 `close()` 상태를 유지한다. 실제 pandas에는 새 `BytesIO` 객체를 전달해 원본을 닫거나 커서를 옮기지 않는다.
5. `try ... except ... from exc` : 파일 파싱의 저수준 예외를 앱에서 처리 가능한 `DashboardError` 하위 예외로 감싼다. `from exc`를 통해 디버깅용 원래 오류 원인도 남긴다.
6. `df.copy(deep=True)` : 호출자에게 받은 원본 DataFrame 대신 복사본을 수정한다. 같은 표를 다른 차트나 테스트가 재사용할 때 부작용을 줄인다.
7. `result = f(result)` : 메서드를 순차적으로 적용한 결과를 다음 메서드의 입력으로 보내는 방식이다. 숨겨진 상태보다 데이터 흐름이 명확하다.

### 헤더 판별의 한계

헤더에 서로 다른 문자열 셀이 2개 이상 있고 문자열 비율이 높다면 헤더 후보로 본다. 상단의 보고서 제목처럼 열이 1개인 행은 피할 수 있다. 그러나 **제목도 여러 열이고 실제 데이터도 문자열뿐인 경우, 다중 헤더/병합 셀, 숫자 헤더**는 자동 결정이 틀릴 수 있다. 완벽한 일반 알고리즘이 아니므로 실제 자료 구조가 확정되면 해당 형식에 맞는 명시적 헤더 설정을 추가하는 것이 낫다. Parser는 이미 문자열 컬럼명이 있는 DataFrame을 다시 헤더 승격하지 않는다.

### 정제 정책과 손실 가능성

- `DataCleaner()`의 기본 결측 처리 전략은 **`keep`**. 검증 후 행을 자동으로 제거하지 않는다.
- `DataCleaner('drop')`은 결측치가 있는 행 전체를 삭제하므로 건수가 줄어든다.
- `fill_zero`는 수치 dtype에만 `0`을 채운다. 문자열·날짜·식별자에 0을 넣지 않는다.
- `fill_mean`은 수치 dtype만 평균으로 채운다. 모든 값이 비어 있다면 평균을 구할 수 없어 결측을 유지한다.
- CSV 숫자는 원본에서는 문자열(`object`)일 수 있다. `check_types({'매출':'numeric'})`는 값이 숫자로 해석 가능한지 확인해 통과시킬 수 있으나 **값을 변환하지 않는다.** `fill_mean`도 dtype이 수치가 아니라면 적용하지 않는다. 숫자 변환은 별도 정책이 필요하다.
- `remove_duplicates`는 기본적으로 **모든 컬럼 값이 같은 행**을 하나로 만든다. 개별 가맹점 식별용 일부 컬럼만 subset으로 사용하면 다른 레코드를 삭제할 위험이 있다.

## 4. 직접 실행하는 입력/출력 예시

```python
from io import BytesIO
from dashboard.config.settings import AppConfig
from dashboard.data.loader import ExcelLoader
from dashboard.data.parser import SheetParser
from dashboard.data.validator import DataValidator
from dashboard.data.cleaner import DataCleaner

# 실제 개인정보를 사용하지 않는 예시 CSV. Streamlit 업로드와 같은 bytes 입력이다.
content = '자치구,업종,가맹점명\n중구,카페,가상가게A\n마포구,음식,가상가게B\n'.encode('utf-8')
source = BytesIO(content)

loader = ExcelLoader(AppConfig())
sheets = loader.load(source)               # {'Sheet1': DataFrame}
parsed = SheetParser().parse(sheets['Sheet1'])
status = DataValidator(required_columns=['자치구', '업종']).validate(parsed)

if status.is_valid:
    cleaned = DataCleaner().clean(parsed)  # DataFrame
    print(cleaned)
else:
    print(status.errors)
```

이 예시가 `DashboardApp._handle_file_upload()`가 하는 일의 핵심이다. 새 파이프라인 클래스를 만들지 않았으며 조립 책임도 상위 계층에 남겼다.

## 5. 테스트 실행·범위·제약

### 설치/실행 (Windows PowerShell, VS Code 터미널)

```powershell
# 저장소 루트에서 실행
py -m pip install -r requirements.txt
py -m pip install pytest
py -m pytest -q tests/test_data_layer.py
py -m streamlit run dashboard/app.py
```

실행 환경이 다른 경우 `py` 대신 `python`을 사용한다. `.xls`는 `xlrd>=2.0.1`, `.xlsx`는 `openpyxl`이 필요하다. Excel 파일 쓰기는 테스트 데이터 생성에만 `openpyxl`을 사용하며, 앱에 새로운 저장/다운로드 기능을 추가하지 않았다.

### 수행한 테스트

정상 XLSX, 여러 시트, 빈 시트, CSV 경로, 세미콜론·탭, 한글 인코딩(UTF-8/UTF-8 BOM/CP949), 버퍼·커서 보존, 확장자 위장, 바이너리 손상, 파일 용량 제한, 메타데이터 행, 헤더 중복 처리 방지, 필수 컬럼 누락, 데이터 타입 불일치, 필수/선택 결측치, 원본 불변, 정제 전략, 중복 삭제, 모델·필터 계층과 결과 호환, `.xls` 미설치 안내 등을 검사한다.

**작성 환경 확인 결과:** `28 passed`, `pandas 2.2.3`, `openpyxl 3.1.5`, `pytest 9.0.2`. 다만 GitHub 저장소 전체를 현재 실행 환경에 Clone하지 못하여, GitHub에서 확인한 파일의 공개 인터페이스에 맞춘 테스트용 `AppConfig`·`Dataset`·`DataFilter` 대역 코드와 실제 구현 파일을 함께 실행했다. 따라서 **전체 Streamlit 앱 통합 테스트 결과로 표현하면 안 된다.** 현재 환경에 `xlrd`가 없어서 **실제 `.xls` 정상 파일 읽기**는 검증하지 못했고, 미설치 안내 경로만 검증했다. 실제 프로젝트 PC에서 `pip install -r requirements.txt` 후 위 테스트와 업로드 UI를 재확인해야 한다.

## 6. Git 브랜치 생성 → 로컬 커밋 → 필요 시 Push/PR

**현재 산출물은 코드 파일 묶음이다. 원격 저장소에 직접 Push하거나 PR/Merge하지 않았다.**

PowerShell이나 VS Code의 **터미널**에서 아래 순서로 진행한다.

### A. 저장소 처음 가져오는 경우

```powershell
git clone https://github.com/2026-KW-OOP/dashboard.git
cd dashboard
```

`git clone`은 원격 저장소의 복사본을 내 PC로 내려받는다. `cd`는 프로젝트 폴더로 이동한다.

### B. 이미 Clone한 경우

```powershell
cd "내가_저장한_경로\dashboard"
git status
git branch --show-current
```

`git status`는 수정/추가된 파일이 있는지, `git branch --show-current`는 현재 브랜치를 확인한다. **남의 변경이나 내가 아직 커밋하지 않은 파일이 보이면 임의로 삭제·덮어쓰지 않는다.** 충돌 가능성이 있다면 수정 파일을 확인하고 팀원과 먼저 조율한다.

### C. 최신 main 받아오기

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
```

- `fetch`: 원격 브랜치 정보를 로컬에 가져오지만 작업 파일은 자동으로 병합하지 않는다.
- `switch main`: 작업 기준 브랜치를 `main`으로 이동한다.
- `pull --ff-only`: 빠른 전진 병합이 가능할 때만 업데이트한다. 로컬에 별도 커밋이 있어 충돌하는 경우 중단하므로 안전하다.

**`git status`에 미완성 작업이 있으면 먼저 보존한 다음에 브랜치를 바꾼다.** 절대로 무작정 `git reset --hard`, `git clean -fd`를 실행하지 않는다.

### D. 기능 브랜치 생성

```powershell
git switch -c feat/data-layer-io
```

이미 같은 이름의 로컬 브랜치가 있다면 위 명령은 실패한다. 그때는 다음을 사용한다.

```powershell
git branch --list feat/data-layer-io
git branch -r --list origin/feat/data-layer-io
git switch feat/data-layer-io
```

로컬에는 없고 원격에만 존재하면 다음처럼 연결한다.

```powershell
git switch -c feat/data-layer-io --track origin/feat/data-layer-io
```

### E. 작성한 파일만 복사하고 변경 내용 확인

이 ZIP의 `dashboard/data/` 네 파일과 `tests/test_data_layer.py`, `docs/DATA_LAYER_GUIDE.md`, `requirements.txt`를 저장소 **같은 상대 경로**에 복사한다. `requirements.txt`를 덮어쓰기 전에는 팀원의 최근 변경 여부를 비교한다. 팀원이 새 의존성을 추가했다면 **해당 파일 전체를 덮어쓰지 말고 `xlrd>=2.0.1` 한 줄만 합친다.**

```powershell
git status
git diff -- dashboard/data/ requirements.txt
git diff --check
```

`git diff`는 실제 변경된 줄을, `git diff --check`는 공백 오류를 검사한다.

### F. 선택적 Add / Commit

```powershell
git add dashboard/data/loader.py dashboard/data/parser.py dashboard/data/validator.py dashboard/data/cleaner.py
git add tests/test_data_layer.py docs/DATA_LAYER_GUIDE.md requirements.txt
git diff --cached --stat
git diff --cached
git commit -m "feat(data): implement data layer I/O and preprocessing"
```

- `add`는 지정한 파일만 다음 커밋 대상으로 올린다. `git add .`는 사용하지 않는다.
- `diff --cached`는 실제로 커밋될 내용을 검토한다.
- `commit`은 **내 PC의 해당 브랜치에만** 기록한다. 원격 GitHub에는 아직 반영되지 않는다.

### G. 명시적으로 원격에 올리기로 결정한 뒤 Push

```powershell
git push -u origin feat/data-layer-io
```

`-u`는 이후 이 로컬 브랜치의 기본 원격 추적 대상을 설정한다. GitHub 계정 로그인과 인증이 필요하고 조직 저장소 쓰기 권한이 있어야 한다. 권한 오류가 나면 팀 저장소 관리자에게 권한을 확인하거나, 허용되면 개인 Fork에서 PR을 제안한다. **`--force`는 사용하지 않는다.**

충돌이 나면 현재 작업을 먼저 커밋·보존하고 `git fetch origin`, `git status`, `git log --oneline --graph --all -10` 등으로 양쪽 작업을 확인한다. 원격의 최신 커밋을 안전하게 병합 또는 리베이스하는 방법을 팀원과 정한다. 임의로 상대방 커밋을 제거하거나 강제 Push하지 않는다.

### H. PR 생성 (사용자 승인 뒤 GitHub 웹에서)

GitHub 저장소 → **Pull requests** → **New pull request** → **base: main**, **compare: feat/data-layer-io** → **Create pull request**.

**PR 제목 예시**

`feat(data): implement data layer I/O and preprocessing`

**PR 본문 예시**

```text
## 변경 내용
- Excel(.xlsx/.xls)/CSV 업로드 및 다중 시트 로딩
- 파일 형식/인코딩/빈 파일 확인, 원본 버퍼 위치 보존
- 헤더·메타데이터 파싱, 검증 결과, 결측/중복 정제
- Data Layer 단위 테스트와 발표용 설명 추가
- .xls 지원을 위해 xlrd 의존성 추가

## 테스트
- 합성 샘플 데이터 기반 pytest 28개 통과(별도 구현 검증 환경)
- 실제 저장소에서는 재실행 및 Streamlit 업로드 수동 확인 필요
- 실제 .xls 파일 검증은 xlrd 설치 후 수행 필요

## 리뷰 요청
- 실제 가맹점 파일의 헤더 구조와 필수 컬럼 정책
- 한글 컬럼명 보존(자치구, 업종)이 UI에 적합한지
- 기본 결측치 유지(keep), 중복 제거 정책이 서비스 요구에 적합한지
```

## 7. 객체지향 프로그래밍 원칙

- **단일 책임(SRP)**: Loader는 읽기만, Parser는 표 구조만, Validator는 검사만, Cleaner는 정제만 수행한다.
- **캡슐화**: 외부에서는 `load`, `parse`, `validate`, `clean`만 호출하면 된다. 내부의 `_detect_format`, `_read_csv`, `_read_excel`은 구현 상세를 감춘다.
- **추상화**: Excel/CSV의 서로 다른 읽기 로직을 `load`라는 공통 인터페이스로 묶는다. 호출자는 파일 종류에 따른 pandas 인수를 알 필요가 없다.
- **의존성 주입(DI)**: Loader는 `AppConfig`를 생성자에서 받는다. 따라서 테스트에서는 파일 크기 설정이 작은 `AppConfig`를 전달할 수 있다.
- **재사용성**: UI 없이도 `BytesIO` 파일 입력과 DataFrame 검사·정제가 가능하다.
- **확장성**: 새 파일 형식은 Loader 내부 분기와 판정 추가, 새 결측치 방식은 Cleaner의 전략 분기에 추가한다.
- **상속 대신 합성**: 상위 `DashboardApp`이 네 객체를 소유하고 순서대로 호출한다. 이번 문제에 필요한 이유 없이 상속 구조를 늘리지 않았다.

## 8. 교수님 예상 질문과 답변

1. **왜 Data Layer를 따로 만들었나요?** 파일 형식 처리와 시각화 책임을 분리하면 화면 변경이 로더에 영향을 덜 미치고 테스트도 쉬워집니다.
2. **왜 pandas를 썼나요?** 엑셀/CSV를 공통 표 구조인 DataFrame으로 읽고 결측치/중복/필터 작업을 같은 API로 처리할 수 있기 때문입니다.
3. **왜 두 파일 형식을 모두 `dict[str, DataFrame]`으로 반환하나요?** 엑셀은 여러 시트가 있고 CSV는 하나뿐인데, 호출자가 파일 형식별로 분기하지 않도록 입력 인터페이스를 통일하기 위해서입니다.
4. **왜 `BytesIO`가 필요하나요?** Streamlit 업로드가 메모리 버퍼 형태로 들어오고, pandas에 임시 파일 없이 바이너리 파일 객체를 전달할 수 있기 때문입니다.
5. **파일 확장자만 믿으면 안 되나요?** 확장자만 바꾼 손상·위장 파일이 들어올 수 있어 ZIP/OLE 매직바이트와 CSV 텍스트 판정도 합니다.
6. **Excel과 CSV의 차이는 무엇인가요?** Excel은 워크북/시트가 있고 엔진(openpyxl/xlrd)이 필요합니다. CSV는 텍스트라 인코딩과 구분자를 알아야 합니다.
7. **왜 `header=None`으로 읽나요?** 표 위에 제목·설명 행이 있을 수 있어 Loader가 첫 행을 헤더로 확정하지 않도록 한 것입니다.
8. **헤더는 항상 정확히 찾나요?** 아닙니다. 문자열 비율에 근거한 휴리스틱이며 복잡한 병합·다단 헤더에는 별도 규칙이 필요합니다.
9. **Validator와 Cleaner 차이는 무엇인가요?** Validator는 오류/경고를 보고하며 데이터를 바꾸지 않습니다. Cleaner는 정제된 새 DataFrame을 반환합니다.
10. **왜 `ValidationResult` 객체를 반환하나요?** 참/거짓뿐 아니라 오류와 경고의 구체적 목록을 상위 UI에서 각각 표시할 수 있기 때문입니다.
11. **왜 오류와 경고를 구분하나요?** 필수 컬럼이 없으면 작업을 막아야 하지만 선택 컬럼 결측치 정도는 사용자에게 알리고 계속할 수 있기 때문입니다.
12. **원본 DataFrame은 변경되나요?** 아니요. Parser/Cleaner가 복제본에서 연산합니다. 검증은 읽기만 합니다.
13. **결측치를 모두 0으로 채우지 않는 이유는 무엇인가요?** 결측과 실제 0은 다른 의미이며 문자열/날짜 컬럼에 0을 넣으면 잘못된 해석이 되기 때문입니다.
14. **중복 제거가 위험할 수 있나요?** 네. 서로 다른 거래가 우연히 같은 값을 가지는 경우도 있으므로 도메인 식별키와 요구사항을 확인해야 합니다.
15. **객체지향 원칙은 어디에 적용했나요?** 역할별 클래스 분리(SRP), 메서드로 구현 숨김(캡슐화), `AppConfig` 전달(DI), DashboardApp의 객체 조합을 적용했습니다.
16. **`try-except`가 필요한 이유는 무엇인가요?** 손상된 파일, 미설치 엔진, 잘못된 인코딩 등 외부 입력 오류를 앱이 안내할 수 있는 예외로 전환하기 위해서입니다.
17. **`.xls`를 위해 `xlrd`가 필요한 이유는 무엇인가요?** 오래된 `.xls`는 `.xlsx`와 내부 형식이 달라 `openpyxl`로 처리할 수 없기 때문입니다.
18. **테스트는 어디까지 확인했나요?** 데이터 계층 28개 자동화 테스트를 실행했습니다. Streamlit 전체 실행과 실제 정상 `.xls` 통합 검증은 프로젝트 환경에서 추가 확인해야 합니다.

## 9. 2~3분 발표 스크립트

안녕하세요. 저는 객체지향 프로그래밍 팀 프로젝트에서 **Data Layer**, 특히 파일의 입력과 출력 부분을 담당했습니다.

이 프로젝트는 사용자가 업로드한 Excel 또는 CSV 데이터를 웹 대시보드에서 시각화하는 프로그램입니다. 데이터 계층은 화면에 데이터를 보여주기 전에 **읽고, 표 구조를 맞추고, 검사하고, 정리된 DataFrame을 전달하는 역할**을 합니다. 저는 단일 책임 원칙에 따라 이 과정을 네 개 클래스로 나눴습니다.

첫 번째 **ExcelLoader**는 파일 경로나 Streamlit 업로드 버퍼를 입력으로 받습니다. 확장자와 실제 파일 바이트를 확인해 Excel인지 CSV인지 구분합니다. Excel은 pandas의 `read_excel`을 통해 여러 시트를 한 번에 읽고, CSV는 인코딩과 구분자를 판별해 `read_csv`로 읽습니다. 결과는 모든 파일 형식에서 일관되게 **시트명을 키로, DataFrame을 값으로 가지는 딕셔너리**입니다. Streamlit 업로드 데이터를 다루기 위해 `BytesIO`를 사용했고, 업로드 파일의 커서 위치는 바꾸지 않도록 했습니다.

두 번째 **SheetParser**는 읽은 표의 구조를 정리합니다. 엑셀 맨 위에는 보고서 제목이나 설명이 있을 수 있기 때문에, Loader에서 첫 행을 헤더로 확정하지 않습니다. Parser가 빈 행과 열을 제거하고 실제 헤더 위치를 추정해 컬럼명을 지정합니다. 이 단계의 결과는 컬럼명과 인덱스가 정돈된 DataFrame입니다.

세 번째 **DataValidator**는 데이터가 사용 가능한 상태인지 검사합니다. 필수 컬럼이 있는지, 기대하는 타입에 맞는지, 필수 데이터에 결측치가 있는지 확인하고, `ValidationResult`에 오류와 경고를 나누어 반환합니다. 이 클래스는 원본 데이터를 수정하지 않으므로 문제가 발생한 이유를 안전하게 확인할 수 있습니다.

네 번째 **DataCleaner**는 컬럼명을 일관된 형식으로 바꾸고, 선택된 전략에 따라 결측치와 중복 행을 정리합니다. 기존 화면이 사용하는 `자치구`, `업종`이라는 한글 컬럼명은 보존하며, 원본 대신 새로운 DataFrame을 반환합니다.

마지막으로 DashboardApp이 이 네 단계를 순서대로 연결하고, 결과를 Dataset에 넣어 필터 및 시각화 계층으로 넘깁니다. 객체지향 관점에서는 **책임 분리, 캡슐화, 설정 의존성 주입**을 구현했고, 가상의 샘플 파일로 다양한 입력·오류·정제 상황을 자동 테스트했습니다. 이상입니다.
