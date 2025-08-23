import sys
import types
import contextlib
import pytest

from apps.orchestrator import executor
from core.planning.task_graph import PlanNode, TaskGraph

class DummyScope:
    def __init__(self):
        self.tags = {}
    def set_tag(self, key, value):
        self.tags[key] = value


@pytest.mark.asyncio
async def test_sentry_capture_on_node_exception(monkeypatch, tmp_path):
    monkeypatch.setenv("RUNS_ROOT", str(tmp_path))
    monkeypatch.setenv("SENTRY_DSN", "http://dummy")

    captured = []
    scopes = []

    @contextlib.contextmanager
    def push_scope():
        scope = DummyScope()
        scopes.append(scope)
        yield scope

    def capture_exception(exc):
        captured.append(exc)

    sentry_stub = types.SimpleNamespace(push_scope=push_scope, capture_exception=capture_exception)
    monkeypatch.setitem(sys.modules, "sentry_sdk", sentry_stub)

    async def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(executor, "_execute_node", boom)

    node = PlanNode(id="n1", title="Test", type="execute", suggested_agent_role="role", llm={"provider": "prov", "model": "m1"})
    dag = TaskGraph([node])

    await executor.run_graph(dag, storage=None, run_id="r1")

    assert captured, "capture_exception should be called"
    scope = scopes[0]
    assert scope.tags.get("run_id") == "r1"
    assert scope.tags.get("node_id") == "n1"
    assert scope.tags.get("provider") == "prov"
    assert scope.tags.get("model") == "m1"


@pytest.mark.asyncio
async def test_no_sentry_without_dsn(monkeypatch, tmp_path):
    monkeypatch.setenv("RUNS_ROOT", str(tmp_path))
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    captured = []

    @contextlib.contextmanager
    def push_scope():
        yield DummyScope()

    def capture_exception(exc):
        captured.append(exc)

    sentry_stub = types.SimpleNamespace(push_scope=push_scope, capture_exception=capture_exception)
    monkeypatch.setitem(sys.modules, "sentry_sdk", sentry_stub)

    async def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(executor, "_execute_node", boom)

    node = PlanNode(id="n1", title="Test", type="execute", suggested_agent_role="role")
    dag = TaskGraph([node])

    await executor.run_graph(dag, storage=None, run_id="r1")

    assert captured == []
