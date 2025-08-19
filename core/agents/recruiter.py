from .registry import AgentSpec

def recruit(role:str) -> AgentSpec:
    r = role.strip()
    if r.lower().startswith("writer"):
        return AgentSpec(role,"core/agents/prompts/executors/writer_fr.txt","ollama","llama3.1:8b",[])
    if r.lower().startswith("research"):
        return AgentSpec(role,"core/agents/prompts/executors/researcher.txt","ollama","llama3.1:8b",[])
    if r.lower().startswith("review"):
        return AgentSpec(role,"core/agents/prompts/executors/reviewer.txt","ollama","llama3.1:8b",[])
    # fallback manager
    return AgentSpec(role,"core/agents/prompts/manager.txt","ollama","llama3.1:8b",[])
