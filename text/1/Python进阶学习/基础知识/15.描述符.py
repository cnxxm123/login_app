"""
============================================
描述符（Descriptor）
============================================

一、核心概念
    描述符是一种"可复用的属性访问控制"机制。
    通过实现 __get__、__set__、__delete__ 等协议方法，描述符对象在被赋值给
    类属性后，可以拦截对该属性的"读取 / 设置 / 删除"操作，
    从而在访问属性时执行自定义逻辑（校验、转换、缓存、通知等）。

二、描述符协议（Descriptor Protocol）
    1. __get__(self, instance, owner)
       - 在"访问属性"时被调用。
       - instance：访问属性的实例对象（通过类访问时为 None）；
         owner：拥有该描述符的类。
    2. __set__(self, instance, value)
       - 在"给属性赋值"时被调用。
       - instance：实例对象；value：要赋的值。
    3. __delete__(self, instance)
       - 在"del 属性"时被调用。
    4. __set_name__(self, owner, name)   （Python 3.6+ 引入）
       - 在描述符被赋值给类属性时自动调用，用于获取该属性的名字。
       - owner：拥有该描述符的类；name：描述符被赋值的属性名。

三、描述符与 property 的关系
    1. property 本质上就是一个内置的、基于描述符实现的便捷工具。
       相同点：两者都能控制属性的访问、设置和删除，都能在属性访问时执行自定义逻辑，
       都能用来封装数据、隐藏内部实现细节。
       不同点：
       - property 语法简洁，适合"单个类"内的简单属性管理。
       - 描述符更通用、更灵活，适合"在多个类中复用"同样的属性管理逻辑，
         也适合实现缓存、通知等更高级的功能。
       - 描述符需要单独定义类并实现协议方法，逻辑相对复杂，会有轻微性能开销
         （实际应用中通常可忽略）。

四、数据描述符与属性查找优先级
    1. 同时实现了 __get__ 和 __set__ 的描述符称为"数据描述符"。
    2. 数据描述符的优先级高于实例字典（instance.__dict__）中的同名属性：
       即使实例的 __dict__ 里存在同名键，访问属性时也会先走描述符的 __get__。
    3. 只实现了 __get__ 的描述符称为"非数据描述符"，
       它的优先级低于实例字典中的属性。

五、注意事项与易错点
    1. 本示例中把值存到 instance.__dict__ 里，而不是 self（描述符对象）上：
       因为描述符对象被该类的所有实例共享，若存到 self 上会导致多个实例互相干扰。
    2. 抛异常必须用 raise TypeError('...') 或 raise ValueError('...') 这种写法，
       原示例中的 raise f'...'（直接 raise 一个字符串）是非法语法，会报 SyntaxError。
    3. 触发 __set_name__ 需要把描述符对象"赋值给类属性"
       （如 Student.first_name = RequiredString(True)），
       而不是在 __init__ 里给实例赋值。
"""


class RequiredString:  # 描述符类：至少要实现 __set_name__、__set__、__get__ 等协议方法
    def __init__(self, trim=True):
        # trim 参数：赋值时是否去除字符串两端的空白
        self.__trim = trim

    def __set_name__(self, owner, name):
        # Python 3.6 引入的协议方法，在描述符被赋值给类属性时自动调用，
        # 用于自动获取该属性的名称。
        # owner：拥有该描述符的类（这里是 Student）；
        # name：描述符被赋值的属性名（这里是 first_name 或 last_name）。
        self.__property = name

    def __set__(self, instance, value):
        # 在给属性赋值时被调用（实现了 __set__，属于"数据描述符"）
        if not isinstance(value, str):
            # 修复：必须用 raise 异常类型（如 TypeError），不能直接 raise 字符串
            raise TypeError(f'{self.__property} is not string')

        if self.__trim:  # 判断是否需要去除字符串两边的空白
            value = value.strip()

        if len(value) == 0:  # 判断去除空白后字符串是否为空
            # 修复：非法语法 raise f'...' -> 改为 raise ValueError('...')
            raise ValueError(f'{self.__property} is empty')

        # 把值保存到实例自己的字典 __dict__ 中。
        # 注意不能保存到 self 上，因为描述符对象被所有实例共享
        instance.__dict__[self.__property] = value

    def __get__(self, instance, owner):
        # 在访问属性时被调用。
        # （注意：如果通过类直接访问如 Student.first_name，instance 会是 None，
        #  这里为了保持示例简单直接访问 instance.__dict__，实际生产代码应加判空处理）
        if self.__property in instance.__dict__:
            # 如果属性已经存在于实例的字典中，返回该值
            return instance.__dict__[self.__property]
        return None  # 否则返回 None（表示尚未赋值）


class Student:
    # 把描述符对象赋值给类属性，此时会触发 __set_name__，记录属性名
    first_name = RequiredString(True)  # 要求非空字符串，且去除首尾空白
    last_name = RequiredString(True)


stu = Student()  # 创建对象，此时 first_name 和 last_name 都还没有值
stu.first_name = '   dad  '  # 赋值时自动调用描述符的 __set__：类型校验 + 去空白 + 非空校验
print(stu.first_name)  # 访问时自动调用描述符的 __get__，返回 'dad'


# ==================== 补充示例 1：数据描述符优先级高于实例属性 ====================

class ReadOnly:
    """数据描述符：实现 __get__ 和 __set__，优先级高于实例字典属性"""

    def __init__(self, value):
        self.value = value

    def __get__(self, instance, owner):
        # 无论实例字典里放什么，这里都返回固定值
        return self.value

    def __set__(self, instance, value):
        # 禁止赋值，体现只读
        raise AttributeError('该属性是只读的')


class Point:
    x = ReadOnly(10)  # 把描述符赋值给类属性 x


p = Point()
print(p.x)  # 10（走描述符 __get__）

# 数据描述符优先级高于实例属性：即使强行往实例字典里塞同名键，
# 访问 p.x 时依然会先走描述符的 __get__，返回固定值 10
p.__dict__['x'] = 999
print(p.x)  # 仍然是 10（数据描述符优先于实例属性）

try:
    p.x = 100  # 走描述符 __set__，抛 AttributeError
except AttributeError as e:
    print(f'赋值被拦截：{e}')
