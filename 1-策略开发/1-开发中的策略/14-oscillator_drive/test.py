buy_svt_orderids = [1]
short_svt_orderids = [2]
sell_svt_orderids = [3]
cover_svt_orderids = [4]

buf_dict = {
            "buy_svt_orderids": buy_svt_orderids,
            "short_svt_orderids": short_svt_orderids,
            "sell_svt_orderids": sell_svt_orderids,
            "cover_svt_orderids": cover_svt_orderids
            }

print(buf_dict.items())

def getDictKey(myDict, value):
    return [k for k, v in myDict.items() if v == value]

a = 1

for buf_orderids in list(buf_dict.values()):
    if a in buf_orderids:
        b = getDictKey(buf_dict, buf_orderids)
        buf_orderids.remove(a)
        print(f"{b[0]}")