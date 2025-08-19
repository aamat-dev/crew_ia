import json, tempfile, os
from core.agents import executor_llm

def test_sidecar_truncation(tmp_path):
    prompt = "x"*2000
    res = {"output":"ok","prompt":prompt}
    executor_llm._write_sidecar(tmp_path, "n1", res)
    data = json.loads((tmp_path/"artifact_n1.llm.json").read_text())
    assert len(data["prompt"]) <= 800
