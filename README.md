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

## Nến 1h VN30F1 → bảng G1..G4 và cột Dnxyw

`vn30f1_hourly.py` lấy nến 1h VN30F1 (giờ Việt Nam) từ TradingView (mặc định, mã `HNX:VN30F1!`, qua websocket, không cần đăng nhập, tối đa 5000 nến ≈ 4 năm), hoặc từ API công khai của DNSE / VNDirect.

| Cột | Ý nghĩa |
|---|---|
| `Date`, `Weekday` | Ngày giao dịch, thứ (2 = thứ Hai … 6 = thứ Sáu) |
| `G1` | Giá lúc 9:00 = open nến 9:00 |
| `G2` | Giá lúc 11:30 = close nến 11:00 |
| `G3` | Giá lúc 13:00 = open nến 13:00 |
| `G4` | Giá lúc 14:45 = close nến 14:00 |
| `Dnxyw` | `Gx` hôm nay − `Gy` của phiên trước đó `n` phiên; chỉ có giá trị ở dòng có thứ = `w` |

`n` ∈ 0..6 (tính theo phiên giao dịch, không theo ngày lịch), `x, y` ∈ 1..4, `w` ∈ 2..6; khi `n = 0` thì `x > y`. Tổng cộng 510 cột D.
Ví dụ `D0212` = G2 − G1 của thứ Hai; `D2212` = G2 thứ Hai − G1 của phiên trước đó 2 phiên. Thiếu nến thì ô để trống.

```bash
# TradingView: toàn bộ nến 1h lấy được, lưu thêm nến thô
python vn30f1_hourly.py --candles-out candles_1h.csv -o vn30f1_1h.csv
# TradingView, lọc từ 2025-01-01
python vn30f1_hourly.py --start 2025-01-01 -o vn30f1_1h.csv
# Nguồn DNSE / VNDirect (mặc định 365 ngày gần nhất)
python vn30f1_hourly.py --source vndirect --start 2025-01-01 -o vn30f1_1h.csv
# Dùng file nến 1h có sẵn, ví dụ file "Export chart data" từ TradingView
# (cột time,open,high,low,close; time là epoch giây hoặc giờ VN "YYYY-MM-DD HH:MM")
python vn30f1_hourly.py --input candles_1h.csv -o vn30f1_1h.csv
```
