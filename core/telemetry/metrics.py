from __future__ import annotations

import os
from typing import Optional

from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge
from prometheus_client.exposition import generate_latest as _generate_latest

# Registry globale pour toutes les métriques
registry = CollectorRegistry()

# Stockage lazy des métriques
_http_requests_total: Optional[Counter] = None
_http_request_duration_seconds: Optional[Histogram] = None
_db_pool_in_use: Optional[Gauge] = None
_orchestrator_node_duration_seconds: Optional[Histogram] = None
_runs_total: Optional[Counter] = None
_run_duration_seconds: Optional[Histogram] = None
_llm_tokens_total: Optional[Counter] = None
_llm_cost_total: Optional[Counter] = None
_http_requests_total_family: Optional[Counter] = None


def metrics_enabled() -> bool:
    """Indique si l'exposition des métriques est activée."""
    return (os.getenv("METRICS_ENABLED", "0") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_http_requests_total() -> Counter:
    global _http_requests_total
    if _http_requests_total is None:
        _http_requests_total = Counter(
            "http_requests_total",
            "Total des requêtes HTTP",
            ["route", "method", "status"],
            registry=registry,
        )
    return _http_requests_total


def get_http_requests_total_family() -> Counter:
    global _http_requests_total_family
    if _http_requests_total_family is None:
        _http_requests_total_family = Counter(
            "http_requests_total_family",
            "Total des requêtes HTTP par famille",
            ["route", "method", "status_family"],
            registry=registry,
        )
    return _http_requests_total_family


def get_http_request_duration_seconds() -> Histogram:
    global _http_request_duration_seconds
    if _http_request_duration_seconds is None:
        _http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "Durée des requêtes HTTP",
            ["route", "method"],
            registry=registry,
        )
    return _http_request_duration_seconds


def get_db_pool_in_use() -> Gauge:
    global _db_pool_in_use
    if _db_pool_in_use is None:
        _db_pool_in_use = Gauge(
            "db_pool_in_use",
            "Connexions DB utilisées",
            ["db"],
            registry=registry,
        )
    return _db_pool_in_use


def get_orchestrator_node_duration_seconds() -> Histogram:
    global _orchestrator_node_duration_seconds
    if _orchestrator_node_duration_seconds is None:
        _orchestrator_node_duration_seconds = Histogram(
            "orchestrator_node_duration_seconds",
            "Durée des nœuds orchestrateur",
            ["role", "provider", "model"],
            registry=registry,
        )
    return _orchestrator_node_duration_seconds


def get_runs_total() -> Counter:
    global _runs_total
    if _runs_total is None:
        _runs_total = Counter(
            "runs_total",
            "Total des runs",
            ["status"],
            registry=registry,
        )
    return _runs_total


def get_run_duration_seconds() -> Histogram:
    global _run_duration_seconds
    if _run_duration_seconds is None:
        _run_duration_seconds = Histogram(
            "run_duration_seconds",
            "Durée des runs",
            ["status"],
            registry=registry,
        )
    return _run_duration_seconds


def get_llm_tokens_total() -> Counter:
    global _llm_tokens_total
    if _llm_tokens_total is None:
        _llm_tokens_total = Counter(
            "llm_tokens_total",
            "Total de tokens LLM",
            ["kind", "provider", "model"],
            registry=registry,
        )
    return _llm_tokens_total


def get_llm_cost_total() -> Counter:
    global _llm_cost_total
    if _llm_cost_total is None:
        _llm_cost_total = Counter(
            "llm_cost_total",
            "Coût total LLM",
            ["provider", "model"],
            registry=registry,
        )
    return _llm_cost_total


def generate_latest() -> bytes:
    """Génère le payload texte des métriques."""
    return _generate_latest(registry)
