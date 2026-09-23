#!/usr/bin/env python3
"""Lấy nến 1h VN30F1 và tính bảng giá G1..G4 + các cột chênh lệch Dnxyw.

Giờ Việt Nam (UTC+7):
  G1: giá lúc 9:00  = open  nến 9:00
  G2: giá lúc 11:30 = close nến 11:00
  G3: giá lúc 13:00 = open  nến 13:00
  G4: giá lúc 14:45 = close nến 14:00

Cột Dnxyw = Gx (ngày hiện tại) - Gy (ngày giao dịch trước đó n phiên),
chỉ có giá trị ở các dòng có thứ = w (2 = thứ Hai ... 6 = thứ Sáu).
  n ∈ 0..6, x,y ∈ 1..4, w ∈ 2..6; khi n = 0 thì x > y.
Ví dụ: D0212 = G2 - G1 của cùng ngày, chỉ tính cho thứ Hai.
       D2212 = G2 hôm nay (thứ Hai) - G1 của phiên trước đó 2 phiên.

Nguồn dữ liệu (API dạng TradingView, không cần token):
  dnse     : services.entrade.com.vn (mặc định)
  vndirect : dchart-api.vndirect.com.vn
Hoặc đọc nến 1h có sẵn từ CSV (--input) với các cột time,open,high,low,close
(time là giờ Việt Nam "YYYY-MM-DD HH:MM" hoặc epoch giây).

Ví dụ:
  python vn30f1_hourly.py --start 2025-01-01 -o vn30f1_1h.csv
  python vn30f1_hourly.py --input candles.csv -o vn30f1_1h.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

VN_TZ = timezone(timedelta(hours=7))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
SOURCES = {
    "dnse": ("https://services.entrade.com.vn/chart-api/v2/ohlcs/derivative",
             {"resolution": "1H"}),
    "vndirect": ("https://dchart-api.vndirect.com.vn/dchart/history",
                 {"resolution": "60"}),
}
CHUNK_DAYS = 90

MAX_N = 6
G_KEYS = (1, 2, 3, 4)
WEEKDAYS = (2, 3, 4, 5, 6)


def diff_columns() -> list[tuple[str, int, int, int, int]]:
    """Danh sách (tên cột, n, x, y, w) theo thứ tự xuất."""
    cols = []
    for w in WEEKDAYS:
        for n in range(MAX_N + 1):
            for x in G_KEYS:
                for y in G_KEYS:
                    if n == 0 and x <= y:
                        continue
                    cols.append((f"D{n}{x}{y}{w}", n, x, y, w))
    return cols


# ---------------------------------------------------------------- lấy dữ liệu

def fetch_candles(symbol: str, start: date, end: date, source: str = "dnse",
                  session: requests.Session | None = None) -> list[dict]:
    """Nến 1h trong [start, end] (giờ VN), mỗi nến {'time': datetime VN, open, high, low, close}."""
    url, extra = SOURCES[source]
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    candles: dict[int, dict] = {}
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), end)
        frm = int(datetime.combine(chunk_start, datetime.min.time(), VN_TZ).timestamp())
        to = int(datetime.combine(chunk_end, datetime.max.time(), VN_TZ).timestamp())
        data = _get(session, url, {"symbol": symbol, "from": frm, "to": to, **extra})
        for c in parse_udf(data):
            candles[int(c["time"].timestamp())] = c
        chunk_start = chunk_end + timedelta(days=1)
    return [candles[k] for k in sorted(candles)]


def _get(session, url, params, retries=3):
    last = None
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=30)
            if resp.ok:
                return resp.json()
            last = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.RequestException as exc:
            last = exc
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Gọi {url} thất bại: {last}")


def parse_udf(data: dict) -> list[dict]:
    """Chuyển phản hồi dạng TradingView {t,o,h,l,c} thành danh sách nến giờ VN."""
    if not data or data.get("s") == "no_data" or not data.get("t"):
        return []
    return [
        {"time": datetime.fromtimestamp(t, VN_TZ), "open": o, "high": h, "low": l, "close": c}
        for t, o, h, l, c in zip(data["t"], data["o"], data["h"], data["l"], data["c"])
    ]


def read_candles_csv(path: str) -> list[dict]:
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): v for k, v in row.items()}
            raw = row.get("time") or row.get("datetime") or row.get("date")
            if raw.strip().isdigit():
                t = datetime.fromtimestamp(int(raw), VN_TZ)
            else:
                t = datetime.fromisoformat(raw.strip()).replace(tzinfo=VN_TZ)
            out.append({"time": t, **{k: float(row[k]) for k in ("open", "high", "low", "close")}})
    return sorted(out, key=lambda c: c["time"])


# ---------------------------------------------------------------- tính toán

def daily_prices(candles: list[dict]) -> list[dict]:
    """Gom nến theo ngày và lấy G1..G4. Thiếu nến thì để None."""
    by_day: dict[date, list[dict]] = defaultdict(list)
    for c in candles:
        by_day[c["time"].date()].append(c)

    days = []
    for d in sorted(by_day):
        cs = sorted(by_day[d], key=lambda c: c["time"])
        morning = [c for c in cs if 9 <= c["time"].hour < 12]
        afternoon = [c for c in cs if 13 <= c["time"].hour < 15]
        g1 = next((c["open"] for c in morning if c["time"].hour == 9), None)
        g2 = next((c["close"] for c in morning if c["time"].hour == 11), None)
        g3 = next((c["open"] for c in afternoon if c["time"].hour == 13), None)
        g4 = next((c["close"] for c in afternoon if c["time"].hour == 14), None)
        days.append({"date": d, "weekday": d.isoweekday() + 1,
                     "G": {1: g1, 2: g2, 3: g3, 4: g4}})
    return days


def build_table(days: list[dict]) -> tuple[list[str], list[list]]:
    cols = diff_columns()
    header = ["Date", "Weekday", "G1", "G2", "G3", "G4"] + [c[0] for c in cols]
    rows = []
    for i, day in enumerate(days):
        g = day["G"]
        row = [day["date"].isoformat(), day["weekday"]] + [_fmt(g[k]) for k in G_KEYS]
        for _, n, x, y, w in cols:
            val = None
            if w == day["weekday"] and i - n >= 0:
                a, b = g[x], days[i - n]["G"][y]
                if a is not None and b is not None:
                    val = a - b
            row.append(_fmt(val))
        rows.append(row)
    return header, rows


def _fmt(v):
    return "" if v is None else round(v, 1)


# ---------------------------------------------------------------- CLI

def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main(argv=None) -> int:
    today = date.today()
    p = argparse.ArgumentParser(description="VN30F1 nến 1h → bảng G1..G4 và Dnxyw")
    p.add_argument("--symbol", default="VN30F1M")
    p.add_argument("--start", type=parse_date, default=today - timedelta(days=365))
    p.add_argument("--end", type=parse_date, default=today)
    p.add_argument("--source", choices=sorted(SOURCES), default="dnse")
    p.add_argument("--input", help="Đọc nến 1h từ CSV thay vì gọi API")
    p.add_argument("--candles-out", help="Lưu nến 1h thô ra CSV (giờ VN)")
    p.add_argument("-o", "--output", help="File CSV kết quả (mặc định in ra màn hình)")
    args = p.parse_args(argv)

    try:
        candles = (read_candles_csv(args.input) if args.input
                   else fetch_candles(args.symbol, args.start, args.end, args.source))
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    candles = [c for c in candles if args.start <= c["time"].date() <= args.end]

    if args.candles_out:
        with open(args.candles_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["time", "open", "high", "low", "close"])
            for c in candles:
                w.writerow([c["time"].strftime("%Y-%m-%d %H:%M"),
                            c["open"], c["high"], c["low"], c["close"]])

    header, rows = build_table(daily_prices(candles))
    out = open(args.output, "w", newline="", encoding="utf-8-sig") if args.output else sys.stdout
    try:
        w = csv.writer(out)
        w.writerow(header)
        w.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()
    if args.output:
        print(f"Đã ghi {len(rows)} ngày, {len(header)} cột vào {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
