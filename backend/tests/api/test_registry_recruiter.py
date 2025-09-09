import pytest


@pytest.mark.asyncio
async def test_recruiter_registers_dynamic_spec(pg_test_db):
    from core.agents.recruiter import recruit
    from core.agents.registry import resolve_agent

    spec = await recruit("UnknownRole")
    assert spec.role == "UnknownRole"
    assert isinstance(spec.provider, str)
    assert isinstance(spec.model, str)

    resolved = resolve_agent("UnknownRole")
    assert resolved == spec


@pytest.mark.asyncio
async def test_recruiter_known_roles_map_to_db(pg_test_db):
    from core.agents.recruiter import recruit
    from core.agents.registry import resolve_agent

    spec = await recruit("Writer_FR")
    assert spec.role == "Writer_FR"
    assert isinstance(spec.provider, str) and spec.provider
    assert isinstance(spec.model, str) and spec.model
    assert resolve_agent("Writer_FR") == spec
