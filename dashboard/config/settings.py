"""애플리케이션 전역 설정."""
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    """파일 경로, 업로드 크기, 캐시 TTL, 로그 레벨 등을 중앙 관리한다."""

    upload_max_size_mb: int = 200
    allowed_extensions: list[str] = field(default_factory=lambda: [".xlsx", ".xls", ".csv"])
    default_sheet_index: int = 0
    log_level: str = "INFO"