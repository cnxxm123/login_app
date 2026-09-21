"""
知识点：删除 property（@xxx.deleter）
=======================================

【核心概念】
- 一个 property 除了有 getter（@property）和 setter（@xxx.setter），
  还可以有 deleter（@xxx.deleter），用来定义"删除"这个属性时执行什么逻辑。
- 语法：@area.deleter 修饰的方法名必须和 property 名相同（都叫 area）。
  外部执行 del obj.area 时，会自动调用这个 deleter 方法。

【工作原理】
- del sq.area
  -> 找到 area 这个 property 的 deleter
  -> 执行 deleter 方法体（例如 del self.__area，把缓存删掉）。

【本示例的设计意图：删除"缓存"】
- 在这个类里，area 是一个"只读 + 缓存"的 property：
  - getter：如果 self.__area 还没有值（None）就计算并缓存；有值就直接返回缓存。
  - deleter：del sq.area 时把缓存 self.__area 删掉。
- 关键点：删掉缓存后，下次再访问 sq.area 时，
  因为缓存不在了（等价于"没缓存"），getter 会【重新计算】并重新缓存。
  所以 print(sq.area) 不会再报错，而是输出重新计算出来的面积。

【注意事项 / 易错点】
1. deleter 的方法名必须与 property 名一致，并且用 @area.deleter 来绑定。
2. 删除的是"缓存属性"（self.__area），而不是删除这个 property 本身；
   如果真想删除整个 property，需要用 delattr(类, 'area') 从类上删除。
3. getter 读取缓存时要注意：缓存可能还没创建（None），
   也可能被 deleter 删掉（属性不存在）。直接写 self.__area is None 时，
   如果属性已被删除会抛 AttributeError，所以要用 try/except 或 getattr 兜底。
4. 常见用途：清理/失效缓存、释放资源（如关闭文件句柄、连接），
   让下次访问时重新初始化。
"""


class Square:
    def __init__(self, width):
        self.__width = width      # 内部真实数据
        self.__area = None        # 面积缓存，None 表示还没计算过

    @property
    def width(self):
        # width 的 getter：读取宽度。
        return self.__width

    @width.setter
    def width(self, width):
        # width 的 setter：赋值时直接存到内部变量。
        self.__width = width

    @property
    def area(self):
        # area 的 getter：计算并缓存面积。
        # 读取缓存：缓存可能还没算过（None），也可能被 del sq.area 删掉了（属性不存在）。
        # 所以不能直接写 self.__area is None（属性被删时那样会抛 AttributeError），
        # 而是用 try/except 把"属性不存在"也当作"没有缓存"处理。
        try:
            cached = self.__area          # 尝试读取缓存
        except AttributeError:
            cached = None                 # 缓存已被 del 删除 -> 视为没有缓存
        if cached is None:
            # 把 self.__area 缓存下来，就不用每次调用都计算一遍。
            # 缓存为空（第一次访问，或缓存被删除后再次访问）时重新计算。
            self.__area = self.__width * self.__width
            cached = self.__area
        return cached

    @area.deleter  # 删除 property：用 @area.deleter 修饰
    def area(self):
        # del sq.area 时会自动调用这个方法。
        # 这里把缓存的面积 self.__area 删掉，
        # 下次再访问 sq.area 时因为缓存不在了，就会重新计算。
        del self.__area


sq = Square(4)
print(sq.width)    # 输出 4
print(sq.area)     # 输出 16（第一次访问，计算并缓存）

# 使用 del 触发 area 的 deleter，把缓存的面积删掉。
del sq.area        # 把area给删除了（这里删除的是"缓存的面积"，不是整个属性）

# 删掉缓存后再访问 sq.area：因为缓存不在了，getter 会重新计算并重新缓存，
# 所以这行【不会报错】，而是输出重新算出来的 16。
print(sq.area)     # 输出 16（缓存被删了，于是重新计算）
print(sq.area)     # 输出 16（这次直接命中重新生成的缓存）
print('----------------------------------------')

# ---- 补充：验证 deleter 之后确实发生了"重新计算" ----
# 改一下宽度，让重新计算的面积不同，更容易看出效果。
sq.width = 5       # 通过 setter 修改宽度（注意：这里没有清空面积缓存）
del sq.area        # 手动删除缓存
print(sq.area)     # 输出 25（缓存被删，重新按 width=5 计算）
print('----------------------------------------')

# ---- 补充：直接删除整个 property（了解即可，一般用不到） ----
# delattr(Square, 'area')   # 这会从"类"上删除 area 这个 property 定义
# print(sq.area)            # 之后对象上就没有 area 了，会报 AttributeError
