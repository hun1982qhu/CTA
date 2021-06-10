from collections import defaultdict

strategy_orderid_map = defaultdict(set)

strategy_orderid_map["a"] = set(["b"])

vt_orderids = strategy_orderid_map["a"]
vt_orderids.add("c")

print(vt_orderids)
print(strategy_orderid_map["a"])

vt_orderids.remove("c")

print(vt_orderids)
print(strategy_orderid_map["a"])
