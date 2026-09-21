"""
知识点：@property 装饰器（属性访问控制）
==========================================

【核心概念】
- @property 可以把一个"方法"变成"属性"来访问：
  原本要写 obj.get_age()，变成直接写 obj.age，看起来就像访问普通属性。
- 配合 @xxx.setter，还能把"赋值"也变成方法调用：
  原本是 obj.age = 10，现在会去执行对应的 setter 方法。
- 主要目的：在"读取"和"赋值"中间插入校验/计算逻辑，
  防止用户给属性赋一个不合法的值，同时对外仍保持"普通属性"的简洁写法。

【工作原理（getter/setter 完整流程）】
1. @property 修饰 def age(self) -> getter（读取器）。
   访问 obj.age 时，Python 自动调用 getter 方法，返回 self.__age。
2. @age.setter 修饰 def age(self, age) -> setter（设置器）。
   执行 obj.age = 10 时，Python 自动调用 setter 方法，把 10 传入 age 参数。
3. 赋值流程：obj.age = 10
   -> 找到 age 这个 property 的 setter
   -> 校验（如 0 <= age <= 100）
   -> 通过校验后，把真正的数据存到"内部的隐藏属性" self.__age。

【为什么内部要存到 self.__age（而不是 self.age）？—— 重点！】
- 在 setter 里如果写 self.age = age：
  -> 这又是一次"给 age 赋值"，会【再次】调用 setter
  -> setter 里又执行 self.age = age -> 再调用 setter -> 无限递归，直到报 RecursionError。
- 所以必须把真实数据存到"另一个名字"（习惯用下划线/双下划线，如 self.__age），
  让 getter 读 self.__age、setter 写 self.__age，从而避免和自己同名造成无限递归。
- 同理，getter 里也绝对不能写 return self.age（会再次触发 getter 无限递归）。

【使用场景】
- 对赋值做范围/类型校验（年龄、长度、价格等）。
- 把"计算出来的值"伪装成属性（见 7 号文件：只读 property + 缓存）。
- 后期需要给属性加逻辑时，不用改动外部调用代码。

【注意事项 / 易错点】
1. getter 和 setter 方法名必须相同（这里都叫 age），setter 用 @age.setter 绑定。
2. 内部存储必须用不同名字（self.__age），否则无限递归。
3. 只写 @property 而不写 @xxx.setter，则该属性是"只读"的（见 7 号文件）。
4. 校验不通过时要用 raise ValueError(...) 抛异常，不能直接 raise 字符串。
"""

# 为了防止用户将属性赋值为一个错误的值，使用property装饰器：
#   1. 将方法变为属性（getter，读取）
#   2. 将方法变为属性的赋值（setter，写入）
class Student:
    def __init__(self, name, age):
        self.name = name
        # 这里的 self.age = age 调用的并不是普通属性赋值，
        # 而是"触发下面定义的 age setter 方法"（会先做合法性校验）。
        self.age = age

    @property  # @property 将方法变成属性（getter）
    def age(self):
        # getter：当外部访问 st1.age 时被自动调用。
        # 注意：这里必须返回 self.__age（内部隐藏变量），
        # 绝不能写 return self.age，否则会再次触发 getter 造成无限递归。
        return self.__age

    @age.setter  # @age.setter 将方法变为属性的赋值（setter）
    def age(self, age):
        # setter：当外部执行 st1.age = 10 时被自动调用，age 参数就是被赋的值。
        # 在这里可以对赋值进行校验。
        if age < 0 or age > 100:
            # 校验不通过：抛出一个 ValueError 异常（这是合法写法）。
            # 注意：不能写 raise 'age不合规范'（那样是非法语法）。
            raise ValueError('age不合规范')
        # 校验通过后，把数据存到"内部的隐藏属性" self.__age。
        # 注意：这里绝不能写 self.age = age，
        # 否则又会触发一次 setter -> 无限递归 -> RecursionError。
        self.__age = age


st1 = Student('小明', 1)   # 创建对象，__init__ 里 self.age = 1 会走一遍 setter
print(st1.age)             # 访问属性 -> 调用 getter，输出 1
st1.age = 10               # 赋值 -> 调用 setter，校验通过后存到 self.__age
print(st1.age)             # 再次调用 getter，输出 10
print('----------------------------------------')

# ---- 补充：setter 的校验生效演示 ----
try:
    st1.age = 200          # 200 不在 [0, 100]，校验失败
except ValueError as e:
    print('赋值 200 被拦截:', e)   # 输出：赋值 200 被拦截: age不合规范

try:
    st2 = Student('小红', -5)      # 构造时传入 -5，也会被 setter 拦截
except ValueError as e:
    print('构造传入 -5 被拦截:', e)  # 输出：构造传入 -5 被拦截: age不合规范
