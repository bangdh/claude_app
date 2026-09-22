# VN30F1 data scraper (FireAnt)

Chương trình Python lấy dữ liệu giá theo ngày của hợp đồng tương lai VN30F1 (mã `VN30F1M` trên FireAnt) từ REST API của https://fireant.vn/.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Lấy token

API `restapi.fireant.vn` cần header `Authorization: Bearer <token>`:

1. Mở https://fireant.vn/ bằng trình duyệt (đăng nhập nếu cần).
2. F12 → tab **Network** → lọc `restapi.fireant.vn`.
3. Chọn một request, copy giá trị header `Authorization` (bỏ chữ `Bearer `).
4. `export FIREANT_TOKEN="<token>"`

## Sử dụng

```bash
# 30 ngày gần nhất, in CSV ra màn hình
python fireant_vn30f1.py

# Khoảng ngày tùy chọn, lưu ra file CSV
python fireant_vn30f1.py --start 2026-01-01 --end 2026-09-22 -o vn30f1.csv

# Xuất JSON đầy đủ các trường
python fireant_vn30f1.py --format json -o vn30f1.json

# Mã khác, ví dụ hợp đồng tháng kế tiếp
python fireant_vn30f1.py --symbol VN30F2M
```

Dùng như thư viện:

```python
from datetime import date
from fireant_vn30f1 import FireAntClient

client = FireAntClient(token="...")
rows = client.historical_quotes("VN30F1M", date(2026, 1, 1), date(2026, 9, 22))
```

Các cột CSV: `date, symbol, priceOpen, priceHigh, priceLow, priceClose, priceAverage, priceBasic, totalVolume, dealVolume, putthroughVolume, totalValue, buyForeignQuantity, sellForeignQuantity`.

## Kiểm thử

```bash
pip install pytest
python -m pytest -q tests
```
