import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.agents.recruiter import recruit

def test_recruiter_unknown():
    spec = recruit("UnknownRole")
    assert spec.system_prompt_path
    assert spec.role == "UnknownRole"
