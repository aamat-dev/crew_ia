import types
import json
from pathlib import Path

import pytest

from orchestrator import recruit_client, hooks_recruit


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        import httpx

        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=self)


class DummyClient:
    def __init__(self, responses, *args, **kwargs):
        self.responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, *args, **kwargs):
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_recruit_retry_and_sidecar(monkeypatch, tmp_path):
    responses = [
        DummyResponse(500, {}),
        DummyResponse(200, {"agent_id": "agent-1", "sidecar": {"x": 1}}),
    ]
    monkeypatch.setattr(
        recruit_client, "httpx", types.SimpleNamespace(AsyncClient=lambda *a, **k: DummyClient(responses))
    )
    node = {}
    await hooks_recruit.handle_missing_role(
        run_id="run42",
        request_id="req-1",
        payload={"role": "executor"},
        node=node,
        runs_root=str(tmp_path),
    )
    assert node["agent_id"] == "agent-1"
    sidecar_file = Path(tmp_path) / "run42" / "sidecars" / "req-1.llm.json"
    assert sidecar_file.exists()
    data = json.loads(sidecar_file.read_text())
    assert data["x"] == 1
