"""
============================================
多继承（Multiple Inheritance）—— 不建议使用
============================================

一、核心概念
    一个子类可以同时继承多个父类，从而复用多个父类的属性和方法。
    例如 class Per(per2, per1) 表示 Per 同时继承 per2 和 per1。

二、MRO（方法解析顺序，Method Resolution Order）
    1. 当子类调用一个方法时，Python 需要决定"先从哪个类开始查找方法"，
       这个查找顺序就是 MRO。
    2. 可以通过 类名.__mro__ 或 类名.mro() 查看。
    3. 多继承时，MRO 采用 C3 线性化算法：子类优先，多个父类按"从左到右"
       的顺序继承，且每个父类在 MRO 中只出现一次。
       例：class Per(per2, per1) 的 MRO 大致为：Per -> per2 -> per1 -> object。

三、super() 在多重继承中的调用顺序
    1. super() 不是简单地调用"第一个父类"，而是根据 MRO 找到"当前类的下一个类"。
    2. 因此，在 Per.gender() 中调用 super().gender()，会按照 MRO
       （Per -> per2 -> per1 -> object）先去调用 per2.gender()。
    3. 直接用"父类名.方法(self)" 的方式（如 per1.hello(self)）是"显式指定"，
       不经过 MRO，适合有目的地调用某个具体父类的方法。

四、钻石继承问题（Diamond Problem）
    当两个父类拥有共同的祖先时，继承关系形成一个菱形。
    例如：D 继承 B 和 C，而 B、C 都继承 A。
    此时 MRO（C3 算法）会保证 A 只被处理一次，顺序大致为：
    D -> B -> C -> A -> object。
    如果 super() 协作没有处理好，可能出现方法被重复调用或顺序混乱的问题。

五、为什么不建议使用多继承
    1. 逻辑复杂：继承关系像一张网，可读性和可维护性下降。
    2. 方法冲突：多个父类有同名方法时，调用结果依赖 MRO，容易产生困惑。
    3. 钻石问题：可能导致方法被重复调用或覆盖顺序难以预测。
    4. 推荐替代方案：优先使用"单继承 + 组合"（把功能拆成独立类，通过属性引用），
       或"混入类（Mixin）"等更可控的方式。
"""


class per1:
    """父类 1"""

    def gender(self):
        print(1)

    def hello(self):
        print('hello,1')


class per2:
    """父类 2"""

    def gender(self):
        print(2)

    def hello(self):
        print('hello,2')


class Per(per2, per1):
    """多继承：同时继承 per2 和 per1（从左到右，per2 在 MRO 中优先级更高）"""

    def gender(self):
        # super() 会按照 MRO（Per -> per2 -> per1 -> object）调用下一个类的 gender()
        super().gender()  # 调用 per2.gender()，打印 2

    def hello(self):
        # 显式指定调用某个父类的方法（不走 MRO，直接指定类）
        per1.hello(self)  # 调用 per1.hello，打印 'hello,1'
        per2.hello(self)  # 调用 per2.hello，打印 'hello,2'


per = Per()
per.gender()  # 打印 2（super() 按 MRO 先调用 per2 的方法）
per.hello()   # 依次打印 'hello,1' 和 'hello,2'


# ==================== 补充示例 1：查看 MRO ====================

print('-' * 40)
# 查看 Per 的方法解析顺序：Per -> per2 -> per1 -> object
for cls in Per.__mro__:
    print(cls)


# ==================== 补充示例 2：钻石继承问题 ====================

print('-' * 40)


class A:
    """钻石的顶端"""

    def greet(self):
        print('A.greet')
        # A 之上只有 object，object 没有 greet 方法，所以这里不再调用 super()


class B(A):
    def greet(self):
        print('B.greet')
        super().greet()  # 按 MRO 继续调用下一个类的方法（C）


class C(A):
    def greet(self):
        print('C.greet')
        super().greet()  # 按 MRO 继续调用下一个类的方法（A）


class D(B, C):
    def greet(self):
        print('D.greet')
        super().greet()  # 按 MRO 继续调用下一个类的方法（B）


d = D()
d.greet()
# 输出顺序：
# D.greet
# B.greet
# C.greet
# A.greet
# 可见 A 只被调用一次，这就是 C3 线性化（MRO）的效果

print('-' * 40)
# 查看 D 的 MRO：D -> B -> C -> A -> object
for cls in D.__mro__:
    print(cls)
