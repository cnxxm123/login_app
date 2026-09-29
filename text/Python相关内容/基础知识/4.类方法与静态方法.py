"""
知识点：类方法（@classmethod）与静态方法（@staticmethod）
=============================================================

【核心概念】
- 实例方法（普通方法）：第一个参数是 self（实例本身），只有实例才能调用它的内部状态。
- 类方法 @classmethod：第一个参数是 cls（类本身），
  通过类调用或通过实例调用都行，cls 自动传入"当前类"。
  它可以访问/修改类变量，适合写"操作类级别数据"的方法。
- 静态方法 @staticmethod：本质上就是一个普通的函数，
  【不会】自动传 self 或 cls，也不依赖类和实例的任何状态，
  只是"放在类里面"方便归类，通常用来做工具函数。

【工作原理】
- @classmethod 装饰后，Python 会把方法绑定为"绑定到类"的函数：
  调用 Student.hello(...) 时，Python 自动把 Student 作为第一个实参传给 cls。
- @staticmethod 装饰后，方法就是一个普通函数：
  不管通过类还是实例调用，都不会自动传任何参数，参数列表里写了什么就要传什么。

【使用场景】
- 类方法：需要访问或修改类变量时（例如统计所有实例数量、修改全局配置）；
  也常用作"备选构造函数"，比如 Date.from_string('2024-01-01')。
- 静态方法：与类和实例无关的纯工具函数（如判断参数是否合法、格式化数据）。

【注意事项 / 易错点】
1. 类方法里拿到的是 cls，是"类"，不是实例；
   因此在类方法中不能直接访问 self 开头的实例变量（没有实例对象）。
2. 静态方法如果不小心加了 self 参数，调用时会因为没有自动传 self 而报"缺少参数"。
3. 类方法中想创建实例，要用 cls(...) 而不是 Student(...)，
   这样才能在继承时正确创建"子类"的实例。
4. 通过"实例"调用类方法/静态方法也完全合法，Python 会忽略实例本身，
   但语义上一般推荐用"类名"去调用，避免误导。
5. 在类方法里改类变量，会影响所有实例共享的值（因为操作的是同一个类变量）。
"""


class Student:
    name = 'abc'           # 类变量，供类方法 / 静态方法访问

    @classmethod  # 加上 @classmethod 装饰器表示类方法，cls 表示类本身
    def hello(cls, a):
        # cls 就是 Student 这个类，因此可以访问类变量 cls.name。
        print(f'Hello {cls.name}', a)

    @staticmethod  # 加上 @staticmethod 装饰器表示静态方法
    # 静态方法就是普通的函数，只不过是在类的范围内定义。
    # 注意：这里【没有】 self 也没有 cls，因为不会自动传任何参数。
    # 静态方法一般拿来做工具函数。
    def out():
        print(f'{Student.name}')


Student.hello('14')   # 类可以直接调用类方法
# 调用时 Python 自动把 Student 传给 cls，因此等价于 hello(Student, '14')
print('----------------------------------------')

st1 = Student()
st1.hello('14')       # 对象也可以直接调用类方法
# 即使通过实例调用，Python 传给 cls 的依然是"类"Student，而不是实例 st1
print('----------------------------------------')

Student.out()         # 类可以直接调用静态方法
st1.out()             # 对象也可以直接调用静态方法（实例会被忽略，不自动传参）
print('----------------------------------------')


# ============================================================
# 补充示例 1：类方法的典型用途 —— 修改类变量 / 记录实例个数
# ============================================================

class Cat:
    count = 0                     # 类变量：统计创建了多少只猫

    def __init__(self, name):
        self.name = name          # 实例变量
        Cat.count += 1            # 每创建一个实例，计数 +1

    @classmethod
    def get_count(cls):
        # cls 就是 Cat，可以读取类变量 count。
        return cls.count

    @classmethod
    def set_count(cls, n):
        # 类方法也可以修改类变量，修改后所有实例共享的值都会变化。
        cls.count = n


c1 = Cat('小白')
c2 = Cat('小黑')
print(Cat.get_count())    # 输出 2（通过类方法拿到类变量）
Cat.set_count(100)        # 修改类变量
print(Cat.get_count())    # 输出 100
print('----------------------------------------')


# ============================================================
# 补充示例 2：类方法作"备选构造函数"、静态方法作"工具函数"
# ============================================================

class Date:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    @classmethod
    def from_string(cls, s):
        # 备选构造函数：从字符串 '2024-01-05' 创建对象。
        # 使用 cls(...) 而不是 Date(...)，继承时依然能创建正确的子类实例。
        y, m, d = map(int, s.split('-'))
        return cls(y, m, d)

    @staticmethod
    def is_valid_month(m):
        # 工具函数：与具体对象无关，只是判断月份是否合法。
        return 1 <= m <= 12


d = Date.from_string('2024-01-05')   # 通过类方法创建实例
print(d.year, d.month, d.day)        # 输出 2024 1 5
print(Date.is_valid_month(13))       # 输出 False（静态工具函数直接调用）
print(Date.is_valid_month(5))        # 输出 True
# 对比记忆：
#   类方法   -> 第一个参数是 cls，能访问/修改类变量，常用作"备选构造函数"
#   静态方法 -> 不带 self/cls，纯工具函数，不访问类和实例的任何状态
