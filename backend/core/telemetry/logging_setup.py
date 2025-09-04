import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(run_dir: str, logger_name: str = "crew", *, to_stdout: bool = True) -> logging.Logger:
    """
    Configure un logger 'crew' avec :
      - niveau depuis LOG_LEVEL (default INFO)
      - fichier .runs/<run_id>/orchestrator.log (rotation 1 Mo x 3)
      - console (stdout) optionnelle
    """
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_path = Path(run_dir) / "orchestrator.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # pas d’héritage root

    # clear handlers si relance dans le même process (pytest)
    for h in list(logger.handlers):
        logger.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_h = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_h.setLevel(level)
    file_h.setFormatter(fmt)
    logger.addHandler(file_h)

    if to_stdout and os.getenv("LOG_TO_STDOUT", "1") == "1":
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    logger.debug("logging initialized (level=%s, path=%s)", level_name, log_path)
    return logger
