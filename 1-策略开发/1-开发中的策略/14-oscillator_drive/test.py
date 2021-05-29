import csv

fields = [
    "vt_symbol",
    "orderid",
    "tradeid",
    "offset",
    "direction",
    "price",
    "volume",
    "datetime"
    ]

f = open("trade_record.csv", "w")

writer = csv.DictWriter(f, fields)

writer.writeheader()

d = {
    "vt_symbol": 1,
    "orderid": 2,
    "tradeid": 3,
    "offset": 4,
    "direction": 5,
    "price": 6,
    "volume": 7,
    "datetime": 8
    }

writer.writerow(d)

f.flush()  # 强制同步