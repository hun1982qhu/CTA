def a():
    print('a() starts')
    spam = 42
    b()
    d()
    print('a() returns')

def b():
    print('b() starts')
    spam = 101
    c()
    print('b() returns')

def c():
    print('c() starts')
    print('c() returns')

def d():
    print('d() starts')
    print('d() returns')

a()
