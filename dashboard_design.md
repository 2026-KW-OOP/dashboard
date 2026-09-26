# Excel 데이터 시각화 대시보드 설계 문서

## 1. 개요

Excel 파일(`.xlsx`, `.xls`, `.csv`)을 입력으로 받아 웹 기반 인터랙티브 대시보드로 시각화하는 파이썬 애플리케이션의 설계 문서. 구현은 포함하지 않으며, 각 모듈·클래스·함수의 책임과 인터페이스를 정의한다.

### 1.1 기술 스택 (권장)

- **데이터 처리**: `pandas`, `openpyxl`, `pyarrow`
- **시각화**: `plotly` (인터랙티브 차트)
- **UI 프레임워크**: `streamlit`
- **검증**: `pydantic`
- **로깅**: 표준 `logging`

### 1.2 설계 원칙

- **계층 분리**: 데이터 로딩 / 처리 / 시각화 / 프레젠테이션을 독립 계층으로 분리
- **단일 책임**: 각 클래스는 하나의 책임만 가진다
- **의존성 역전**: 상위 계층은 인터페이스에만 의존
- **테스트 용이성**: UI와 무관하게 데이터 계층을 단독 테스트 가능

---

## 2. 아키텍처 계층

```
┌─────────────────────────────────────────┐
│  Presentation Layer (Streamlit     )    │  ← 사용자 상호작용
├─────────────────────────────────────────┤
│  Visualization Layer (Chart Builders)   │  ← Plotly Figure 생성
├─────────────────────────────────────────┤
│  Service Layer (Filter)                 │  ← 비즈니스 로직
├─────────────────────────────────────────┤
│  Data Layer (Load/Validate/Clean)       │  ← Excel I/O
├─────────────────────────────────────────┤
│  Config & Utils (공통 기반)              │
└─────────────────────────────────────────┘
```

---

## 3. 디렉터리 구조

```
dashboard/
├── app.py                    # 진입점
├── config/
│   ├── settings.py           # AppConfig
│   └── theme.py              # ThemeConfig
├── data/
│   ├── loader.py             # ExcelLoader
│   ├── parser.py             # SheetParser
│   ├── validator.py          # DataValidator
│   └── cleaner.py            # DataCleaner
├── models/
│   └── dataset.py            # Dataset
├── services/
│   └── filter.py             # DataFilter
├── visualization/
│   ├── factory.py            # ChartFactory
│   ├── builders/             # 차트별 Builder
├── ui/
│   ├── layout.py             # PageLayout
│   ├── sidebar.py            # View
└── utils/
    ├── logger.py
    └── exceptions.py
```

---

## 4. 계층별 상세 설계

### 4.1 Config & Utils

#### `AppConfig` (config/settings.py)
애플리케이션 전역 설정 관리.
- **역할**: 파일 경로, 최대 업로드 크기, 캐시 TTL, 로그 레벨 등을 중앙 관리
- **주요 속성**: `upload_max_size_mb`, `allowed_extensions`, `default_sheet_index`
- **로드 방식**: 기본값으로 직접 생성 (`AppConfig()`).

#### `ThemeConfig` (config/theme.py)
시각적 테마 정의.
- **역할**: 컬러 팔레트, 폰트, 차트 기본 스타일을 한 곳에서 관리
- **주요 속성**: `primary_color`, `palette`, `font_family`, `chart_template`
- **사용처**: 모든 `ChartBuilder`가 참조하여 일관된 룩앤필 보장

#### `Logger` (utils/logger.py)
- **역할**: 표준 로깅 설정. 포맷·핸들러 통일
- **주요 함수**: `get_logger(name: str) -> logging.Logger`

#### 커스텀 예외 (utils/exceptions.py)
- `InvalidFileFormatError`: 지원하지 않는 파일 확장자
- `SchemaValidationError`: 컬럼 스키마 불일치
- `EmptyDatasetError`: 빈 시트 또는 필터 결과 없음
- `ChartRenderError`: 차트 생성 실패

---

### 4.2 Data Layer

#### `ExcelLoader` (data/loader.py)
Excel/CSV 파일을 읽어 원시 DataFrame으로 변환.

| 메서드 | 역할 |
|---|---|
| `__init__(config: AppConfig)` | 설정 주입 |
| `load(file_path: str \| BytesIO) -> dict[str, DataFrame]` | 모든 시트를 딕셔너리로 반환 (`{시트명: DataFrame}`) |
| `list_sheets(file_path) -> list[str]` | 시트 목록만 미리 조회 (미리보기용) |
| `_detect_format(file_path) -> str` | 확장자·매직바이트로 포맷 판정 |
| `_read_excel(...)` | `openpyxl` 엔진 기반 실제 읽기 |
| `_read_csv(...)` | 인코딩·구분자 자동 탐지 후 CSV 읽기 |

**책임 경계**: 파일을 읽는 데만 집중. 검증·정제는 하지 않음.

#### `SheetParser` (data/parser.py)
로드된 시트에서 헤더·데이터 영역을 식별.

| 메서드 | 역할 |
|---|---|
| `parse(df: DataFrame) -> DataFrame` | 빈 행/열 제거, 헤더 행 탐지, 인덱스 정규화 |
| `detect_header_row(df) -> int` | 실제 헤더가 시작되는 행 번호 반환 |
| `strip_metadata_rows(df) -> DataFrame` | 상단 메타데이터(제목·설명 등) 제거 |

#### `DataValidator` (data/validator.py)
스키마·데이터 타입 검증.

| 메서드 | 역할 |
|---|---|
| `validate(df: DataFrame) -> ValidationResult` | 컬럼 존재 여부·타입·필수값 검증 |
| `check_required_columns(df, required: list[str])` | 필수 컬럼 누락 확인 |
| `check_types(df, type_map: dict)` | 컬럼별 dtype 검증 |

**반환**: `ValidationResult(is_valid: bool, errors: list, warnings: list)`

#### `DataCleaner` (data/cleaner.py)
정제·전처리.

| 메서드 | 역할 |
|---|---|
| `clean(df: DataFrame) -> DataFrame` | 파이프라인 실행 (아래 메서드 순차 호출) |
| `normalize_column_names(df)` | 공백·특수문자 제거, snake_case 변환 |
| `handle_missing(df, strategy: str)` | 결측치 처리 (`drop`, `fill_zero`, `fill_mean` 등) |
| `remove_duplicates(df, subset: list \| None)` | 중복 제거 |

---

### 4.3 Model Layer

#### `Dataset` (models/dataset.py)
정제된 데이터 + 메타데이터를 담는 컨테이너.

- **속성**: `df: DataFrame`, `source_file: str`, `loaded_at: datetime`
- **메서드**:
  - `get_unique_values(column: str) -> list[str]`: 특정 컬럼의 중복 없는 값 목록
    (결측치 제외, 문자열로 변환 후 정렬). 사이드바 필터의 `st.multiselect` 선택지로 쓰임

---

### 4.4 Service Layer

#### `DataFilter` (services/filter.py)
사이드바 필터 조건을 DataFrame에 적용.

| 메서드 | 역할 |
|---|---|
| `apply(df: DataFrame, filters: list[FilterCondition]) -> DataFrame` | 모든 필터 순차 적용 |
| `filter_by_categories(df, column, values)` | 다중 선택 필터 |
| `filter_by_search(df, column, keyword)` | 문자열 부분 일치 |

**`FilterCondition`**: 데이터클래스. `column`, `operator`, `value`.

---

### 4.5 Visualization Layer

#### `ChartBuilder` (visualization/builders/base.py) — 추상 기본 클래스
모든 차트 빌더의 공통 인터페이스.

| 메서드 | 역할 |
|---|---|
| `__init__(theme: ThemeConfig)` | 테마 주입 |
| `build(df: DataFrame, spec: ChartSpec) -> Figure` | (추상) 실제 Plotly Figure 반환 |
| `_apply_theme(fig: Figure) -> Figure` | 공통 스타일 적용 (색상·폰트·여백) |
| `_validate_spec(spec: ChartSpec)` | 스펙 유효성 검사 |

**구체 클래스 (visualization/builders/)**:

| 클래스 | 역할 |
|---|---|
| `BarChartBuilder` | 막대 차트 (수직/수평, 스택/그룹) |
| `PieChartBuilder` | 파이·도넛 차트 (비중 시각화) |
| `TableBuilder` | 인터랙티브 데이터 테이블 |

**`ChartSpec`**: 차트 구성 스펙. `chart_type`, `x`, `y`, `color`, `size`, `title`, `agg_func`, `orientation` 등.

#### `ChartFactory` (visualization/factory.py)
Spec에 맞는 Builder를 반환하는 팩토리.

| 메서드 | 역할 |
|---|---|
| `create(spec: ChartSpec) -> ChartBuilder` | 차트 타입에 해당하는 Builder 인스턴스 반환 |
| `available_types() -> list[str]` | 지원 차트 타입 목록 |
| `recommend(dataset: Dataset) -> list[ChartSpec]` | 데이터 스키마 기반 차트 자동 추천 |

---

### 4.6 Presentation Layer (UI)

#### `DashboardApp` (app.py)
애플리케이션 진입점.

| 메서드 | 역할 |
|---|---|
| `__init__(config: AppConfig)` | 의존성 조립 (DI 컨테이너 역할) |
| `run()` | 앱 실행 루프 |
| `_handle_file_upload(file) -> Dataset` | 업로드 → Loader → Parser → Validator → Cleaner → Dataset 파이프라인 조율 |

#### `SidebarComponent` (ui/sidebar.py)
좌측 사이드바: 파일 업로드·필터·설정.

| 메서드 | 역할 |
|---|---|
| `render(dataset: Dataset \| None) -> SidebarState` | 사이드바 위젯을 그리고 사용자 입력 반환 |
| `_render_file_uploader()` | 업로드 UI |
| `_render_sheet_selector(sheets: list)` | 시트 선택 드롭다운 |
| `_render_filters(dataset: Dataset) -> list[FilterCondition]` | 컬럼별 필터 위젯 동적 생성 |
| `_render_theme_toggle()` | 라이트/다크 모드 전환 |

**`SidebarState`**: 데이터클래스. `selected_sheet`, `filters`, `theme_mode`.

#### `PageLayout` (ui/layout.py)
전체 페이지 배치 관리.

| 메서드 | 역할 |
|---|---|
| `render(dataset, sidebar_state)` | 헤더·탭·본문·푸터 조립 |
| `_render_header(dataset)` | 파일명·마지막 업데이트 시간 표시 |
| `_render_empty_state()` | 파일 미업로드 시 안내 화면 |

---

## 5. 데이터 흐름 (End-to-End)

```
1. 사용자 파일 업로드
   ↓
2. ExcelLoader.load()          → {sheet: DataFrame}
   ↓
3. SheetParser.parse()         → 정규화된 DataFrame
   ↓
4. DataValidator.validate()    → ValidationResult (실패 시 UI 경고)
   ↓
5. DataCleaner.clean()         → 정제된 DataFrame
   ↓
7. Sidebar에서 필터 입력 → SidebarState
   ↓
8. DataFilter.apply()          → 필터링된 DataFrame
   ↓
9. ChartFactory.create() → ChartBuilder.build() → Plotly Figure
   ↓
10. Figure를 렌더링
```

---

## 6. 확장 지점

- **새 차트 추가**: `ChartBuilder` 상속 → `ChartFactory`에 등록만 하면 됨

---