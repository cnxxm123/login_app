"""
【metaclass 实战实例：元类 + 描述符自动生成 property —— Python 高级特性】

一、本示例要解决的问题
    在 Student 类里，我们只想声明一个列表 props = ['name', 'age']，
    然后希望"类被创建时"，自动为 name、age 各生成一组 property 属性
    （即 obj.name 自动读写内部 _name，obj.age 自动读写内部 _age）。
    如果手动写，每个属性都要写一遍 getter/setter，很啰嗦；
    用元类可以在【类创建时】统一批量加工，一劳永逸。

二、核心流程（元类里做了什么）
    1. 类 Student 定义时，Python 调用元类 Human.__new__ 创建类对象。
    2. __new__ 里通过 super().__new__ 先正常创建类，然后读取类属性 class_.props
       （一个字符串列表：['name', 'age']）。
    3. 遍历 props 中的每个属性名：
         a. 用属性名创建描述符对象 prop = Prop(props_name)
            （描述符封装了读写底层 _xxx 的逻辑）
         b. 用 property(fget=prop.get, fset=prop.set) 生成 property 对象
         c. 用 setattr(class_, props_name, p_obj) 把 property 挂到类上
    4. 返回加工完成的类。
    从此每个实例访问 stu.name / stu.age 时，就会自动走 property 的读写逻辑。

三、为什么要在元类里做这件事
    - 时机对：类刚被创建、还没被实例化时就加工好，之后所有实例自动生效。
    - 集中：属性列表只维护一份 props，想加属性只需往列表里加一个名字。
    - 复用：换个类只要声明 props，就自动获得完整的属性访问器（"约定优于配置"）。
    - 对比：如果不用元类，就得在每个类里手写重复的 getter/setter 代码。

四、补充知识：描述符（Descriptor）
    Prop 是一个"描述符"：它定义了 get / set 方法（或者 __get__/__set__），
    当被放到类上并被实例访问时，Python 会调用描述符的方法来拦截读写。
    属性读写真正发生的位置：
        - 读 obj.name  -> property 的 fget -> Prop.get(obj) -> 返回 _name
        - 写 obj.name=值 -> property 的 fset -> Prop.set(obj, 值) -> 存到 _name

五、易错点
    1. 元类 __new__ 里要先用 super().__new__ 创建出类，才能 setattr 加工它。
    2. 描述符内部存值用带下划线的 _attr，避免和 property 名冲突（无限递归）。
    3. property(fget=..., fset=...) 只设置了读和写；如需删除可加 fdel。
"""


# 定义一个描述符类 Prop：封装"读/写底层 _xxx 属性"的逻辑
class Prop:
    def __init__(self, attr):
        # 初始化时，将属性名前面加上下划线，用于内部存储（如 'name' -> '_name'）
        # 加下划线的目的：避免内部变量名和对外暴露的 property 名冲突
        self._attr = f'_{attr}'

    def get(self, obj):
        # get 方法用于获取属性值：obj 是访问该属性的实例
        if not hasattr(obj, self._attr):
            # 如果对象还没有这个内部属性，则返回 None
            return None
        return getattr(obj, self._attr)   # 返回实例上的 _name 值

    def set(self, obj, value):
        # set 方法用于设置属性值：把 value 存到实例的 _name 属性上
        setattr(obj, self._attr, value)


# 定义一个元类 Human：负责在"类创建时"自动为每个属性生成 property
class Human(type):
    @staticmethod
    def __new__(cls, *args, **kwargs):
        # 调用父类 type 的 __new__ 创建出类对象 class_
        class_ = super().__new__(cls, *args)
        # 遍历类中定义的 props 属性列表（比如 ['name', 'age']）
        for props_name in class_.props:
            # 为每个属性名创建一个描述符实例（如 Prop('name') -> _attr='_name'）
            prop = Prop(props_name)
            # 用描述符的 get/set 方法生成一个 property 对象
            p_obj = property(fget=prop.get, fset=prop.set)
            # 把 property 对象设置为类的同名属性（类创建时统一加工完成）
            setattr(class_, props_name, p_obj)
        return class_


# 定义一个名为 Student 的类，它继承自 object，并使用 Human 作为它的元类
class Student(object, metaclass=Human):
    # 定义一个类属性 props，列出需要自动生成属性访问器的属性名
    # 想新增字段，只需往这个列表里加名字即可（这就是元类带来的"批量加工"）
    props = ['name', 'age']


# 创建一个 Student 类的实例
stu = Student()

# 尝试打印 stu 的 name 属性，此时属性尚未设置，因此会返回 None
print(stu.name)  # 输出: None

# 设置 stu 的 name 属性（实际上写入了内部 _name）
stu.name = 'lisi'

# 打印 stu 的 name 属性，此时属性已设置，因此会返回 'lisi'
print(stu.name)  # 输出: lisi

# age 属性同样被自动生成了
print('age 未设置时:', stu.age)   # 输出: None
stu.age = 25                     # 自动写入内部 _age
print('设置 age 后:', stu.age)   # 输出: 25


# =====================================================================
# 补充示例一：验证元类加工的效果 —— 检查类上的属性是 property 对象
# =====================================================================
print('\n===== 补充示例一：验证类属性已被自动加工成 property =====')
print('name 属性在类上的类型:', type(Student.name))   # <class 'property'>
print('age  属性在类上的类型:', type(Student.age))    # <class 'property'>
print('props 列表:', Student.props)                   # ['name', 'age']


# =====================================================================
# 补充示例二：同一个元类加工多个类（验证可复用性）
# 只需要声明 props，任何使用 Human 元类的类都会自动获得属性访问器
# =====================================================================
class Book(object, metaclass=Human):
    props = ['title', 'price']


book = Book()
print('\n===== 补充示例二：元类的可复用性（Book 类）=====')
book.title = 'Python 高级编程'
book.price = 88.5
print(f'书名: {book.title}, 价格: {book.price}')   # 自动生成的 property 生效
