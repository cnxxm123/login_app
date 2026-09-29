"""
============================================
枚举（Enum）
============================================

一、核心概念
    枚举（Enumeration）是一组"命名常量"的集合。
    它把一组固定的、有意义的取值集中定义在一个类中，
    每个成员由"名字（name）"和"值（value）"两部分组成。

二、为什么要用枚举
    1. 可读性：用 Gender.MALE 代替裸的 1 或 'MALE'，语义更清晰。
    2. 防手误：把取值限定在枚举成员中，避免随意传错数字/字符串，
       也避免"魔法数字"散落在代码各处。
    3. 集中管理：相关常量集中定义，便于统一修改和维护。

三、工作原理
    1. 通过 from enum import Enum 导入，class Gender(Enum) 即可创建枚举类。
    2. 枚举成员是类的属性（如 Gender.MALE），每个成员都是 Enum 类的实例。
    3. 枚举类不能被直接实例化（Gender() 会报错）；同一名字只对应一个成员实例。
    4. 每个成员有 name（成员名，字符串）和 value（成员的值）两个属性。
    5. 反向查找：
       - 按名字查找：Gender['MALE'] -> Gender.MALE
       - 按值查找：Gender(1) -> Gender.MALE
    6. 枚举类是"可迭代"的，for 循环可以遍历出所有成员。

四、注意事项与易错点
    1. 枚举成员的值不可变，创建后不能修改。
    2. 不能给枚举类动态添加新属性。
    3. 同一个值只允许一个名字，值相同的后面成员会成为"别名"（见 12 号文件）。
    4. 枚举成员是单例对象，比较身份建议用 is 或 ==（两者一致）。
"""

from enum import Enum


class Gender(Enum):  # 创建枚举类，继承自 Enum
    MALE = 1    # 成员 MALE，值为 1
    FEMALE = 2  # 成员 FEMALE，值为 2


class Student:
    def __init__(self, gender: Gender):
        # 类型标注 Gender 提示这里应该传入枚举成员，
        # 这样就能避免传入任意魔法数字，保证取值的合法性
        self.gender = gender


student = Student(Gender.MALE)  # 传入枚举成员作为参数

# 成员与类的类型
print(Gender.MALE, type(Gender.MALE))  # Gender.MALE <enum 'Gender'>
print(Gender, type(Gender))            # <enum 'Gender'> <class 'enum.EnumType'>

# 每个成员都有 name 和 value 两个属性
print(Gender.MALE.name)     # MALE  成员名（字符串）
print(Gender.MALE.value)    # 1     成员的值
print(student.gender.name)  # MALE  通过对象访问其枚举属性

# 反向查找 1：通过"名字字符串"查找
s_gender = 'MALE'   # 将对应的字符串转为枚举成员
print(Gender[s_gender])  # Gender.MALE

# 反向查找 2：通过"值"查找
i_gender = 1        # 将对应的值转为枚举成员
print(Gender(i_gender))  # Gender.MALE

# 遍历枚举类：for 循环会依次取出每个成员，打印其名字和值
for i in Gender:
    print(i, i.name, i.value)


# ==================== 补充示例 1：枚举类不能被实例化 ====================

try:
    Gender()  # 枚举类不能直接创建实例，会抛 TypeError
except TypeError as e:
    print(f'枚举类不能实例化：{e}')


# ==================== 补充示例 2：枚举成员的值不可修改 ====================

try:
    Gender.MALE.value = 100  # 不能修改枚举成员的值
except AttributeError as e:
    print(f'不能修改枚举成员的值：{e}')


# ==================== 补充示例 3：用类常量代替魔法数字，提升可读性 ====================
# 不使用枚举时的替代方案：在类里定义常量，语义比裸数字清晰得多

class Order:
    PENDING = 0      # 待支付
    PAID = 1         # 已支付
    SHIPPED = 2      # 已发货
    COMPLETED = 3    # 已完成


print(Order.PAID, Order.COMPLETED)  # 通过类常量访问，语义清晰
