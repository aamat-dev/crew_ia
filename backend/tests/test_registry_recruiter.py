def test_recruiter_unknown():
    from core.agents.recruiter import recruit
    from core.agents.registry import load_default_registry

    spec = recruit("UnknownRole")
    assert spec.system_prompt.strip() != ""
    assert spec.role == "UnknownRole"
    assert load_default_registry()["UnknownRole"] == spec


def test_recruiter_generic_fallback(monkeypatch):
    import core.config as cfg
    import importlib

    monkeypatch.setattr(cfg, "LLM_DEFAULT_PROVIDER", "provX")
    monkeypatch.setattr(cfg, "LLM_DEFAULT_MODEL", "modX")

    registry = importlib.reload(__import__("core.agents.registry", fromlist=["resolve_agent"]))
    recruiter = importlib.reload(__import__("core.agents.recruiter", fromlist=["recruit"]))

    spec = recruiter.recruit("Analyst_EN")
    assert spec.role == "Analyst_EN"
    assert spec.system_prompt.strip() != ""
    assert spec.provider == "provX"
    assert spec.model == "modX"

    resolved = registry.resolve_agent("Analyst_EN")
    assert resolved == spec
