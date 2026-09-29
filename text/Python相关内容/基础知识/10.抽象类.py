"""
============================================
抽象类（Abstract Class）与抽象方法
============================================

一、核心概念
    抽象类是一种"不能被实例化"的类，它用来定义一组子类必须实现的"规范/契约"。
    抽象方法则是只声明、不实现的方法（通常用 pass 占位），
    子类必须实现这些抽象方法，子类才能被实例化。

二、工作原理
    1. 导入：from abc import ABC, abstractmethod。
    2. 定义抽象类：class Action(ABC): —— 继承 ABC 基类即成为抽象类。
    3. 声明抽象方法：@abstractmethod 装饰的方法就是抽象方法，只有声明没有实现。
    4. 实例化约束：
       - 抽象类本身不能实例化，否则报错
         TypeError: Can't instantiate abstract class Action ...
       - 子类若没有实现父类的全部抽象方法，同样无法实例化。
    5. 子类实现全部抽象方法后，就可以像普通类一样正常实例化。

三、使用场景
    - 定义统一接口：多个类具有相同行为但实现不同，用抽象方法规定这个"接口"。
    - 框架/插件设计：规定子类必须提供哪些方法，保证调用方可以统一调用。

四、鸭子类型（Duck Typing）的体现
    "如果它走起来像鸭子、叫起来像鸭子，那它就是鸭子。"
    在 Python 中调用方法并不强制要求对象是某个类的实例，
    只要它"有这个同名方法"就能被调用。
    示例中 def say(action: Action) 里的类型标注 Action 只是"提示"，
    即便传入的不是 Action 的子类，只要它有 say() 方法，调用也能成功。

五、注意事项与易错点
    1. 抽象类不能实例化：直接 Action() 会报错。
    2. 子类必须实现所有抽象方法：只要漏掉一个，子类也无法实例化。
    3. 抽象类里也可以写普通方法和普通属性，供子类直接继承使用。
    4. 类型标注（如 : Action）在运行时不做强制检查，只是给人/IDE 看的提示，
       这正是鸭子类型"宽松"的一面，但也要注意由此带来的灵活性风险。
"""

from abc import ABC, abstractmethod


class Action(ABC):
    """抽象类：创建抽象类需要继承 ABC"""

    @abstractmethod  # 抽象方法装饰器：把 say 声明为抽象方法
    def say(self) -> int:  # 冒号后的 -> int 只是返回值类型标注（提示），并不强制
        # 抽象方法只做声明，不实现具体逻辑，用 pass 占位
        pass


class Student_Action(Action):
    """继承 Action 的子类，必须实现父类的抽象方法 say，否则无法实例化"""

    def say(self):
        # 这里实现了抽象方法的具体逻辑
        print('hello')


# 若子类没有实现抽象方法，实例化时会报错：
# class Bad(Action):
#     pass
# b = Bad()  # TypeError: Can't instantiate abstract class Bad with abstract method say


def say(action: Action):
    # 类型标注 : Action 表示"期望传入 Action 及其子类的实例"，
    # 但 Python 运行时并不会强制校验，这就是鸭子类型的体现：
    # 只要传入的对象有 say() 方法，这里就能正常调用。
    action.say()


# 抽象类本身不能实例化，尝试下面的代码会报错：
# act = Action()  # TypeError: Can't instantiate abstract class Action ...

stu = Student_Action()  # 子类实现了全部抽象方法，可以正常实例化
stu.say()               # 调用子类实现的 say()，打印 'hello'
say(stu)                # 把子类实例传给参数类型为 Action 的函数，也能正常工作


# ==================== 补充示例 1：子类未实现抽象方法会报错 ====================

class Shape(ABC):
    """抽象类：规定子类必须实现 area 求面积方法"""

    @abstractmethod
    def area(self):
        """求面积，子类必须实现"""
        pass


class NoArea(Shape):
    """这个子类没有实现 area 抽象方法，不能实例化"""
    pass


try:
    # 尝试实例化未实现抽象方法的子类，会抛出 TypeError
    s = NoArea()
    print(s)
except TypeError as e:
    print(f'实例化失败：{e}')


# ==================== 补充示例 2：正确实现抽象方法 + 鸭子类型 ====================

class Circle(Shape):
    """实现了 area 抽象方法，可以正常实例化"""

    def __init__(self, r):
        self.r = r

    def area(self):
        return 3.14 * self.r ** 2


class Duck:
    """一个与 Shape 完全无关的类，但它恰好也有 area 方法（鸭子类型）"""

    def area(self):
        return '鸭子不会算面积，但我会这个方法！'


c = Circle(2)
print(f'圆的面积：{c.area()}')  # 12.56

# 鸭子类型：Duck 不是 Shape 的子类，但只要它有 area 方法，就能被统一调用
d = Duck()
print(d.area())
