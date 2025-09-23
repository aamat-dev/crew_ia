from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..schemas_base import AgentCreate, AgentUpdate


class SafetyPolicies(BaseModel):
    model_config = ConfigDict(extra='forbid')
    allow_tools: List[str] = Field(default_factory=list)
    forbidden_content: List[str] = Field(default_factory=list)
    pii_redaction: bool = True


class Capabilities(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tools: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class PromptGuidelines(BaseModel):
    model_config = ConfigDict(extra='forbid')
    style: Dict[str, Any] = Field(default_factory=lambda: {"tone": "professionnel", "no_purple_prose": True})
    io_format: Dict[str, Any] = Field(default_factory=lambda: {"input": "json", "output": "json"})
    acceptance: List[str] = Field(default_factory=list)
    tracing: Dict[str, Any] = Field(default_factory=lambda: {"summarize_key_decisions": True})


class ProviderStrategy(BaseModel):
    model_config = ConfigDict(extra='forbid')
    preferences: List[Dict[str, Any]] = Field(default_factory=list)
    fallbacks: List[Dict[str, Any]] = Field(default_factory=list)
    budget: Dict[str, Any] = Field(default_factory=lambda: {"max_total_cost_per_run": 5.0})


class CostLimits(BaseModel):
    model_config = ConfigDict(extra='forbid')
    max_tokens_per_call: int = 8192
    max_total_cost_per_run: float = 5.0


class RecruitRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role_description: str
    role: Optional[str] = None
    domain: Optional[str] = None
    language: Optional[str] = Field(default="fr")
    tone: Optional[str] = Field(default="professionnel")
    tools_required: List[str] = Field(default_factory=list)
    budget: Dict[str, Any] = Field(default_factory=lambda: {"max_total_cost_per_run": 5.0})
    latency_target_ms: Optional[int] = None
    safety_level: Optional[str] = Field(default="standard")


class RecruitResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    agent_id: str
    # Ajouts non-cassants pour faciliter l'usage côté client
    id: Optional[str] = None
    name: str
    role: str
    domain: Optional[str]
    default_model: Optional[str]
    sidecar: Dict[str, Any]
    template_used: Optional[str] = None
    template_id: Optional[str] = None
    created_at: Optional[datetime] = None
