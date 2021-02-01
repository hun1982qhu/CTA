from datetime import datetime, timedelta

a = datetime.now()
print(a)

date1 = "2020-8-28"
date2 = "20200828"
time = "12:23:43.254366"
c = " ".join([date1, time])
d = " ".join([date2, time])
print("c=", c)
print("d=", d)

e = datetime.strptime(c, "%Y-%m-%d %H:%M:%S.%f")
f = datetime.strptime(d, "%Y%m%d %H:%M:%S.%f")
print("e=", e)
print("f=", f)

millitime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
print(millitime)
