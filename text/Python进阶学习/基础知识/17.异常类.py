"""
============================================
自定义异常类与异常处理
============================================

一、核心概念
    异常（Exception）是程序运行过程中出现的错误信号。
    Python 用 try/except 捕获并处理异常，避免程序直接崩溃。
    自定义异常类则是继承内置异常，创建属于自己业务的异常类型。

二、异常层级（异常体系）
    BaseException
     └── Exception            <-- 大多数异常都继承自它
          ├── ArithmeticError
          │    └── ZeroDivisionError
          ├── ValueError
          ├── TypeError
          └── 自定义异常（继承 Exception）
    1. BaseException 是异常体系的根，一般不要直接继承它。
    2. 自定义异常通常继承 Exception（而不是 BaseException），
       这样既能被 except Exception 捕获，也符合常规的异常处理习惯。

三、为什么需要自定义异常
    1. 语义清晰：Agnmet 比通用的 Exception 更能表达业务含义。
    2. 按类型捕获：调用方可以根据不同的异常类型分别处理。
    3. 携带额外信息：自定义异常可以在构造时保存更多错误细节。

四、try / except / else / finally 结构
    try:
        可能出错的代码
    except 某异常类型 as e:
        捕获并处理该异常（as e 用于获取异常对象）
    else:
        没有发生任何异常时才执行
    finally:
        无论是否发生异常都会执行（常用于关闭资源）

五、异常捕获顺序与易错点
    1. 捕获顺序：先写"具体异常"，再写"宽泛异常"。
       因为 except 是自上而下匹配的，如果先写 except Exception，
       后面的 except ZeroDivisionError 永远不会被执行。
    2. 异常会一级一级向上抛出：如果当前 try 没有捕获，会继续向外层抛出，
       直到最外层仍未被处理，程序才会终止并打印 Traceback。
    3. as e：用 as e 可以拿到异常对象，从而获取错误信息。
    4. raise：在函数内部使用 raise 主动抛出异常（可以带错误信息字符串）。
    5. super().__init__(*args)：自定义异常里要调用父类的 __init__，
       注意使用 *args 把参数逐个展开传给父类，而不是把整个元组作为一个参数。
"""


class Agnmet(Exception):  # 自定义异常类，继承自 Exception
    """自定义异常：当传入的参数不是整数时抛出"""

    def __init__(self, *args, **kwargs):
        # 修复：把 *args 展开后传给父类 Exception 的 __init__，
        # 这样异常对象就能保存完整的错误信息；
        # 原示例写成 super().__init__(args) 会把整个元组当成一个参数，是错误的。
        super().__init__(*args, **kwargs)


def add(x, y):
    """加法函数：如果参数不是整数，抛出自定义异常"""
    if not isinstance(x, int) or not isinstance(y, int):
        raise Agnmet('参数必须是整数！')  # 使用 raise 主动抛出自定义异常
    return x + y


a = 1
b = 0

try:
    # 1. 先尝试执行可能出错的代码
    # c = a / b          # 这行会触发 ZeroDivisionError（被下面的 except 捕获）
    z = add('e', 1)      # 参数不是整数，触发自定义异常 Agnmet
except ZeroDivisionError:
    # 2. 捕获 ZeroDivisionError（具体异常，写在前面）
    print('除数不能为 0！')
except Agnmet:
    # 3. 捕获自定义异常 Agnmet
    print('Agnmet')
except Exception as ex:
    # 4. 捕获其他所有常规异常（宽泛异常写在后面），as ex 拿到异常对象
    print(f'发生了其他异常：{ex}')
except BaseException:
    # 5. BaseException 是最宽泛的，几乎捕获一切，一般放最后
    print('最宽泛的异常')
else:
    # 6. 只有当 try 块没有发生任何异常时才会执行
    print('没有发生异常')
finally:
    # 7. 无论是否发生异常，finally 都会执行（适合关闭文件、释放资源等）
    print('finally 一定会执行')


# ==================== 补充示例：try/except/else/finally 与 as e 的完整演示 ====================

print('-' * 40)


def divide(x, y):
    """安全的除法：除数为 0 时抛出 ValueError"""
    if y == 0:
        raise ValueError('除数不能为 0')
    return x / y


try:
    result = divide(10, 0)
except ValueError as e:
    # as e：把异常对象赋值给变量 e，便于读取错误信息
    print(f'捕获到 ValueError，信息：{e}')
else:
    # try 中没有异常时才执行
    print(f'计算结果：{result}')
finally:
    # 无论如何都会执行
    print('无论对错，finally 都会执行')
