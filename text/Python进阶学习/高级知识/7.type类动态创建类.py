"""
【type 类动态创建类 —— Python 高级特性】

一、核心概念
    在 Python 中，"类"本身也是一个对象，而这个对象的类型就是 type。
    我们平时写 `class People: ...` 只是创建类的语法糖，底层其实等价于：
        People = type('People', (object,), {...命名空间字典...})
    也就是说，type 的【三参形式】可以直接动态地创建类：
        type(类名, 父类元组, 类体命名空间字典)

二、type(name, bases, dict) 三个参数的含义
    1. name : 类名（字符串），如 'Student'
    2. bases: 父类组成的元组，如 (People,)；只有一个父类时也要写成 (People,)
    3. dict : 类的命名空间字典，存放类的方法和属性（键是名字，值是对象）

三、exec 的作用
    exec(代码字符串, 全局命名空间, 局部命名空间) 可以把一段字符串形式的 Python
    代码"执行"到指定的命名空间字典里。这样我们就能把类体代码写成字符串，
    再通过 exec 填充到 class_dict 中，配合 type 三参形式实现"动态生成类"。

四、动态创建类的适用场景
    - 根据配置文件/数据库表结构动态生成类（ORM 框架，如 SQLAlchemy）
    - 工厂模式：运行时根据需求批量生成结构相似的类
    - 插件系统、代码生成工具
    - 教学/元编程实验

五、与 metaclass（元类）的联系
    type 是"最顶层的元类"，所有类（包括 metaclass）都是 type 的实例。
    class 语句的本质是调用元类的 __new__/__init__ 来创建类对象。
    动态创建类的 type() 三参调用，和 metaclass 机制是同一件事的两种写法：
        - type('A', (object,), {...})           是直接"手动创建类"
        - class A(metaclass=MyMeta): ...        是"让元类帮你创建类"
    掌握 type 三参形式，是理解元类的第一步。

六、易错点
    1. 单父类元组别漏逗号：(People) 是类本身，(People,) 才是元组。
    2. exec 的命名空间要正确：方法里用到全局名（如 print）需要 globals()。
    3. 动态创建出的类名要和变量名区分开（类名是字符串）。
"""


# =====================================================================
# 示例：先定义父类 People，再用 exec + type 动态创建 Student
# =====================================================================

# 定义父类的方法
class People:
    a = 1                    # 父类属性 a，子类可以继承
    def speak(self):         # 父类方法 speak
        print('我是 People 的 speak 方法')


# 类体代码以字符串形式存在，这才是"动态"的关键：代码可以从文件/网络/配置读进来
class_body = '''
def __init__(self):
    self.name = 'liu'

def hello(self):
    print('hello')
'''

# 准备一个空的命名空间字典，用来承接 exec 执行后产生的类方法
class_dict = {}

# 用 exec 把字符串代码执行到 class_dict 中
# 第一个参数 globals() 提供内置函数等全局名字（如 print、def 关键字不需要）
exec(class_body, globals(), class_dict)   # 执行后 class_dict 里就有了 __init__ 和 hello

# 动态创建类：类名 'Student'，父类 (People,)，类体命名空间 class_dict
Student = type('Student', (People,), class_dict)

sty = Student()          # 实例化动态创建的类
print(sty.name)          # 调用动态生成的 __init__，输出: liu
print(sty.a)             # 继承自父类 People 的属性，输出: 1

sty.hello()              # 调用动态生成的 hello 方法，输出: hello
sty.speak()              # 调用继承来的父类方法 speak


# =====================================================================
# 补充示例一：type 三参形式直接动态创建类（不借助字符串）
# 用普通函数直接作为类的方法
# =====================================================================
def __init__(self, x, y):
    """Point 的初始化方法：把 x, y 存到实例上"""
    self.x = x
    self.y = y


def distance(self, other):
    """计算两点之间（欧几里得）距离的方法"""
    return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


# type(类名, 父类元组, {方法名: 函数对象})
Point = type('Point', (object,), {'__init__': __init__, 'distance': distance})

p1 = Point(0, 0)
p2 = Point(3, 4)
print('p1 到 p2 的距离:', p1.distance(p2))    # 输出: 5.0
print('Point 的父类:', Point.__bases__)       # 输出: (<class 'object'>,)


# =====================================================================
# 补充示例二：动态批量生成多个结构相似的类（工厂场景）
# 元类里"类创建时统一加工"的做法，在 type 三参形式中同样可以实现
# =====================================================================
def make_class(cls_name, base, attrs: dict):
    """工厂函数：动态创建一个带 name 属性和 greet 方法的类"""
    def greet(self):                      # 给每个动态类统一生成 greet 方法
        print(f'你好，我是 {self.name}')
    attrs['name'] = cls_name              # 类属性 name
    attrs['greet'] = greet                # 把方法放进命名空间
    return type(cls_name, (base,), attrs)  # 用 type 三参形式创建类


# 批量创建三个类（相当于三个"模板"）
Dog = make_class('Dog', object, {})
Cat = make_class('Cat', object, {})
Bird = make_class('Bird', object, {})

d = Dog()
print('Dog 类名:', d.name)
d.greet()                      # 输出: 你好，我是 Dog
print('Cat 类名:', Cat().name)
