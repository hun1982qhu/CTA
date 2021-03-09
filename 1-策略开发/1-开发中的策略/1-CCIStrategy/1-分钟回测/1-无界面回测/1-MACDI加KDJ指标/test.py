from datetime import date, datetime, timedelta
from time import time
start = time()
print(timedelta(seconds=36475))
print(datetime.now())
print(datetime.now() + timedelta(seconds=36475))
end = time()
duration = end - start
print(type(duration))
print(duration)
a: int=2
b: float=2.02
print(type(a*b))