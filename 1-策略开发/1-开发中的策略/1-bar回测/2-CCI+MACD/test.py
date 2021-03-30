class A:
    def  __init__(self):
        self.list1 = []

    def test(self):
        for i in [1, 2, 3, 4, 5, 6]:
            if i == 3:
                self.list1.append(i)
                continue
            else:
                print(i)


a = A()
a.test()
print(a.list1)