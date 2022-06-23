class A:
    a = 1
    b = 2

    def set(self, x, y):
        setattr(A, x, y)

class B:
    c = 3 

a = A()
print(A.a)
a.set("a", 3)
print(A.a)