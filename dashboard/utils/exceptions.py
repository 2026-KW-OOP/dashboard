"""커스텀 예외.

각 예외가 어디서 발생시켜야 하는지는 [dashboard_design.md](../../dashboard_design.md) 4.1절 참고.
아직 이 예외들을 실제로 raise하는 코드는 없다 — 아래 각 계층 로직을 채울 때
해당 지점에서 사용하면 된다.
"""


class DashboardError(Exception):
    """대시보드 예외 공통 기반."""


class InvalidFileFormatError(DashboardError):
    """지원하지 않는 파일 확장자.

    발생 지점(예정): data/loader.py의 _detect_format() — 확장자/매직바이트로도
    xlsx/xls/csv 중 어느 것도 아니라고 판정됐을 때.
    """


class SchemaValidationError(DashboardError):
    """컬럼 스키마 불일치.

    발생 지점(예정): data/validator.py의 validate() — 필수 컬럼 누락이나
    타입 불일치처럼 "경고"가 아니라 "치명적 오류"로 취급해야 할 때.
    """


class EmptyDatasetError(DashboardError):
    """빈 시트 또는 필터 결과 없음.

    발생 지점(예정): data/loader.py(시트 자체가 비었을 때) 또는
    services/filter.py의 apply()(필터 적용 후 남은 행이 0개일 때).
    """


class ChartRenderError(DashboardError):
    """차트 생성 실패.

    발생 지점(예정): visualization/builders/base.py의 _validate_spec()
    (ChartSpec에 필수 필드가 비어 있을 때) 또는 visualization/factory.py의
    create()(등록되지 않은 chart_type이 들어왔을 때).
    """
