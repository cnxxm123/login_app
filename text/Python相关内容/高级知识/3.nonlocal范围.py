"""
【nonlocal 关键字 —— Python 作用域与闭包】

一、LEGB 变量查找规则
    当代码里访问一个变量时，Python 按以下顺序逐层查找，找到即用：
        L - Local        局部作用域（当前函数内的变量）
        E - Enclosing    外层函数作用域（闭包中嵌套函数的外层函数）
        G - Global       全局作用域（当前模块顶层定义的变量）
        B - Built-in     内置作用域（Python 内置的名字，如 len、print）
    注意：普通访问（只读）会自动一层层往外找，不需要任何声明。

二、nonlocal 是干什么的
    在"内层函数"中，如果只是【读取】外层函数的变量，直接读即可（LEGB 的 E）。
    但如果你想在【内层函数里修改】外层函数（且不是全局）的变量，就必须用
    nonlocal 声明：告诉 Python "这个变量不是本函数的局部变量，而是外层函数中的，
    请直接修改外层的那一份"。

三、nonlocal 与 global 的区别
    - nonlocal: 指向【外层函数】里的变量（Enclosing 层），且不能指向模块全局。
    - global  : 指向【模块顶层】的全局变量（Global 层）。
    简单记忆：
        global   = 我要改全局（模块级）变量
        nonlocal = 我要改外层函数的局部变量
    两者都必须在【赋值语句之前】声明，且声明的名字在函数里不能再次做普通局部赋值。

四、易错点
    1. 不加 nonlocal 就在内层函数里给外层变量赋值，Python 会认为你在
       创建"局部变量"，导致：要么只影响局部，要么报 UnboundLocalError。
    2. nonlocal 只能找"外层函数"的变量，找不到会报 SyntaxError: no binding ...
    3. nonlocal 不能用于模块级（最外层），因为模块级已经是全局了。
"""

message = "module"          # 全局（Global 层）变量 message


def outer():
    # 外层函数 outer 的局部（Enclosing 层）变量 message
    message = "outer"

    def inner():
        nonlocal message    # 声明 message 是 nonlocal 范围的变量（外层函数的）
        message = "inner"   # 直接修改外层函数 outer 里的 message
        print(message)      # 打印修改后的 message -> inner

    inner()
    print(message)          # 打印 outer 函数内的局部变量 message -> 已被改为 inner


outer()                     # 调用 outer
print(message)              # 打印全局变量 message -> 仍是 "module"（global 不受影响）


# =====================================================================
# 补充示例一：不加 nonlocal 会发生什么 —— 对比"创建局部变量"
# =====================================================================
def outer2():
    x = 10                  # 外层函数的局部变量 x

    def inner2():
        # 这里没有 nonlocal 声明，x = 20 会创建一个"inner2 自己的局部变量 x"
        x = 20
        print('inner2 里的 x:', x)   # 输出: 20（这是 inner2 自己的 x）

    inner2()
    print('outer2 里的 x:', x)       # 输出: 10（外层 x 完全没被动过）


print('\n===== 补充示例一：不加 nonlocal =====')
outer2()


# =====================================================================
# 补充示例二：nonlocal 实现计数器（闭包的典型应用）
# 内层函数通过 nonlocal 持续修改外层变量，实现"有状态的函数"
# =====================================================================
def make_counter():
    count = 0                # 外层函数持有的"状态"

    def add(step=1):
        nonlocal count       # 声明要修改外层函数的 count
        count += step        # 修改外层 count（如果不加 nonlocal 会报 UnboundLocalError）
        return count

    return add               # 返回内层函数（形成闭包，count 被保存在 __closure__）


print('\n===== 补充示例二：nonlocal 实现计数器 =====')
counter = make_counter()
print(counter())     # 输出: 1
print(counter())     # 输出: 2
print(counter(5))    # 输出: 7（每次调用都会累加，因为 nonlocal 改的是同一份 count）
