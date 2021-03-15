#%%
import numpy as np

a = [1, 2, 3, 4, 5]
a = np.array([1, 2, 4, 5, 6, 7])
c = np.array([1, 2])
c[:-1] = c[1:]
print(c)
c[-1] = 3
print(c)