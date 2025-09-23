import pytest


@pytest.mark.asyncio
async def test_templates_crud(client):
    # Create
    payload = {"name": "tmpl-1", "role": "executor", "domain": "doc", "prompt_system": "Sys"}
    r = await client.post("/agents/templates", json=payload, headers={"X-Request-ID": "t1"})
    assert r.status_code == 201
    tpl = r.json()

    # List
    r2 = await client.get("/agents/templates", params={"role": "executor"})
    if r2.status_code != 200:
        print("templates list error:", r2.json())
    assert r2.status_code == 200
    assert any(it["id"] == tpl["id"] for it in r2.json().get("items", []))

    # Patch
    r3 = await client.patch(
        f"/agents/templates/{tpl['id']}", json={"prompt_system": "Sys2"}, headers={"X-Request-ID": "t2"}
    )
    assert r3.status_code == 200
    assert r3.json()["prompt_system"] == "Sys2"

    # Deactivate/Reactivate
    r4 = await client.post(f"/agents/templates/{tpl['id']}/deactivate", headers={"X-Request-ID": "t3"})
    assert r4.status_code == 204
    r5 = await client.post(f"/agents/templates/{tpl['id']}/reactivate", headers={"X-Request-ID": "t4"})
    assert r5.status_code == 204


@pytest.mark.asyncio
async def test_models_matrix_crud(client):
    # Create
    payload = {"role": "reviewer", "domain": "qa", "models": {"preferred": [{"provider": "openai", "model": "gpt-4o-mini"}]}}
    r = await client.post("/agents/models-matrix", json=payload, headers={"X-Request-ID": "m1"})
    assert r.status_code == 201
    item = r.json()

    # List (filter)
    r2 = await client.get("/agents/models-matrix", params={"role": "reviewer", "domain": "qa"})
    if r2.status_code != 200:
        print("matrix list error:", r2.json())
    assert r2.status_code == 200
    assert any(it["id"] == item["id"] for it in r2.json().get("items", []))

    # Patch
    r3 = await client.patch(
        f"/agents/models-matrix/{item['id']}", json={"models": {"preferred": [{"provider": "mistral", "model": "mistral-small"}]}}, headers={"X-Request-ID": "m2"}
    )
    assert r3.status_code == 200
    assert r3.json()["models"]["preferred"][0]["provider"] in ("mistral",)

    # Deactivate/Reactivate
    r4 = await client.post(f"/agents/models-matrix/{item['id']}/deactivate", headers={"X-Request-ID": "m3"})
    assert r4.status_code == 204
    r5 = await client.post(f"/agents/models-matrix/{item['id']}/reactivate", headers={"X-Request-ID": "m4"})
    assert r5.status_code == 204
