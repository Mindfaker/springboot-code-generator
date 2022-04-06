async def func1():
    print("func1 start")
    print("func1 end")

async def func2():
    print("func2 start")
    print("func2 a")
    print("func2 b")
    print("func2 c")
    print("func2 end")

def func3():
    print()

f1 = func1()
f2 = func2()
print(f1,f2)
f3 = func3()
print(func3)