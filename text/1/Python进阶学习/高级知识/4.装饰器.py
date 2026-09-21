"""
【装饰器 Decorator —— Python 高级特性】

一、核心概念
    装饰器本质上是一个"接收函数、返回新函数"的可调用对象（通常是函数）。
    它可以在不改动原函数代码的前提下，给函数"附加"额外的功能，比如：
    打印日志、计时、权限校验、缓存等。
    一句话：装饰器 = 高阶函数（参数是函数，返回值也是函数）。

二、语法糖 @ 的等价写法
    @welcome('tom')
    def sad(): ...
    等价于：
        sad = welcome('tom')(sad)
    也就是说，@ 只是"把下面的函数当作参数传给装饰器，再用返回值替换掉函数名"
    的语法糖而已。

三、带参数的装饰器（三层结构）
    如果装饰器本身需要参数（如 welcome('tom')），就必须包三层：
        第 1 层：welcome(name)        接收装饰器的参数，返回真正的装饰器
        第 2 层：decorator(fn)        接收被装饰的函数，返回包装函数
        第 3 层：wrapper(*args, **kwargs)  真正被调用的包装函数
    调用流程：sad() -> wrapper() -> 原 sad()，从而可以在前后插入额外逻辑。

四、@wraps 的作用
    wrapper 是新的函数对象，默认会丢失原函数的名字(__name__)和文档(__doc__)。
    @wraps(fn) 会把原函数 fn 的 __name__、__doc__、__module__ 等属性"复制"到
    wrapper 上，保证装饰后的函数"看起来"还是原来的函数，便于调试。

五、叠放多个装饰器
    从下往上装饰，从上往下执行。例如：
        @d1
        @d2
        def f(): ...
    等价于 f = d1(d2(f))，执行时先进入 d1 的 wrapper，再进入 d2 的 wrapper，
    最后才执行原函数 f 本体（执行顺序与书写顺序相反）。

六、注意事项与易错点
    1. 装饰器在被 import 时就会执行（定义阶段），而不是调用时执行。
    2. 别忘了 return wrapper（以及返回调用结果 result），否则函数会丢失返回值。
    3. 写带参装饰器时容易少包一层，导致被装饰函数被错误地当成装饰器参数。
"""

from functools import wraps


# =====================================================================
# 示例一：不带参数的装饰器（最基础的两层结构）
# 先注释掉的这段是"普通装饰器"的标准写法，结构与带参装饰器对比着看
# =====================================================================
# def welcome(fn):                      # 第 1 层：接收被装饰的函数
#     @wraps(fn)                        # 保留原函数的 __name__ / __doc__
#     def wrapper(*args, **kwargs):     # 第 2 层：包装函数，参数不定
#         print('welcome')              # 调用前额外做的"增强"动作
#         result = fn(*args, **kwargs)  # 调用原函数，并拿到它的返回值
#         return result                 # 必须把结果返回出去，否则原函数返回值丢失
#     return wrapper                    # 返回包装函数（这就是"返回新函数"）

# =====================================================================
# 示例二：带参数的装饰器（三层结构）
# =====================================================================
def welcome(name):            # 第 1 层：接收装饰器自己的参数 name
    def decorator(fn):        # 第 2 层：接收被装饰的函数（name 已通过闭包捕获）
        @wraps(fn)            # 把原函数 fn 的元信息复制给 wrapper
        def wrapper(*args, **kwargs):   # 第 3 层：真正运行的包装函数
            print(f'wclcome {name}')    # 调用前打印：这里用到了外层的 name
            result = fn(*args, **kwargs)  # 调用原函数本体
            return result               # 透传原函数的返回值
        return wrapper        # 第 2 层返回第 3 层
    return decorator          # 第 1 层返回第 2 层


# @welcome('tom') 是语法糖，等价于：sad = welcome('tom')(sad)
# 即：先用 'tom' 调用 welcome 拿到 decorator，再把 sad 传给 decorator 得到 wrapper
@welcome('tom')
def sad():
    print('hello')


print('===== 调用被装饰后的 sad() =====')
sad()          # 实际执行的是 wrapper：先打印 welcome tom，再打印 hello

# 由于使用了 @wraps，打印出来的名字仍然是原函数名 sad，而不是 wrapper
print('函数名（有 @wraps 保持原名）:', sad.__name__)  # 输出: sad


# =====================================================================
# 补充示例一：不带参数装饰器的标准写法（计时器）
# 注意结构：只有两层，装饰器直接接收函数
# =====================================================================
def timer(fn):
    """一个简单的计时装饰器：测量函数执行耗时"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        import time
        start = time.perf_counter()   # 调用前记录开始时间
        result = fn(*args, **kwargs)  # 调用原函数
        end = time.perf_counter()     # 调用后记录结束时间
        print(f'{fn.__name__} 执行耗时: {end - start:.6f} 秒')
        return result                 # 返回原函数的结果
    return wrapper


@timer
def add(a, b):
    """把两个数相加"""
    return a + b


print('===== 使用 @timer 装饰 =====')
print('add(3, 5) =', add(3, 5))


# =====================================================================
# 补充示例二：叠放多个装饰器的执行顺序
# 装饰顺序：从下往上（先 apply_b，再 apply_a）
# 执行顺序：从上往下（先进入 a 的 wrapper，再进入 b 的 wrapper，最后执行原函数）
# =====================================================================
def apply_a(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print('[A 进入] 在调用前打印 A')
        result = fn(*args, **kwargs)
        print('[A 退出] 在调用后打印 A')
        return result
    return wrapper


def apply_b(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print('[B 进入] 在调用前打印 B')
        result = fn(*args, **kwargs)
        print('[B 退出] 在调用后打印 B')
        return result
    return wrapper


# 等价于：show = apply_a(apply_b(show))，所以先包 B 再包 A
@apply_a
@apply_b
def show():
    print('函数本体执行')


print('===== 叠放两个装饰器（观察执行顺序）=====')
show()
# 期望输出顺序：
#   [A 进入] ...
#   [B 进入] ...
#   函数本体执行
#   [B 退出] ...
#   [A 退出] ...
