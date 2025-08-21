from core.agents.recruiter import recruit

def test_recruiter_unknown():
    spec = recruit("UnknownRole")
    assert spec.system_prompt_path
    assert spec.role == "UnknownRole"
