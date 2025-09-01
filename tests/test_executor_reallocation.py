import uuid
import pytest

from core.planning.task_graph import PlanNode, TaskGraph
from apps.orchestrator import executor as exec_mod

class DummyStorage:
    async def save_run(self, *a, **kw):
        pass
    async def save_node(self, *a, **kw):
        pass
    async def save_artifact(self, *a, **kw):
        pass

@pytest.mark.asyncio
async def test_reallocation_success(monkeypatch):
    calls = []
    async def fake_exec(node, *args, **kwargs):
        calls.append(node.suggested_agent_role)
        if node.suggested_agent_role.endswith('_alt'):
            return {}
        raise RuntimeError('boom')
    monkeypatch.setattr(exec_mod, '_execute_node', fake_exec)
    monkeypatch.setenv('NODE_MAX_RETRIES', '0')
    node = PlanNode(id='n1', title='N', type='execute', suggested_agent_role='Writer_FR')
    dag = TaskGraph([node])
    storage = DummyStorage()
    res = await exec_mod.run_graph(dag, storage, str(uuid.uuid4()))
    assert calls == ['Writer_FR', 'Writer_FR_alt']
    assert res['status'] == 'succeeded'

@pytest.mark.asyncio
async def test_reallocation_failure_signal(monkeypatch):
    async def fake_exec(node, *args, **kwargs):
        raise RuntimeError('boom')
    monkeypatch.setattr(exec_mod, '_execute_node', fake_exec)
    monkeypatch.setenv('NODE_MAX_RETRIES', '0')
    node = PlanNode(id='n1', title='N', type='execute', suggested_agent_role='Writer_FR')
    dag = TaskGraph([node])
    storage = DummyStorage()
    res = await exec_mod.run_graph(dag, storage, str(uuid.uuid4()))
    assert res['failed'] == ['n1']
    assert res['signals']
    sig = res['signals'][0]
    assert sig['plan_status'] == 'draft'
    assert sig['report']['attempts'] == 1
