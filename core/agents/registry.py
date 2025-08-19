import os
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class AgentSpec:
    role: str
    system_prompt_path: str
    provider: str
    model: str
    tools: list[str]

def _env(name:str, default:str=""):
    return os.getenv(name, default)

def load_default_registry() -> Dict[str,AgentSpec]:
    return {
        "Supervisor": AgentSpec("Supervisor","core/agents/prompts/supervisor.txt",
            _env("SUPERVISOR_PROVIDER",_env("LLM_DEFAULT_PROVIDER","ollama")),
            _env("SUPERVISOR_MODEL",_env("LLM_DEFAULT_MODEL","llama3.1:8b")),
            []),
        "Manager_Generic": AgentSpec("Manager_Generic","core/agents/prompts/manager.txt",
            _env("MANAGER_PROVIDER",_env("LLM_DEFAULT_PROVIDER","ollama")),
            _env("MANAGER_MODEL",_env("LLM_DEFAULT_MODEL","llama3.1:8b")),
            []),
        "Writer_FR": AgentSpec("Writer_FR","core/agents/prompts/executors/writer_fr.txt",
            _env("EXECUTOR_PROVIDER",_env("LLM_DEFAULT_PROVIDER","ollama")),
            _env("EXECUTOR_MODEL",_env("LLM_DEFAULT_MODEL","llama3.1:8b")),
            []),
        "Researcher": AgentSpec("Researcher","core/agents/prompts/executors/researcher.txt",
            _env("EXECUTOR_PROVIDER",_env("LLM_DEFAULT_PROVIDER","ollama")),
            _env("EXECUTOR_MODEL",_env("LLM_DEFAULT_MODEL","llama3.1:8b")),
            []),
        "Reviewer": AgentSpec("Reviewer","core/agents/prompts/executors/reviewer.txt",
            _env("EXECUTOR_PROVIDER",_env("LLM_DEFAULT_PROVIDER","ollama")),
            _env("EXECUTOR_MODEL",_env("LLM_DEFAULT_MODEL","llama3.1:8b")),
            []),
    }
