import cython as c

def f(x: c.double):
    return x ** 2 - x

def integrate_f(a: c.double, b: c.double, N: c.int):
    i: c.int
    s: c.double
    dx: c.double

    s = 0

    dx = (b - a) / N

    for i in range(N):
        s += f(a + i * dx)
    return s * dx


print(integrate_f(2.4, 5.5, 10000000))
