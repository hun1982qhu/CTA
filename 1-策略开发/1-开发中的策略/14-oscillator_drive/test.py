import copy

a = set([1, 2])
b = list(a).copy()

print(b)

c = [1, 2, [3, 4]]
d = copy.copy(c)
e = copy.deepcopy(c)

d[2][0] = 5
print(c)
print(d)
print(e)