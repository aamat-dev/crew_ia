import logging

import pytest


@pytest.mark.asyncio
async def test_request_id_header_and_log(client, caplog):
    with caplog.at_level(logging.INFO, logger="api.access"):
        resp = await client.get("/health")
    assert resp.status_code == 200
    rid = resp.headers.get("X-Request-ID")
    assert rid
    logged = [r.request_id for r in caplog.records]
    assert rid in logged
