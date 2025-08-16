# tests/test_file_storage_atomic.py
import os
import pytest

from core.storage.file_adapter import FileStorage

@pytest.mark.asyncio
async def test_atomic_write_success(tmp_path):
    base = tmp_path / "run"
    storage = FileStorage(str(base))
    path = await storage.save_artifact("nZ", "HELLO", ext=".txt")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        assert f.read() == "HELLO"

@pytest.mark.asyncio
async def test_atomic_write_failure_does_not_corrupt(tmp_path, monkeypatch):
    base = tmp_path / "run"
    storage = FileStorage(str(base))
    path = os.path.join(str(base), "artifact_nZ.txt")

    # on crée un ancien contenu
    os.makedirs(base, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("OLD")

    # on simule un crash au moment du replace
    import os as _os
    def boom(src, dst):
        raise RuntimeError("replace failed")
    monkeypatch.setattr(_os, "replace", boom, raising=True)

    with pytest.raises(RuntimeError):
        await storage.save_artifact("nZ", "NEW", ext=".txt")

    # l'ancien contenu reste intact
    with open(path, "r", encoding="utf-8") as f:
        assert f.read() == "OLD"
