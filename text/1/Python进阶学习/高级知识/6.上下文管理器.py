"""
【上下文管理器 Context Manager —— Python 高级特性】

一、核心概念
    上下文管理器用于"进入/退出"一段代码块时自动做资源管理，典型用法就是 with 语句。
    最常见的例子：with open(...) as f，无论代码块正常结束还是抛出异常，
    文件都会被自动关闭，我们不用手动写 f.close()。

二、with 语句的协议（魔法方法）
    with 表达式 as 变量: 代码块
    执行过程分三步：
    1. 进入代码块前，调用表达式对象的 __enter__() 方法；
       __enter__ 的返回值会被赋给 as 后面的变量。
    2. 执行 with 代码块内的语句。
    3. 无论代码块是正常结束还是抛出了异常，退出时【都会】调用 __exit__(...) 方法。

三、__exit__ 的三个参数
    def __exit__(self, exc_type, exc_val, exc_tb):
        - exc_type: 异常类型（如果没有异常则为 None）
        - exc_val : 异常实例/错误信息（没有异常则为 None）
        - exc_tb  : 异常堆栈回溯对象 traceback（没有异常则为 None）
    正常退出时三个参数都是 None；发生异常时它们携带异常信息。

四、__exit__ 的返回值控制是否"吞掉"异常
    - 返回 False（或不返回，默认 None 视为 False）：异常继续向上抛出。
    - 返回 True：表示异常已被处理/吞掉，调用方不会看到这个异常。
    这是实现"异常抑制"的关键，比如数据库连接断开的自动重连。

五、contextlib.contextmanager 装饰器（写上下文管理器的快捷方式）
    用 @contextmanager 装饰一个生成器函数：yield 之前的代码相当于 __enter__，
    yield 之后的代码相当于 __exit__（即使抛异常也会执行），比手写类简单得多。

六、使用场景与易错点
    使用场景：文件/网络连接/数据库/锁的自动释放、计时、事务、临时目录切换等。
    易错点：
    1. __enter__ 必须返回值，否则 as 拿到的是 None。
    2. __exit__ 记得返回 True/False 来决定是否吞掉异常。
    3. 多个 with 可以连写：with A() as a, B() as b: ...
"""

import time
import contextlib

# =====================================================================
# 示例一：with + open 文件自动关闭（最常用）
# 运行本文件会在当前目录写入/生成 1.txt，这是正常现象
# =====================================================================
with open('1.txt', 'w') as instance:   # __enter__ 返回文件对象，赋给 instance
    instance.write('fgiadygf')          # 写入内容
# 离开 with 代码块后，文件自动关闭（无需手动 close）


# =====================================================================
# 示例二：自定义上下文管理器（类 + __enter__ / __exit__）—— 计时器
# =====================================================================
class Timer:
    """上下文管理器：统计 with 代码块的执行耗时"""

    def __init__(self):
        self.elapsed = 0

    def __enter__(self):  # 进入 with 时最先被调用，必须要有返回值
        self.start = time.perf_counter()   # 记录开始时间
        print('start')
        return self        # 返回值会被赋给 as 后面的 timer 变量

    def __exit__(self, exc_type, exc_val, exc_tb):  # with 结束时必定被调用
        self.end = time.perf_counter()     # 记录结束时间
        self.elapsed = self.end - self.start  # 计算耗时
        print('end')
        # 不写 return（返回 None 等价于 False）：不吞掉异常，异常照常抛出


with Timer() as timer:  # as 后面为 __enter__ 的返回值
    ls = []
    for i in range(10000):
        ls.append(i ** 2)   # 计算 1 万个平方并存入列表

print('耗时:', timer.elapsed, '秒')


# =====================================================================
# 补充示例一：__exit__ 的三个参数 + 返回值 True 吞掉异常
# =====================================================================
class Suppressor:
    """专门用来"吞掉"指定异常的上下文管理器"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 三个参数的含义：
        # exc_type 是异常类型，exc_val 是异常对象，exc_tb 是堆栈回溯
        print(f'__exit__ 收到异常信息 -> 类型: {exc_type}, 信息: {exc_val}')
        if exc_type is ZeroDivisionError:   # 如果是除零错误
            return True                     # 返回 True：把异常吞掉，调用方无感知
        return False                        # 其它异常不处理，继续抛出


print('\n===== 补充示例一：返回 True 吞掉异常 =====')
with Suppressor():
    print('进入 with')
    1 / 0                       # 触发 ZeroDivisionError，但会被 __exit__ 吞掉
    print('这行不会执行')
print('异常被吞掉了，程序继续正常运行到这里')


# =====================================================================
# 补充示例二：contextlib.contextmanager 装饰器写法
# =====================================================================
@contextlib.contextmanager
def open_file(path, mode):
    """用 @contextmanager 实现的简化版文件上下文管理器"""
    print('yield 之前 -> 相当于 __enter__（打开文件）')
    f = open(path, mode)
    try:
        yield f          # 把资源交给 with 代码块使用（相当于 __enter__ 的返回值）
    finally:
        print('yield 之后 -> 相当于 __exit__（关闭文件）')
        f.close()        # 无论代码块是否抛异常，finally 都会执行


print('\n===== 补充示例二：@contextmanager 简化写法 =====')
with open_file('1.txt', 'a') as f:   # as 拿到的是 yield 出来的 f
    f.write('\n追加一行内容')
print('文件已自动关闭（无需手动 close）')
