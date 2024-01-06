class AA:
    a = 0


class B:
    def __init__(self):
        self.a = AA

    def Aa(self):
        print(self.a().a)


print(B().a)
print(B().Aa())
