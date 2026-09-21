"""
知识点：只读 property（最佳实践）
====================================

【核心概念】
- "只读属性"：一个 property 如果【只写了 @property，没有写 @xxx.setter】，
  那么它就只能被"读取"，不能被赋值。
  一旦尝试赋值，Python 会抛 AttributeError: can't set attribute。
- 典型用途：把"由内部数据计算出来的结果"暴露成属性，例如正方形的面积
  area = width * width，它不应该由用户随便赋值，只能通过 width 间接改变。
- 缓存（cache）：如果这个"计算"比较昂贵（复杂、耗时），
  可以用一个内部变量（如 self.__area）把结果存起来，下次访问直接返回缓存，
  不用每次重新计算。当内部数据（width）变化时，再把缓存清空（设为 None）。

【工作原理】
- 构造对象时：self.width = width 会触发 setter，
  setter 校验后写入 self.__width，并把缓存 self.__area 重置为 None。
- 访问面积时：s.area 调用 area 的 getter，
  若 self.__area 是 None（还没算过/被清空）就重新计算并缓存，否则直接返回缓存。

【为什么内部要用 self.__width（而不是 self.width）？—— 重点坑】
- 在 setter 里如果写 self.width = width：
  -> 这又是一次"给 width 赋值"，会【再次】调用 setter
  -> setter 里再写 self.width = width -> 再触发 setter -> 无限递归 -> RecursionError。
- 所以必须把真实数据存到另一个名字 self.__width，
  getter 读 self.__width、setter 写 self.__width，避免与自己同名造成无限递归。
- 同理，getter 里也不能写 return self.width（会再次触发 getter 无限递归）。

【使用场景】
- 计算型属性：面积、周长、BMI、折扣价等由其它属性推导出来的值。
- 不希望用户直接改动的派生数据，只能通过修改"源头数据"来间接改变。
- 对昂贵计算做"懒加载 + 缓存"，提升性能。

【注意事项 / 易错点】
1. 只写 @property 不写 @xxx.setter -> 只读；写了 setter -> 可写（可用 @x.setter 不写校验）。
2. setter 内部写 self.width 会无限递归，必须写 self.__width。
3. 校验失败要 raise ValueError('...')，不能直接 raise 字符串（非法语法）。
4. 修改 width 后要记得清空缓存（self.__area = None），否则面积还是旧值。
5. 缓存是存在"实例"上的（self.__area），不同实例各自独立。
"""


class Square:
    def __init__(self, width):
        # 这里直接调用 width 的 setter，并不是普通的属性赋值：
        # 会先校验宽度 >= 0，再把数据存到 self.__width。
        self.width = width
        # 面积缓存：None 表示"还没计算过"。
        # 首次访问 s.area 时才真正计算，并把这个值缓存下来。
        self.__area = None

    @property
    def width(self):
        # width 的 getter：读取宽度。
        # 必须返回 self.__width（内部真实数据），不能 return self.width（会无限递归）。
        return self.__width

    @width.setter
    def width(self, width):
        # width 的 setter：赋值时先校验。
        if width < 0:
            # 校验不通过就抛异常（这是合法写法）。
            # 注意：不能写 raise 'width不能小于0'（那样是非法语法）。
            raise ValueError('width不能小于0')
        # 这里一定要用 self.__width，如果使用 self.width 会一直调用 width 方法
        # （无限递归 -> RecursionError）。
        self.__width = width
        # 在改变 self.__width 后将 self.__area 重新设置为 None：
        # 因为宽度变了，之前缓存的面积已经失效，必须"清空缓存"，
        # 这样下次访问 s.area 才会重新计算。
        self.__area = None

    @property
    def area(self):
        # 这样就把 area 设置为了只读，无法使用 self.area = xxx 进行赋值，
        # 因为没有设置 @area.setter 装饰器。
        # 尝试 s.area = 100 会抛 AttributeError: can't set attribute。
        if self.__area is None:
            # 把 self.__area 缓存下来，就不用每次调用都计算一遍。
            # 首次访问（或宽度改变后缓存被清空）时，才真正做乘法计算。
            self.__area = self.__width * self.__width
        return self.__area


s = Square(10)      # 构造：setter 校验 10 >= 0 通过，存到 __width，缓存为 None
print(s.width)      # 输出 10（getter）
print(s.area)       # 输出 100（首次访问，计算并缓存）
print('----------------------------------------')

# ---- 补充 1：验证缓存 —— 修改 width 后 area 会重新计算 ----
s.width = 20        # 触发 setter：校验通过，__width 变为 20，且清空面积缓存
print(s.width)      # 输出 20
print(s.area)       # 输出 400（缓存已被清空，所以重新计算）
print(s.area)       # 输出 400（这次直接命中缓存，没有重新计算）
print('----------------------------------------')

# ---- 补充 2：只读属性无法赋值 ----
try:
    s.area = 999    # area 没有 setter，是只读的，赋值会报错
except AttributeError as e:
    print('给只读 area 赋值被拒绝:', e)
print('----------------------------------------')

# ---- 补充 3：构造时传入负数会触发 setter 校验 ----
try:
    bad = Square(-5)
except ValueError as e:
    print('构造传入负数被拦截:', e)   # 输出：构造传入负数被拦截: width不能小于0
