import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import vn30f1_hourly as vh  # noqa: E402


def day_candles(d, base):
    """5 nến 1h của một phiên: 9h, 10h, 11h, 13h, 14h. open = base+giờ, close = open+0.5."""
    out = []
    for hour in (9, 10, 11, 13, 14):
        t = datetime(d.year, d.month, d.day, hour, tzinfo=vh.VN_TZ)
        o = base + hour
        out.append({"time": t, "open": o, "high": o + 1, "low": o - 1, "close": o + 0.5})
    return out


def test_diff_column_count_and_names():
    names = [c[0] for c in vh.diff_columns()]
    assert len(names) == (6 + 6 * 16) * 5
    assert "D0212" in names and "D2212" in names and "D6446" in names
    assert "D0122" not in names and "D0112" not in names  # n=0 cần x>y


def test_parse_udf_converts_to_vn_time():
    # 2026-09-21 02:00 UTC = 09:00 giờ VN
    ts = int(datetime(2026, 9, 21, 2, tzinfo=vh.timezone.utc).timestamp())
    [c] = vh.parse_udf({"t": [ts], "o": [1], "h": [2], "l": [0], "c": [1.5]})
    assert c["time"].hour == 9 and c["time"].date() == date(2026, 9, 21)
    assert vh.parse_udf({"s": "no_data"}) == []


def test_daily_prices_picks_correct_candles():
    [day] = vh.daily_prices(day_candles(date(2026, 9, 21), 1000))
    assert day["weekday"] == 2  # thứ Hai
    assert day["G"] == {1: 1009, 2: 1011.5, 3: 1013, 4: 1014.5}


def test_build_table_diffs():
    # Thứ Tư 16/9 → thứ Sáu 18/9 → thứ Hai 21/9 (bỏ qua cuối tuần)
    candles = (day_candles(date(2026, 9, 16), 1000)
               + day_candles(date(2026, 9, 18), 1100)
               + day_candles(date(2026, 9, 21), 1200))
    header, rows = vh.build_table(vh.daily_prices(candles))
    mon = dict(zip(header, rows[2]))
    assert mon["Date"] == "2026-09-21" and mon["Weekday"] == 2
    assert mon["D0212"] == 1211.5 - 1209              # G2 - G1 cùng ngày
    assert mon["D1212"] == 1211.5 - 1109              # G2 hôm nay - G1 phiên thứ Sáu
    assert mon["D2212"] == 1211.5 - 1009              # G2 hôm nay - G1 phiên thứ Tư
    assert mon["D3212"] == ""                          # không đủ 3 phiên trước
    assert mon["D0214"] == ""                          # cột thứ Tư, dòng thứ Hai → trống
    wed = dict(zip(header, rows[0]))
    assert wed["D0414"] == 1014.5 - 1009


def test_missing_candle_gives_blank():
    cs = [c for c in day_candles(date(2026, 9, 21), 1000) if c["time"].hour != 11]
    header, [row] = vh.build_table(vh.daily_prices(cs))
    r = dict(zip(header, row))
    assert r["G2"] == "" and r["D0212"] == "" and r["D0412"] != ""
