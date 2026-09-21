"""
【变量作用域与 UnboundLocalError —— Python 高级特性】

一、核心知识点：Python 是"先编译，后执行"的语言
    当 Python 编译一个函数时，它会【扫描整个函数体】，只要发现某个名字在函数
    内部【任意位置】被赋值（包括 if/for/while 等分支里），就会把这个名字标记为
    "该函数的局部变量"。这个判定发生在【编译阶段】，与实际运行时那一行代码
    到底有没有执行【无关】。

    所以：
        count = 10
        def f(flag):
            if flag:
                count = 20   # count 在函数内被赋值 -> 编译时认定 count 是局部变量
            print(count)     # 当 flag=False 时，if 里的赋值没执行，
                             # count 这个"局部变量"从未初始化，读取它 -> UnboundLocalError
    报错信息：UnboundLocalError: local variable 'count' referenced before assignment
    （局部变量 count 在赋值之前被引用）

二、global 的用法与作用
    想让函数内的赋值去修改【模块级全局变量】，必须先在函数内用 global 声明：
        def f():
            global count     # 声明：count 是全局变量，不是局部变量
            count = 20       # 此时修改的是模块顶层的 count
    注意：
    - global 声明必须写在函数体内、对该名字的【任何使用之前】。
    - 声明之后，函数里所有对这个名字的读和写都指向全局的那一份。
    - 只读（不赋值）全局变量不需要 global，LEGB 会自动找到全局。

三、局部变量遮蔽（Shadowing）全局变量
    如果函数内对某个名字赋值但没有 global 声明，那么这个名字就是【局部变量】，
    它会"遮蔽"同名全局变量：函数内访问到的永远是局部的那一份，全局变量不受影响。
    这既是"隔离"的好处（不污染全局），也是"坑"（忘记 global 时修改无效）。

四、修复 task(False) 报错的两种常用方式
    方式一：在函数里加 `global count`，明确告诉 Python count 是全局变量，
            这样就不存在"未初始化的局部变量"问题了。
    方式二：改判断逻辑，让 count 的赋值不依赖某个可能不执行的分支
            （例如先把 count 赋好初值，再在 if 里做覆盖）。
"""

# =====================================================================
# 全局变量定义（模块级 / Global 层）
# =====================================================================
count = 10
print('初始全局 count =', count)
a = 1


# =====================================================================
# 示例一：原版 task 函数 —— 理解"为什么 task(False) 会报 UnboundLocalError"
# =====================================================================
def task(flag: bool):
    global a      # 使用全局的 a：不加这行，a = 10 会把 a 变成局部变量
    a = 10        # 因为声明了 global，这里修改的就是模块顶层的全局 a
    if flag:
        count = 20  # count 在函数内被赋值，编译阶段就认定 count 是"局部变量"
    print(count)    # 局部范围（函数内）优先找 count，找不到不会去全局找
    print(a)


print('\n===== 示例一：原版 task 函数 =====')
task(True)      # flag=True 时 if 分支执行，count=20 被初始化，输出 20 和 10
print('task(True) 后全局 count =', count)   # 全局 count 仍为 10（函数内的 count 是局部变量）
print('task(True) 后全局 a =', a)           # 全局 a 已被改成 10

# task(False) 原本会报错，原因：
# Python 先编译后执行：编译 task 函数时已发现函数体内有 count = 20 这个赋值，
# 所以把 count 认定为"函数的局部变量"；但编译时并不知道 if 那一行要不要执行。
# 当 flag=False 时，if 分支不执行，局部变量 count 从未被初始化，
# 而 print(count) 又优先在局部范围查找 -> UnboundLocalError。
# 下面把它放在 try/except 里演示，程序可以继续运行而不崩溃：
try:
    task(False)   # 此行原样执行会抛 UnboundLocalError
except UnboundLocalError as e:
    print('\ntask(False) 抛出了 UnboundLocalError ->', e)


# =====================================================================
# 示例二（修复方式一）：加 global count，让 task(False) 不报错
# =====================================================================
def task_global(flag: bool):
    global a, count   # 同时声明 a 和 count 都是全局变量（不是局部变量）
    a = 10
    if flag:
        count = 20    # 修改的是全局 count
    print(count)      # 因为声明了 global，这里读的也是全局 count -> 不会报错
    print(a)


print('\n===== 示例二（修复方式一）：用 global count =====')
task_global(False)   # 不再报错，输出全局 count=10 和 a=10
print('task_global(False) 后全局 count =', count)   # 仍为 10


# =====================================================================
# 示例三（修复方式二）：改判断逻辑，让 count 一定有初值
# =====================================================================
def task_safe(flag: bool):
    local_count = count   # 先把全局值读进"确定已初始化"的局部变量
    if flag:
        local_count = 20  # 在已初始化的局部变量上做覆盖
    print(local_count)    # 无论 flag 真假，local_count 都有值 -> 不会报错
    print(a)


print('\n===== 示例三（修复方式二）：先初始化再分支赋值 =====')
task_safe(False)   # 输出: 10（读的是全局 count 的值）
task_safe(True)    # 输出: 20
print('两种修复方式后全局 count 仍 =', count)   # 全局 count 一直没被破坏


# =====================================================================
# 补充示例：局部变量遮蔽（Shadowing）全局变量
# =====================================================================
name = '全局 name'      # 全局变量 name


def shadow():
    name = '局部 name'  # 没有 global 声明，这里创建的是"局部变量" name
    print('函数内访问 name:', name)   # 局部遮蔽了全局 -> '局部 name'


def read_global():
    print('函数内只读 name（无赋值，不需要 global）:', name)   # LEGB 找到全局


print('\n===== 补充示例：局部变量遮蔽全局变量 =====')
shadow()
read_global()
print('函数外访问 name:', name)   # 全局变量未被函数内修改，仍为 '全局 name'
