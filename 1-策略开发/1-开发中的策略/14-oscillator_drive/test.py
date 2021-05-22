#%%
vt_orderis = "abcd.1234"
gateway, vt_orderid = vt_orderis.split(".")
print(gateway, vt_orderid)

stop_orders = {"a":1,"b":2, "c":3}
print(stop_orders.values())
print(type(stop_orders.values()))
print(list(stop_orders.values()))

#%%
a = set([1, 1, 2, 3])
print(a)
# %%
