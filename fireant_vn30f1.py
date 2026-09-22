#!/usr/bin/env python3
"""Lấy dữ liệu giá hợp đồng tương lai VN30F1 (VN30F1M) từ FireAnt.

FireAnt (https://fireant.vn/) cung cấp dữ liệu qua REST API tại
``https://restapi.fireant.vn``. Mọi request cần header
``Authorization: Bearer <token>``. Cách lấy token:

  1. Mở https://fireant.vn/ bằng trình duyệt (có thể cần đăng nhập).
  2. Mở DevTools (F12) → tab Network → lọc "restapi.fireant.vn".
  3. Chọn một request bất kỳ, copy giá trị header ``Authorization``
     (bỏ tiền tố ``Bearer ``).
  4. Đặt vào biến môi trường ``FIREANT_TOKEN`` hoặc truyền ``--token``.

Ví dụ:
  export FIREANT_TOKEN="eyJhbGciOi..."
  python fireant_vn30f1.py --start 2026-01-01 --end 2026-09-22 -o vn30f1.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from typing import Any, Iterable

import requests

BASE_URL = "https://restapi.fireant.vn"
DEFAULT_SYMBOL = "VN30F1M"
PAGE_SIZE = 100
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)

# Các cột chính xuất ra CSV (theo thứ tự). Các trường khác vẫn có trong JSON.
CSV_FIELDS = [
    "date",
    "symbol",
    "priceOpen",
    "priceHigh",
    "priceLow",
    "priceClose",
    "priceAverage",
    "priceBasic",
    "totalVolume",
    "dealVolume",
    "putthroughVolume",
    "totalValue",
    "buyForeignQuantity",
    "sellForeignQuantity",
]


class FireAntError(RuntimeError):
    """Lỗi khi gọi API FireAnt."""


def normalize_symbol(symbol: str) -> str:
    """FireAnt dùng mã VN30F1M cho hợp đồng tháng gần nhất; chấp nhận cả VN30F1."""
    symbol = symbol.strip().upper()
    if symbol in {"VN30F1", "VN30F2", "VN30F1Q", "VN30F2Q"}:
        return symbol if symbol.endswith("Q") else symbol + "M"
    return symbol


class FireAntClient:
    def __init__(
        self,
        token: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        if not token:
            raise FireAntError(
                "Thiếu token FireAnt. Đặt biến môi trường FIREANT_TOKEN hoặc dùng --token."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
                "Origin": "https://fireant.vn",
                "Referer": "https://fireant.vn/",
            }
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = exc
            else:
                if resp.status_code == 401:
                    raise FireAntError("Token không hợp lệ hoặc đã hết hạn (HTTP 401).")
                if resp.status_code == 429 or resp.status_code >= 500:
                    last_exc = FireAntError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                elif not resp.ok:
                    raise FireAntError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                else:
                    return resp.json()
            time.sleep(2**attempt)
        raise FireAntError(f"Gọi {url} thất bại sau {self.retries} lần: {last_exc}")

    def historical_quotes(
        self,
        symbol: str,
        start: date,
        end: date,
        page_size: int = PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        """Lấy dữ liệu giá theo ngày trong khoảng [start, end], sắp xếp tăng dần theo ngày."""
        symbol = normalize_symbol(symbol)
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self._get(
                f"/symbols/{symbol}/historical-quotes",
                {
                    "startDate": start.isoformat(),
                    "endDate": end.isoformat(),
                    "offset": offset,
                    "limit": page_size,
                },
            )
            if not isinstance(page, list):
                raise FireAntError(f"Phản hồi không mong đợi: {str(page)[:200]}")
            rows.extend(page)
            if len(page) < page_size:
                break
            offset += page_size

        # Loại trùng theo ngày và sắp xếp tăng dần.
        unique = {row.get("date"): row for row in rows}
        return sorted(unique.values(), key=lambda r: r.get("date") or "")


def write_csv(rows: Iterable[dict[str, Any]], out) -> None:
    writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        row = dict(row)
        if isinstance(row.get("date"), str):
            row["date"] = row["date"][:10]
        writer.writerow(row)


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Ngày không hợp lệ '{value}', cần YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    today = date.today()
    p = argparse.ArgumentParser(description="Lấy dữ liệu VN30F1 từ FireAnt (fireant.vn)")
    p.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Mã (mặc định: VN30F1M)")
    p.add_argument("--start", type=parse_date, default=today - timedelta(days=30),
                   help="Ngày bắt đầu YYYY-MM-DD (mặc định: 30 ngày trước)")
    p.add_argument("--end", type=parse_date, default=today,
                   help="Ngày kết thúc YYYY-MM-DD (mặc định: hôm nay)")
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    p.add_argument("-o", "--output", help="File đầu ra (mặc định: in ra màn hình)")
    p.add_argument("--token", default=os.environ.get("FIREANT_TOKEN", ""),
                   help="Bearer token FireAnt (mặc định lấy từ biến FIREANT_TOKEN)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.start > args.end:
        print("Lỗi: --start phải trước hoặc bằng --end", file=sys.stderr)
        return 2
    try:
        client = FireAntClient(args.token)
        rows = client.historical_quotes(args.symbol, args.start, args.end)
    except FireAntError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1

    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.format == "json":
            json.dump(rows, out, ensure_ascii=False, indent=2)
            out.write("\n")
        else:
            write_csv(rows, out)
    finally:
        if out is not sys.stdout:
            out.close()

    if args.output:
        print(f"Đã lưu {len(rows)} dòng {normalize_symbol(args.symbol)} vào {args.output}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
