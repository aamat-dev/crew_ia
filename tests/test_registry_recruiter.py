from core.agents.recruiter import recruit
from core.agents.registry import resolve_agent
import core.config as cfg

def test_recruiter_unknown():
    spec = recruit("UnknownRole")
    assert spec.system_prompt
    assert spec.role == "UnknownRole"


def test_registry_resolve(monkeypatch):
    monkeypatch.setattr(cfg, "SUPERVISOR_PROVIDER", None)
    monkeypatch.setattr(cfg, "SUPERVISOR_MODEL", None)
    monkeypatch.setattr(cfg, "LLM_DEFAULT_PROVIDER", "prov")
    monkeypatch.setattr(cfg, "LLM_DEFAULT_MODEL", "mod")
    spec = resolve_agent("Supervisor")
    assert spec.provider == "prov"
    assert spec.model == "mod"
    assert "" != spec.system_prompt.strip()


def test_dynamic_registration():
    spec = recruit("Writer_FR_Bis")
    resolved = resolve_agent("Writer_FR_Bis")
    assert resolved == spec
