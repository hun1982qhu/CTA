#%%
vt_orderis = "abcd.1234"
gateway, vt_orderid = vt_orderis.split(".")
print(gateway, vt_orderid)

stop_orders = {"a":1,"b":2, "c":3}
print(stop_orders.values())
print(type(stop_orders.values()))
print(list(stop_orders.values()))

#%%
d = {"a":1, "b":2}

while True:

    name = input('请输入您的用户名：')

    if name in d:

        break

    else:

        print('您输入的用户名不存在，请重新输入')

        continue

 

while True:

    password = input('请输入您的密码：')

    if d[name] == password:

        print('进入系统')

        break

    else:

        print('您输入的密码不正确，请重新输入')

        continue
# %%
