"""
============================================
继承（Inheritance）
============================================

一、核心概念
    继承是面向对象编程（OOP）的三大特性之一（封装、继承、多态）。
    通过继承，子类（派生类）可以复用父类（基类/超类）的属性和方法，
    并在其基础上扩展新功能，从而避免代码重复，提高代码的可复用性和可维护性。
    继承表达的是 "is-a"（是一种）的关系：学生（Student）是人（Person）。

二、工作原理
    1. 语法：class 子类名(父类名): —— 在类名后面的括号里写上父类名即可继承。
    2. 属性查找顺序：访问对象属性/方法时，Python 会先在实例自身找，
       找不到再去它的类里找，再找不到就沿着继承链往父类找，
       直到 object 为止。
    3. super() 的原理：
       - super() 并不是简单地调用"父类"，而是根据类的 MRO
         （方法解析顺序，Method Resolution Order）找到"当前类的下一个类"。
       - 单继承下 MRO 就是：子类 -> 父类 -> object，所以 super() 等价于"父类"。
       - super() 必须配合实例使用（如 super().__init__(...)、super().say()），
         它会自动传入 self，调用父类的同名方法。
    4. 方法重写（Override）：子类定义与父类同名的方法，就会覆盖父类的实现，
       调用时执行的是子类版本——这是"多态"的基础。

三、使用场景
    - 多个类有大量公共属性和行为时，抽出公共父类。
    - 在父类基础上扩展（新增方法）或修改（重写方法）已有行为。

四、注意事项与易错点
    1. 推荐使用单继承：Python 虽然支持多继承，但层级过深会让代码难以理解，
       日常开发优先用单继承 + 组合（见 14 号文件）。
    2. 子类若重写了 __init__，父类的 __init__ 不会自动调用，
       必须手动 super().__init__(...) 初始化父类属性，否则父类属性未定义。
    3. isinstance 与 type 的区别：
       - type(obj) 判断的是"精确类型"；
       - isinstance(obj, 类) 判断"是某类或其子类的实例"。
         所以 Student 的实例对 Person 做 isinstance 返回 True，但 type 严格相等为 False。
    4. 方法重写后，如仍需父类逻辑，可在子类方法里用 super().方法() 先调用父类版本。
"""


# ==================== 基础示例：单继承 ====================

class Person:
    """父类（基类）：定义所有人都具有的公共属性和行为"""

    def __init__(self, name, age):
        # 初始化属性：name 姓名、age 年龄
        self.name = name
        self.age = age

    def say(self):
        # 父类中定义的普通方法，子类可以直接继承使用
        print('Person')


class Student(Person):
    """子类（派生类）：继承自 Person，表示"学生是一种人"（is-a 关系）"""

    def __init__(self, wed, fr):
        # 这里重写了 __init__，父类的 __init__ 不会自动执行，
        # 必须显式调用 super().__init__(...) 来初始化父类中的 name、age 属性。
        # super() 会按照 MRO（Student -> Person -> object）找到下一个类 Person，
        # 等价于调用 Person.__init__(self, wed, fr)
        super().__init__(wed, fr)  # wed、fr 必须传，因为父类需要这两个参数才能完成初始化

    def say_stu(self):
        # 在子类方法中，也可以通过 super() 调用父类中被继承的方法
        super().say()  # 调用父类 Person 的 say()，打印 'Person'
        print('Student')  # 修复了原示例中的拼写错误 'Syudent' -> 'Student'


# 实例化子类：Student('ff', 12) 会先创建对象，再执行 Student.__init__('ff', 12)，
# 后者又通过 super().__init__('ff', 12) 去初始化父类的 name='ff'、age=12
st = Student('ff', 12)

print(type(st))                # <class '__main__.Student'>：st 的精确类型是 Student
print(isinstance(st, Person))  # True：Student 是 Person 的子类，所以 st 也是 Person 的实例

st.say()      # 子类没有重写 say，所以调用的是父类 Person.say()，打印 'Person'
st.say_stu()  # 内部先 super().say() 打印 'Person'，再打印 'Student'

# 继承后，子类对象可以直接访问父类中定义的属性
print(f'name={st.name}, age={st.age}')  # name=ff, age=12


# ==================== 补充示例 1：isinstance 与 type 的区别 ====================

print('-' * 40)
print(f'type(st) == Student       -> {type(st) == Student}')      # True
print(f'type(st) == Person        -> {type(st) == Person}')       # False：类型不精确匹配
print(f'isinstance(st, Student)   -> {isinstance(st, Student)}')  # True
print(f'isinstance(st, Person)    -> {isinstance(st, Person)}')   # True：子类实例也算父类实例

# 结论：判断"是不是某个类或其子类的实例"用 isinstance；
# 判断"精确类型"才用 type(obj) == 某类。


# ==================== 补充示例 2：方法重写与多态 ====================
# 多态：同一个方法名，对不同对象表现出不同的行为。
# 只要对象提供了同名方法，就可以被统一调用，而不必关心它具体是哪个类。

class Animal:
    """父类：定义默认行为"""

    def sound(self):
        print('动物发出声音')


class Cat(Animal):
    """子类：重写父类的 sound 方法"""

    def sound(self):  # 方法重写（Override）：覆盖父类实现
        print('喵喵喵')


class Dog(Animal):
    """子类：重写父类的 sound 方法"""

    def sound(self):
        print('汪汪汪')


def make_sound(animal):
    # 多态：统一调用接口，具体行为由传入对象的实际类型决定
    animal.sound()


print('-' * 40)
make_sound(Cat())       # 喵喵喵
make_sound(Dog())       # 汪汪汪
make_sound(Animal())    # 动物发出声音（父类默认实现）
