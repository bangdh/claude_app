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

Nguồn dữ liệu (không cần token):
  tradingview : websocket TradingView, mã HNX:VN30F1! (mặc định, tối đa 5000 nến)
  dnse        : services.entrade.com.vn
  vndirect    : dchart-api.vndirect.com.vn
Hoặc đọc nến 1h có sẵn từ CSV (--input) với các cột time,open,high,low,close
(time là giờ Việt Nam "YYYY-MM-DD HH:MM" hoặc epoch giây).

Ví dụ:
  python vn30f1_hourly.py -o vn30f1_1h.csv                      # TradingView
  python vn30f1_hourly.py --source dnse --start 2025-01-01 -o vn30f1_1h.csv
  python vn30f1_hourly.py --input candles.csv -o vn30f1_1h.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import string
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


# ---------------------------------------------------------------- TradingView

TV_WS_URL = "wss://data.tradingview.com/socket.io/websocket?from=chart%2F"
TV_SYMBOL = "HNX:VN30F1!"
TV_MAX_BARS = 5000  # giới hạn số nến cho tài khoản khách


def tv_frame(func: str, params: list) -> str:
    body = json.dumps({"m": func, "p": params}, separators=(",", ":"))
    return f"~m~{len(body)}~m~{body}"


def tv_split(raw: str) -> list[str]:
    """Tách các gói "~m~<len>~m~<payload>" trong một frame websocket."""
    return [p for p in re.split(r"~m~\d+~m~", raw) if p]


def fetch_tradingview(symbol: str = TV_SYMBOL, bars: int = TV_MAX_BARS,
                      token: str = "unauthorized_user_token", ws=None,
                      timeout: float = 30.0) -> list[dict]:
    """Lấy `bars` nến 1h gần nhất từ TradingView qua websocket (không cần đăng nhập)."""
    if ws is None:
        import websocket  # pip install websocket-client
        try:
            ws = websocket.create_connection(
                TV_WS_URL, timeout=timeout,
                header={"Origin": "https://www.tradingview.com", "User-Agent": USER_AGENT})
        except Exception as exc:
            raise RuntimeError(f"Kết nối TradingView thất bại: {exc}") from exc
    cs = "cs_" + "".join(random.choices(string.ascii_lowercase, k=12))
    sym = json.dumps({"symbol": symbol, "adjustment": "splits", "session": "regular"})
    for func, params in [
        ("set_auth_token", [token]),
        ("chart_create_session", [cs, ""]),
        ("resolve_symbol", [cs, "sds_sym_1", "=" + sym]),
        ("create_series", [cs, "sds_1", "s1", "sds_sym_1", "60", bars, ""]),
    ]:
        ws.send(tv_frame(func, params))

    bars_by_time: dict[int, list] = {}
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            raw = ws.recv()
            for pkt in tv_split(raw):
                if pkt.startswith("~h~"):  # heartbeat: gửi lại để giữ kết nối
                    ws.send(f"~m~{len(pkt)}~m~{pkt}")
                    continue
                try:
                    msg = json.loads(pkt)
                except ValueError:
                    continue
                m, p = msg.get("m"), msg.get("p", [])
                if m in ("timescale_update", "du") and len(p) > 1 and isinstance(p[1], dict):
                    for bar in p[1].get("sds_1", {}).get("s", []):
                        bars_by_time[int(bar["v"][0])] = bar["v"]
                elif m in ("symbol_error", "series_error", "critical_error", "protocol_error"):
                    raise RuntimeError(f"TradingView lỗi {m}: {p}")
                elif m == "series_completed":
                    deadline = 0
    except RuntimeError:
        raise
    except Exception as exc:  # lỗi mạng / timeout của websocket-client
        raise RuntimeError(f"Kết nối TradingView thất bại: {exc}") from exc
    finally:
        ws.close()
    if not bars_by_time:
        raise RuntimeError("TradingView không trả về nến nào")
    return [
        {"time": datetime.fromtimestamp(t, VN_TZ), "open": v[1], "high": v[2],
         "low": v[3], "close": v[4]}
        for t, v in sorted(bars_by_time.items())
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
    p.add_argument("--symbol", help="Mã (mặc định HNX:VN30F1! với tradingview, VN30F1M với dnse/vndirect)")
    p.add_argument("--start", type=parse_date,
                   help="Ngày bắt đầu (mặc định: mọi nến TradingView trả về; 365 ngày với dnse/vndirect)")
    p.add_argument("--end", type=parse_date, default=today)
    p.add_argument("--source", choices=["tradingview", *sorted(SOURCES)], default="tradingview")
    p.add_argument("--bars", type=int, default=TV_MAX_BARS, help="Số nến 1h lấy từ TradingView")
    p.add_argument("--tv-token", default="unauthorized_user_token",
                   help="auth token TradingView (tài khoản trả phí lấy được nhiều nến hơn)")
    p.add_argument("--input", help="Đọc nến 1h từ CSV thay vì gọi API")
    p.add_argument("--candles-out", help="Lưu nến 1h thô ra CSV (giờ VN)")
    p.add_argument("-o", "--output", help="File CSV kết quả (mặc định in ra màn hình)")
    args = p.parse_args(argv)

    try:
        if args.input:
            candles = read_candles_csv(args.input)
        elif args.source == "tradingview":
            candles = fetch_tradingview(args.symbol or TV_SYMBOL, args.bars, args.tv_token)
        else:
            args.start = args.start or today - timedelta(days=365)
            candles = fetch_candles(args.symbol or "VN30F1M", args.start, args.end, args.source)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    candles = [c for c in candles
               if (args.start is None or args.start <= c["time"].date()) and c["time"].date() <= args.end]

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
