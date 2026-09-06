"""
============================================
定制和扩展枚举：__str__ / __eq__ / __lt__ + @total_ordering
============================================

一、核心概念
    枚举成员本质上是类的实例，因此我们可以在枚举类中定义各种魔法方法
    （__str__、__eq__、__lt__ 等），来定制枚举成员的行为，
    比如打印格式、比较逻辑、排序规则等。

二、各方法的作用
    1. __str__(self)：定制 print(成员) 时的显示内容。
    2. __eq__(self, other)：定制 == 比较逻辑。
       这里实现了三种比较：与整数比较值、与字符串比较名字、与枚举成员比较身份。
    3. __lt__(self, other)：定制 < 比较逻辑，用于排序（sorted、max、min 等）。

三、@total_ordering 装饰器
    1. 作用：只要在类中实现了 __eq__ 和 __lt__（或 __gt__ 等一个基础比较方法），
       @total_ordering 会自动补齐剩下的比较方法：
       __le__（<=）、__ne__（!=）、__gt__（>）、__ge__（>=）。
    2. 也就是说，@total_ordering 不要求我们手写全部 6 个比较方法，
       它根据已有的比较方法推导出其他比较关系，让枚举成员可以参与各种排序/比较。

四、注意事项与易错点
    1. 易错点 1：在 __eq__ 中比较字符串时，要写 self.name == other，
       而不是 self.name == str。因为 str 是"类型对象"，而 other 才是传进来的值，
       原示例中的 return self.name == str 永远为 False，是一个经典错误。
    2. 易错点 2：比较对象时要注意传"实例"而不是"类"。
       原示例写 Status.MEAL < Status 是把类本身当作比较对象，没有意义；
       应写成 Status.MEAL < Status.FEMALE 才是比较两个具体成员。
    3. 枚举默认比较的是身份（is），一旦重写 __eq__，请确保逻辑完备，
       否则可能出现 == 与 is 行为不一致的情况。
"""

from enum import Enum
from functools import total_ordering


@total_ordering  # 装饰器：自动生成其他比较方法（__le__、__ne__、__gt__、__ge__）
class Status(Enum):
    MEAL = 1     # 主成员，值为 1（保留原示例命名）
    FEMALE = 2   # 主成员，值为 2

    def __str__(self):
        # 定制 print(Status.MEAL) 的显示内容，例如 MEAL(1)
        return f'{self.name}({self.value})'

    def __eq__(self, other):
        # 定制 == 比较逻辑，支持与三种类型比较
        if isinstance(other, int):
            # 与整数比较：比较的是枚举成员的值
            return self.value == other
        if isinstance(other, str):
            # 与字符串比较：比较的是枚举成员的名字
            # 修复：原示例误写为 return self.name == str（str 是类型不是内容），
            # 应改为 self.name == other
            return self.name == other
        if isinstance(other, Status):
            # 与枚举成员比较：同一个成员就是同一个对象（身份比较）
            return self is other
        return False  # 其他类型一律不相等

    def __lt__(self, other):
        # 定制 < 比较逻辑，@total_ordering 会基于它生成其他比较方法
        if isinstance(other, int):
            # 与整数比较：比较值
            return self.value < other
        if isinstance(other, Status):
            # 与枚举成员比较：比较各自的值
            return self.value < other.value
        return False


print(Status.MEAL == Status.MEAL)  # 走 __eq__：是同一个成员对象，True
print(Status.MEAL == 1)            # 走 __eq__：与整数 1 比较值，True
print(Status.MEAL == 'MEAL')       # 走 __eq__：与字符串 'MEAL' 比较名字，True
# 修复：原示例写的是 Status.MEAL < Status（把类当成了比较对象），
# 应比较两个具体的枚举成员才有意义
print(Status.MEAL < Status.FEMALE)  # 走 __lt__：1 < 2，True

# 由于 __lt__ 只定义了 < 比较，@total_ordering 自动生成了其他比较方法
# （__le__、__ne__、__gt__、__ge__），所以 > 也能正常使用
print(Status.MEAL > Status.FEMALE)  # 1 > 2，False（走 @total_ordering 生成的 __gt__）

print(Status.MEAL)  # 走 __str__，打印 MEAL(1)

# 补充：@total_ordering 生成的其他比较方法示例
print(Status.MEAL != Status.FEMALE)  # 走 __ne__：True
print(Status.MEAL <= Status.FEMALE)  # 走 __le__：True
print(Status.MEAL >= Status.FEMALE)  # 走 __ge__：False

'''
    @total_ordering 的原理：
    在 Python 中，__le__（<=）、__ne__（!=）、__gt__（>）、__ge__（>=）
    是用于实现比较运算符的特殊方法。
    只需要实现 __eq__ 和其中一个基础比较方法（如 __lt__），
    @total_ordering 就会自动生成其余所有比较方法（__le__、__ne__、__gt__、__ge__）。
    这使得枚举成员（以及其他自定义类）可以方便地参与排序（sorted、max、min 等）。
'''
