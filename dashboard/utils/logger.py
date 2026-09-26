"""표준 로깅 설정."""
from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """포맷·핸들러가 통일된 로거를 반환한다.

    입력: name — 로거 이름, 보통 호출하는 모듈의 __name__을 넘긴다
          (예: dashboard/data/loader.py에서 get_logger(__name__)).
    동작: 같은 이름의 로거가 이미 핸들러를 갖고 있으면 그대로 재사용하고,
          없으면 시각·레벨·이름·메시지를 포함한 포맷의 StreamHandler를 붙인다.
    반환: 설정이 끝난 logging.Logger 인스턴스. 이후 logger.info(...) /
          logger.warning(...) / logger.error(...)로 각 계층에서 그대로 사용한다.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
