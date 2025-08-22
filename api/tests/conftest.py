import sys
from pathlib import Path

try:
    from tests_api.conftest import *  # noqa: F401,F403
    from tests_api.conftest import _dispose_engine  # noqa: F401
except ImportError:  # pragma: no cover - fallback when tests_api not on path
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tests_api.conftest import *  # noqa: F401,F403
    from tests_api.conftest import _dispose_engine  # noqa: F401
