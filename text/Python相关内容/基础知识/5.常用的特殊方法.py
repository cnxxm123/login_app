"""
知识点：常用的特殊方法（魔法方法）
=====================================

【核心概念】
- 特殊方法（也称魔法方法 / dunder 方法）是名字以双下划线开头和结尾的方法，
  例如 __init__、__str__、__eq__ 等。
  它们【不需要也不能直接调用】，而是被 Python 解释器在特定时机"自动调用"。
- 通过定义这些方法，可以让我们的对象拥有与内置类型（int、str、list 等）
  一样的"语法行为"，例如用 print() 打印、用 == 比较、放进集合、用 len() 求长度等。

【工作原理（关键机制）】
1. __str__ / __repr__：print(obj) 会优先调用 __str__；若没定义 __str__，
   会自动"退回(fallback)"调用 __repr__。开发者工具/交互式环境则用 __repr__。
2. __eq__ 与 __hash__ 联动：这是最重要的坑之一！
   - 如果定义了 __eq__ 而没有定义 __hash__，Python 会把该类的 __hash__ 置为 None，
     导致对象【不可哈希】，放进 set / 作为 dict 的键会报 TypeError。
   - 原因：既然两个对象可能"相等"（__eq__ 判定），就必须保证相等的对象 hash 相同，
     而默认的 hash 是基于 id（内存地址）的，两者会冲突。
   - 解决办法：同时定义 __eq__ 和 __hash__（让相等对象返回相同 hash），
     或者在子类中用 __hash__ = object.__hash__ 显式恢复。
   - 可哈希对象要求：a == b 为真时，hash(a) == hash(b) 必须为真。
3. __bool__ 的调用时机：除了 bool(obj) 之外，
   if obj、while obj、obj and x、obj or x、not obj 等只要需要对对象"求真值"的地方，
   都会自动调用 __bool__。若未定义 __bool__，Python 会退而调用 __len__
   （len 为 0 则 False）；两者都没有则一律为 True。
4. __del__ 在对象被垃圾回收(引用计数归零)前调用，调用时机不确定，不要放重要逻辑。

【使用场景】
- __str__/__repr__：调试与打印更友好、可读。
- __eq__/__hash__：让对象支持 == 比较，并可放入 set / dict。
- __bool__：让对象支持真假判断。
- __len__：让对象支持 len(obj)，常配合容器类。
- __add__：让对象支持 + 运算符，例如自定义向量/复数/金额相加。

【注意事项 / 易错点】
1. 定义了 __eq__ 忘记定义 __hash__ -> 对象不可哈希（最经典的大坑）。
2. __str__ 必须返回字符串，否则报错。
3. __bool__ 必须返回布尔值；__len__ 必须返回非负整数。
4. print() 会自动 fallback 到 __repr__，所以只定义 __repr__ 时 print 也能显示。
5. 这些方法不一定都要自己写，按需定义即可。
"""

'''
六个常用方法：
    1. __str__     调用方法：print(对象) 或 str(对象)
    2. __repr__    调用方法：直接  print(repr(对象))
    3. __eq__      调用方法：使用 == 判断两个对象是否相等
    4. __hash__    调用方法：把对象放进 set（集合） 时自动对调用 __hash__
    5. __bool__    调用方法：bool(my_date_1)
    6. __del__     调用方法：对象被删除时自动调用
这些方法不一定都要自己写
'''

class MyDate:
    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day

    '''
    __str__返回描述对象本身的字符串，但内容并不是规定死的，实际上返回什么都行，但一定要是字符串
    该描述主要面向用户
    注意：print(对象) 会自动调用 __str__；如果没定义 __str__，
          print 会自动 fallback 到 __repr__。
    '''
    def __str__(self):
        return f'{self.year}-{self.month}-{self.day}'

    '''
    __repr__返回描述对象本身的字符串，但内容并不是规定死的，实际上返回什么都行，但一定要是字符串
    该描述主要面向开发者
    注意：交互式环境输入对象名、以及 print(repr(obj)) 时会调用 __repr__。
          只定义 __repr__ 时，print(obj) 也会 fallback 到它。
    '''
    def __repr__(self):
        return f'MyDate:{self.year}-{self.month}-{self.day}'

    '''
    一般情况下就算两个对象的属性都相同他们也不相等，使用__eq__方法可以自己设定判断两个对象是否相等的判断方法，
    '''
    def __eq__(self, other):
        if not isinstance(other, MyDate):
            return False
        else:
            return self.year == other.year and self.month == other.month and self.day == other.day

    '''
    __hash__方法用于实现根据对象生成hash值的逻辑,
    一般类会自动计算，不需要自己定义这个方法,当把对象放在 dict 或 set 里面时这个方法会被调用
    关键联动规则：
        - 只要定义了 __eq__，Python 就会把 __hash__ 置为 None（对象不可哈希），
          所以必须【同时】定义 __hash__，对象才能放进 set / dict。
        - 保证：两个对象 __eq__ 相等时，hash 也必须相等。
          这里用 year、month、day 一起参与哈希，满足该约束。
    '''
    def __hash__(self):
        print('__hash__已调用')
        return hash(self.year + self.month * 100 + self.day * 101)

    '''
     __bool__方法用于返回对象被bool函数求解时返回的一个布尔值
     如果没有实现这个方法，__len__将会被用户求解布尔值
     调用时机：bool(obj)、if obj、while obj、obj and x、obj or x、not obj 都会调用它。
    '''
    def __bool__(self):
        return self.year > 2020

    '''
    __del__方法在对象被垃圾回收前调用，因为不知道对象何时被回收，所以不要用来做一些重要的事情
    一般拿来清除创建对象时产生的图片等资源
    '''
    def __del__(self):
        print(f"回收")


my_date_1 = MyDate(2000, 11, 3)
my_date_2 = MyDate(2000, 11, 3)
my_date_3 = MyDate(2000, 7, 3)

print('__str__方法:', my_date_1)  # 直接打印就可以输出 __str__  返回的内容
print('-------------------------------------------')
print('__repr__方法:', repr(my_date_1))  # 输出__repr__  返回的内容
print('-------------------------------------------')
print('__eq__方法:', my_date_1 == my_date_2)  # 使用 == 就可以调用 __eq__ 方法
print('__eq__方法:', my_date_1 == my_date_3)  # 使用 == 就可以调用 __eq__ 方法
print('-------------------------------------------')
my_set = set()
my_set.add(my_date_1)  # 把对象放进 set 时自动对调用 __hash__
print('hash值:', hash(my_date_1))
print('-------------------------------------------')
print('__bool__方法', bool(my_date_1))

# ---- __bool__ 的其他调用时机：if / and / or / not 都会调用 ----
if my_date_1:                     # 这里会调用 __bool__（year=2000 不大于 2020 -> False）
    print('my_date_1 为真')
else:
    print('my_date_1 为假（因为 __bool__ 返回 year>2020）')

print(not my_date_1)              # not 也会调用 __bool__，输出 True
print(my_date_1 and '条件成立')    # and 也会调用 __bool__，此处为假 -> 输出 False
print('-------------------------------------------')


# ============================================================
# 补充示例 1：只定义 __eq__ 而不定义 __hash__ 会导致对象不可哈希
# ============================================================

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        # 只定义 __eq__，没定义 __hash__
        return isinstance(other, Point) and self.x == other.x and self.y == other.y


p1 = Point(1, 2)
try:
    print('hash(p1) =', hash(p1))
except TypeError as e:
    # 上面这行在 Python 3 中会抛 TypeError：unhashable type: 'Point'
    # 因为定义了 __eq__ 后 __hash__ 被置为 None，对象变得不可哈希。
    print('hash(p1) 报错:', e)
    print('原因：定义了 __eq__ 后 __hash__ 被自动置为 None，对象不可哈希。')
    print('解决办法：同时定义 __hash__，例如：')
    print('    def __hash__(self):')
    print('        return hash((self.x, self.y))')
    print('这样对象就能放进 set / 作为 dict 的键了。')
print('-------------------------------------------')


# ============================================================
# 补充示例 2：__len__ 与 __add__ 两个常用特殊方法
# ============================================================

class Vector:
    """一个简单的二维向量，支持 len() 和 + 运算。"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __len__(self):
        # len(v) 会调用 __len__，必须返回非负整数。
        # 这里返回"非零分量的个数"来演示。
        return (1 if self.x != 0 else 0) + (1 if self.y != 0 else 0)

    def __add__(self, other):
        # v1 + v2 会调用 __add__，返回一个新对象（不要修改 self）。
        if not isinstance(other, Vector):
            raise TypeError('只能和 Vector 相加')
        return Vector(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return f'Vector({self.x}, {self.y})'


v1 = Vector(1, 2)
v2 = Vector(3, 4)
print('len(v1) =', len(v1))       # 输出 2（两个分量都非零）
print('v1 + v2 =', v1 + v2)       # 输出 Vector(4, 6)，调用 __add__
