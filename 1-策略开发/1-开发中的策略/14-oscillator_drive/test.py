#%%
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

file = open("trade_record.csv", "a", newline="")

file_writer = csv.DictWriter(file, fields)

file_writer.writeheader()

#%%
d = {
    "vt_symbol": 4,
    "orderid": 2,
    "tradeid": 3,
    "offset": 4,
    "direction": 5,
    "price": 6,
    "volume": 7,
    "datetime": 8
    }

file_writer.writerow(d)

file.flush()  # 强制同步
# %%
