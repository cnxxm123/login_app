"""
【metaclass 元类 —— Python 高级特性】

一、核心概念：元类是"创建类的类"
    普通对象由类创建（如 stu = Student()，stu 是 Student 的实例）；
    而"类"本身也是对象，它由"元类"创建（Student 是元类的实例）。
    内置的 type 就是最基础的元类：
        type(Student)  ->  <class 'type'>
        type(stu)      ->  <class '__main__.Student'>
    元类 = 类的"模板/工厂"，负责在类被创建时统一做加工。

二、class 语句的本质
    当写上 `class Student(metaclass=Human): ...` 时，Python 实际执行：
        1. 收集类体命名空间（类里的属性和方法）
        2. 调用元类的 __new__(meta, name, bases, namespace) 创建类对象
        3. 调用元类的 __init__(cls, name, bases, namespace) 初始化类对象
    重写 __new__ 可以在类被"生出来"之前/之后修改它（比如给类加属性）。
    注意：__new__ 返回的类对象，就是最终声明的那个类。

三、元类的继承关系
    - 所有普通类（如 Student）的元类默认为 type。
    - 元类本身也是类，所以元类（如 Human）也是 type 的实例：
        type(Human) is type  ->  True
    - 元类之间也可以有继承关系；最顶层是 type。
    - 继承元类的子类，其元类由最近的父类元类决定（元类也会被继承）。

四、使用场景
    - 在类创建时统一添加属性/方法（本示例）
    - 自动注册类（插件系统、框架中扫描子类）
    - 自动校验类定义、自动生成 property（见 6metaclass实例.py）
    - ORM、API 框架（Django/SQLAlchemy）的底层基石

五、易错点
    1. 元类用 __new__ 时，第一个参数是元类自身（习惯命名 cls 或 mcs），
       而不是普通类的 cls。
    2. super().__new__(cls, *args) 中 cls 是要创建的"新类"，不是元类本身。
    3. 99% 的场景不需要自己写元类；只有需要"类级统一加工"时才用得上。
"""


# 定义一个名为 Human 的元类，它必须继承自 type
class Human(type):
    # __new__ 方法用于创建"类"（注意：元类的 __new__ 创建的是类对象）
    # cls 指向元类自身，args 依次是 (类名, 父类元组, 类体命名空间字典)
    @staticmethod
    def __new__(cls, *args, **kwargs):
        # 使用 super() 调用父类 type 的 __new__ 来真正创建出类对象 class_
        class_ = super().__new__(cls, *args)
        # 给新创建的类统一添加一个属性 freedom，并设置为 True
        class_.freedom = True
        # 遍历 class 语句中额外传入的关键字参数（如 country='china'）
        # 它们会出现在 kwargs 里，这里用 setattr 把它们统一设为类的属性
        for name, value in kwargs.items():
            setattr(class_, name, value)
        # 返回新创建的类，class_ 将成为 class 语句所声明的类
        return class_


# 定义一个名为 Student 的类，它继承自 object（不写 object 也行，因为默认就继承 object）
# metaclass=Human 表示：用 Human 这个元类来创建 Student
# country='china', address='广东' 会作为关键字参数传给元类的 __new__（进入 kwargs）
class Student(object, metaclass=Human, country='china', address='广东'):
    # 类体为空，表示这个类目前没有定义任何属性或方法
    pass


# 创建一个 Student 类的实例
stu = Student()

# 打印 Student 类的 country 和 freedom 属性（都是元类自动加上去的）
print(Student.country, Student.freedom)  # 输出: china True
# 打印 stu 实例的 country 和 freedom 属性（实例可以访问类属性）
print(stu.country, stu.freedom)          # 输出: china True


# =====================================================================
# 补充示例一：验证元类关系链（谁是"创建类"的类）
# =====================================================================
print('\n===== 补充示例一：元类关系链 =====')
print('stu 的类型（由类创建）:', type(stu))        # <class '__main__.Student'>
print('Student 的类型（由元类创建）:', type(Student))  # <class '__main__.Human'>
print('Student 的元类是 Human:', Student.__class__ is Human)  # True
print('Human 自身也是 type 的实例:', type(Human) is type)      # True
print('type 的元类是 type 自己:', type(type) is type)          # True
print('所有类的最终父类 object 的元类也是 type:', type(object) is type)  # True


# =====================================================================
# 补充示例二：用 __init__ 阶段自动注册子类（插件系统的常见套路）
# 元类除了 __new__，还可以重写 __init__ 做"类创建后的初始化"
# =====================================================================
_registry = {}   # 全局注册表：记录所有注册进来的插件类


class RegistryMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        # 先调用父类 type 的 __new__ 正常创建类
        return super().__new__(cls, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)
        # 排除元类自己（RegistryMeta 以 object 为父类，我们只注册它的子类）
        if bases != (object,):
            _registry[name] = cls     # 类被创建出来时，自动登记进注册表
            print(f'自动注册类: {name}')


# 下面的类都继承 object 并且使用 RegistryMeta 元类，所以会自动注册
class PluginBase(object, metaclass=RegistryMeta):   # bases==(object,) 不注册
    def run(self):
        raise NotImplementedError


class PluginA(PluginBase):   # 继承 PluginBase，元类仍为 RegistryMeta -> 自动注册
    def run(self):
        print('PluginA 运行')


class PluginB(PluginBase):
    def run(self):
        print('PluginB 运行')


print('\n注册表内容:', _registry)
# 根据名称动态取出插件并运行
_registry['PluginA']().run()    # 输出: PluginA 运行
