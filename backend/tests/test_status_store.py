import os
from core.storage.file_adapter import FileStatusStore, NodeStatus

def test_status_store_roundtrip(tmp_path, monkeypatch):
    runs_root = tmp_path / ".runs"
    store = FileStatusStore(runs_root=str(runs_root))
    run_id = "runA"
    node = "N1"

    # Écriture initiale (pending)
    st0 = NodeStatus.new_pending(run_id, node, input_checksum="sha256:abc")
    store.write(st0)
    st = store.read(run_id, node)
    assert st is not None and st.status == "pending"

    # in_progress
    store.mark_in_progress(run_id, node)
    st = store.read(run_id, node)
    assert st.status == "in_progress"
    assert st.attempts == 1
    assert st.started_at

    # failed
    store.mark_failed(run_id, node, "boom")
    st = store.read(run_id, node)
    assert st.status == "failed"
    assert "boom" in st.error

    # in_progress -> completed
    store.mark_in_progress(run_id, node)
    store.mark_completed(run_id, node)
    st = store.read(run_id, node)
    assert st.status == "completed"
    assert st.ended_at
