from .registry import AgentSpec, ROLE_PROMPTS, _resolve_provider_model


def recruit(role: str) -> AgentSpec:
    r = role.strip()
    if not r:
        raise ValueError("role vide")

    if r.lower().startswith("writer"):
        prompt, prefix = ROLE_PROMPTS["Writer_FR"]
    elif r.lower().startswith("research"):
        prompt, prefix = ROLE_PROMPTS["Researcher"]
    elif r.lower().startswith("review"):
        prompt, prefix = ROLE_PROMPTS["Reviewer"]
    else:
        prompt, prefix = ROLE_PROMPTS["Manager_Generic"]

    provider, model = _resolve_provider_model(prefix)
    return AgentSpec(r, prompt, provider, model, [])
