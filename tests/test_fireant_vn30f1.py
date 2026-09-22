import io
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fireant_vn30f1 as fa  # noqa: E402


class FakeResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.ok = 200 <= status < 300
        self.text = str(data)

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, pages):
        self.pages = list(pages)
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        return self.pages.pop(0)


def quote(day):
    return {"date": f"2026-09-{day:02d}T00:00:00", "symbol": "VN30F1M",
            "priceOpen": 1300 + day, "priceClose": 1301 + day, "totalVolume": 1000 * day}


def test_normalize_symbol():
    assert fa.normalize_symbol("vn30f1") == "VN30F1M"
    assert fa.normalize_symbol("VN30F1M") == "VN30F1M"
    assert fa.normalize_symbol("VN30F1Q") == "VN30F1Q"


def test_pagination_and_sorting():
    session = FakeSession([
        FakeResponse([quote(d) for d in (5, 4)]),
        FakeResponse([quote(3)]),
    ])
    client = fa.FireAntClient("tok", session=session)
    rows = client.historical_quotes("VN30F1", date(2026, 9, 1), date(2026, 9, 5), page_size=2)
    assert [r["date"][:10] for r in rows] == ["2026-09-03", "2026-09-04", "2026-09-05"]
    assert session.calls[0][0].endswith("/symbols/VN30F1M/historical-quotes")
    assert [c[1]["offset"] for c in session.calls] == [0, 2]
    assert session.headers["Authorization"] == "Bearer tok"


def test_unauthorized_raises():
    client = fa.FireAntClient("bad", session=FakeSession([FakeResponse({}, status=401)]))
    with pytest.raises(fa.FireAntError, match="401"):
        client.historical_quotes("VN30F1M", date(2026, 9, 1), date(2026, 9, 5))


def test_missing_token():
    with pytest.raises(fa.FireAntError):
        fa.FireAntClient("")


def test_write_csv():
    buf = io.StringIO()
    fa.write_csv([quote(3)], buf)
    lines = buf.getvalue().splitlines()
    assert lines[0].startswith("date,symbol,priceOpen")
    assert lines[1].startswith("2026-09-03,VN30F1M,1303")
