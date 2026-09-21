"""
============================================
__new__ 方法：控制对象的创建过程
============================================

一、核心概念
    __new__ 是 Python 中真正"创建对象"的特殊方法，
    而 __init__ 只是"初始化对象"的方法（给创建好的对象设置属性）。
    一句话总结：__new__ 负责"造出来"，__init__ 负责"装进去"。

二、__new__ 与 __init__ 的区别与执行顺序
    1. __new__ 先执行，__init__ 后执行。
       调用 类名(参数) 时，Python 的执行流程是：
       a. 先调用 __new__(cls, 参数)，它负责创建并返回一个实例；
       b. 只有当 __new__ 返回的对象是"当前类的实例"时，
          Python 才会自动调用 __init__(obj, 参数) 对这个实例进行初始化。
    2. __new__ 的第一个参数是类本身（cls，约定俗成），它是"静态方法"：
       不需要 self，也不需要通过 @staticmethod 声明。
    3. __new__ 必须返回一个实例；如果不返回（返回 None），
       则对象创建失败，__init__ 也不会被调用。

三、什么时候需要自定义 __new__
    1. 不可变类型的子类：如 int、str、tuple、frozenset 的实例在创建后不能修改，
       所以必须在 __new__ 阶段完成所有定制。
       示例 1：SquareNumber(int) 继承 int，在 __new__ 中把传入值求平方后再创建。
    2. 实现单例模式：保证整个程序只有一个实例。
    3. 需要完全控制实例创建过程（如对象池、缓存复用对象等）。
    4. 在创建实例时就提前设置属性（虽然通常建议放在 __init__，
       但某些场景需要在 __new__ 里提前准备）。
       示例 2：在 __new__ 中提前创建 first_name、last_name 两个属性。

四、注意事项与易错点
    1. __new__ 是静态方法：第一个参数是 cls，不要写成 self。
    2. __new__ 一定要 return：如果不返回实例，Python 不会调用 __init__，
       甚至可能返回 None 导致后续代码出错。
    3. 调用父类 __new__ 用 super().__new__(cls, ...)，
       对不可变类型还要传入对应的构造参数。
    4. 只有 __new__ 返回的是 cls 的实例时，__init__ 才会被自动调用。
       若 __new__ 返回了其他类型的对象，__init__ 不会执行。
"""


class SquareNumber(int):
    """继承不可变类型 int，通过 __new__ 定制创建过程：返回传入整数的平方"""

    def __new__(cls, value: int):
        # 自定义对象的创建过程：传入一个整数，创建出的对象是这个整数的平方
        # int 是不可变类型，必须在创建阶段（__new__）就确定最终的值
        return super().__new__(cls, value ** 2)


a = SquareNumber(10)  # 创建时：10 ** 2 = 100
print(a)              # 100


class Student:
    """演示在 __new__ 中提前创建属性"""

    def __new__(cls, first_name, last_name):
        # 自定义对象的创建过程
        obj = super().__new__(cls)  # 必须调用父类 __new__ 并返回一个实例
        # 在创建对象时就已经创建了两个属性：first_name 和 last_name
        obj.first_name = first_name
        obj.last_name = last_name
        return obj  # 返回创建好的实例（__new__ 必须返回实例）


stu = Student('Mary', 'Ma')  # 实例创建时属性已被设置好
print(stu.first_name)  # Mary
print(stu.last_name)   # Ma


# ==================== 补充示例 1：__new__ 与 __init__ 的执行顺序 ====================

class Order:
    def __new__(cls, *args, **kwargs):
        print('1. __new__ 先执行')
        instance = super().__new__(cls)  # 调用父类的 __new__ 真正创建对象
        return instance

    def __init__(self, *args, **kwargs):
        print('2. __init__ 后执行（进行初始化）')
        # 因为 __new__ 返回了本类的实例，所以 __init__ 会被自动调用


o = Order()


# ==================== 补充示例 2：用 __new__ 实现单例模式 ====================

class Singleton:
    """单例模式：整个程序只有一个实例"""

    _instance = None  # 类属性，用于保存唯一实例

    def __new__(cls):
        if cls._instance is None:
            # 第一次创建：调用父类 __new__ 创建实例并保存
            cls._instance = super().__new__(cls)
        # 之后每次都直接返回之前保存的同一个实例
        return cls._instance


s1 = Singleton()
s2 = Singleton()
print(s1 is s2)  # True：s1 和 s2 是同一个对象
