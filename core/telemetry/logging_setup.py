import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


class _RunIdFilter(logging.Filter):
    def __init__(self, run_id: str):
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self.run_id
        return True


def setup_logging(run_dir: str, logger_name: str = "crew", *, to_stdout: bool = True, run_id: str | None = None) -> logging.Logger:
    """Configure un logger préfixant les messages par le run_id."""

    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    run_id = run_id or Path(run_dir).name
    log_path = Path(run_dir) / "orchestrator.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    # reset handlers (utile en tests)
    for h in list(logger.handlers):
        logger.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(run_id)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_filter = _RunIdFilter(run_id)

    file_h = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_h.setLevel(level)
    file_h.setFormatter(fmt)
    file_h.addFilter(run_filter)
    logger.addHandler(file_h)

    if to_stdout and os.getenv("LOG_TO_STDOUT", "1") == "1":
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(fmt)
        sh.addFilter(run_filter)
        logger.addHandler(sh)

    logger.debug("logging initialized (level=%s, path=%s)", level_name, log_path)
    return logger

