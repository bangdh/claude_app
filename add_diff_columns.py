#!/usr/bin/env python3
"""Bỏ các cột I1..I5 và thêm các cột chênh lệch giá D21, D43, D53, D63, D54, D64.

Dùng: python add_diff_columns.py input.csv output.csv
"""

import csv
import sys

DIFFS = {
    "D21": ("G2", "G1"),
    "D43": ("G4", "G3"),
    "D53": ("G5", "G3"),
    "D63": ("G6", "G3"),
    "D54": ("G5", "G4"),
    "D64": ("G6", "G4"),
}


def diff(row, a, b):
    try:
        return f"{float(row[a]) - float(row[b]):.1f}"
    except (ValueError, TypeError):
        return ""  # thiếu dữ liệu ở một trong hai cột


def main(src, dst):
    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        keep = [c for c in reader.fieldnames if not c.startswith("I")]
        rows = list(reader)
    with open(dst, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(keep + list(DIFFS))
        for row in rows:
            writer.writerow([row[c] for c in keep] + [diff(row, a, b) for a, b in DIFFS.values()])
    print(f"Đã ghi {len(rows)} dòng vào {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
