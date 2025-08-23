from pathlib import Path
from .registry import AgentSpec, register_agent
from core.config import get_role_config, LLM_DEFAULT_PROVIDER, LLM_DEFAULT_MODEL



def recruit(role: str) -> AgentSpec:
    r = role.strip()
    root = Path(__file__).resolve().parents[2]
    exe_cfg = get_role_config("EXECUTOR")
    provider = (LLM_DEFAULT_PROVIDER or exe_cfg.provider).strip()
    model = (LLM_DEFAULT_MODEL or exe_cfg.model).strip()

    def readp(rel: str) -> str:
        return (root / rel).read_text(encoding="utf-8")

    if r.lower().startswith("writer"):
        prompt = readp("core/agents/prompts/executors/writer_fr.txt")
        spec = AgentSpec(r, prompt, exe_cfg.provider, exe_cfg.model, [])
    elif r.lower().startswith("research"):
        prompt = readp("core/agents/prompts/executors/researcher.txt")
        spec = AgentSpec(r, prompt, exe_cfg.provider, exe_cfg.model, [])
    elif r.lower().startswith("review"):
        prompt = readp("core/agents/prompts/executors/reviewer.txt")
        spec = AgentSpec(r, prompt, exe_cfg.provider, exe_cfg.model, [])
    elif r.lower().startswith("manager"):
        man_cfg = get_role_config("MANAGER")
        prompt = readp("core/agents/prompts/manager.txt")
        spec = AgentSpec(r, prompt, man_cfg.provider, man_cfg.model, [])
    else:
        # Rôle inconnu → agent générique FR avec fallback provider/model
        prompt = readp("core/agents/prompts/generic_fr.txt")
        spec = AgentSpec(r, prompt, provider, model, [])

    register_agent(spec)
    return spec
