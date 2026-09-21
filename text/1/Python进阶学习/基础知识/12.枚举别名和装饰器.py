"""
============================================
枚举的别名（Alias）与 @enum.unique 装饰器
============================================

一、核心概念
    在枚举中，如果两个成员的值相同，那么后定义的成员会成为先定义成员的"别名"（alias）。
    别名并不是一个新的独立成员，它和主成员指向同一个对象。

二、别名机制
    1. 值相同：后定义的成员与前一个成员的值相同，则它是前一个成员的别名。
    2. 遍历时只显示主成员：for 循环遍历枚举时，只会遍历出每个值对应的"主成员"，
       别名不会单独出现。
    3. __members__：枚举类有一个 __members__ 属性（有序字典），
       里面包含所有名字（包括别名），可以看到全部成员。
    4. 判断相等：由于别名指向同一对象，
       Status.OK is Status.SUCESS 为 True，Status.OK == Status.SUCESS 也为 True。

三、@enum.unique 装饰器
    1. 作用：强制规定枚举成员的值必须唯一。
    2. 使用：在枚举类上方加 @enum.unique 装饰器。
    3. 报错：如果类中存在值相同的成员（别名），定义该类时会抛出
       ValueError: duplicate values found in <enum 'xxx'>: SUCESS -> OK
    4. 适用：当业务上要求每个枚举值必须唯一时，用 @enum.unique 可以在"定义阶段"
       就发现错误，而不是等到运行时。

四、注意事项与易错点
    1. 别名不会被遍历出来，如果你需要拿到所有名字，请使用 __members__。
    2. 本示例中 SUCESS、WORNG 其实是 SUCCESS、WRONG 的拼写笔误，
       但它们与前面成员值相同，因此只是别名而不是独立成员——
       这提醒我们：给枚举命名要认真，否则很容易因拼写错误产生难以察觉的别名。
    3. 一旦使用 @enum.unique，任何值重复都会在类定义阶段直接报错。
"""

import enum
from enum import Enum


class Status(Enum):
    OK = 1       # 主成员：值 1
    SUCESS = 1   # 别名：值与 OK 相同（SUCCESS 的拼写笔误），所以是 OK 的别名
    FAIL = 2     # 主成员：值 2
    WORNG = 2    # 别名：值与 FAIL 相同，是 FAIL 的别名


@enum.unique  # 规定成员的值必须唯一，若重复会直接报 ValueError
class Gneder(Enum):  # 保留原示例的类名，注意其拼写是 G-e-n-d-e-r（正确拼写应为 Gender）
    MALE = 1
    FEMALE = 2


print(Status.__members__)  # 打印出全部成员（包括别名）
# 输出形如：{'OK': <Status.OK: 1>, 'SUCESS': <Status.OK: 1>,
#           'FAIL': <Status.FAIL: 2>, 'WORNG': <Status.FAIL: 2>}
# 注意：SUCESS、WORNG 的"值"指向的是主成员 OK / FAIL

for i in Status:  # 遍历时只会遍历出主成员（值相同的只出现一次）
    print(i.name)  # 输出 OK、FAIL，不会单独输出 SUCESS、WORNG

print(Status.OK == Status.SUCESS)  # True  两者的值一样
print(Status.OK is Status.SUCESS)  # True  说明它们指向同一个对象（别名）

# 别名可以直接通过名字访问，得到的就是主成员对象
print(Status.SUCESS)             # Status.OK
print(Status.SUCESS.name, Status.SUCESS.value)  # OK 1


# ==================== 补充示例：@enum.unique 检测到重复值时报错 ====================

try:
    # 由于 C 的值 1 与 A 重复，定义这个类时会抛出 ValueError
    @enum.unique  # 关键：必须加上 @enum.unique 装饰器，重复值才会报错
    class CodeBad(Enum):
        A = 1
        B = 2
        C = 1  # 与 A 重复，@enum.unique 会在这里直接报错
except ValueError as e:
    print(f'@enum.unique 发现重复值：{e}')
