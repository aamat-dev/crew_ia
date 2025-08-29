import pytest
import datetime as dt


@pytest.mark.asyncio
async def test_runs_date_range_cap(client):
    start = dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=120)
    r = await client.get(
        "/runs",
        params={"started_from": start.isoformat(), "started_to": end.isoformat()},
    )
    assert r.status_code == 400
