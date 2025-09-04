import sys
from pathlib import Path

try:
    from tests.api.conftest import *  # noqa: F401,F403
    from tests.api.conftest import _dispose_engine  # noqa: F401
except ImportError:  # pragma: no cover - fallback when package not on path
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tests.api.conftest import *  # noqa: F401,F403
    from tests.api.conftest import _dispose_engine  # noqa: F401
