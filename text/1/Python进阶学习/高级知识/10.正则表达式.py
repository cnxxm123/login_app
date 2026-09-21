"""
【正则表达式 Regular Expression —— Python 高级特性】

一、什么是正则表达式
    正则表达式（regex）是一种描述"字符串匹配模式"的语言，用一个"模式串"去
    文本里搜索、匹配、替换符合规则的内容。Python 通过 re 模块提供支持。

二、常用 API 的区别与使用场景
    1. re.search(pattern, string)  在【整个字符串中】搜索第一个匹配；
       不要求从开头匹配，找到就返回 Match 对象，找不到返回 None。
    2. re.match(pattern, string)   只从字符串的【开头】尝试匹配；
       开头不匹配就直接返回 None（即使后面有匹配）。
    3. re.fullmatch(pattern, string) 要求【整个字符串】完全匹配才返回 Match。
    4. re.findall(pattern, string)  找出【所有】匹配，返回列表（没分组时返回
       匹配到的子串列表；有分组时返回分组元组列表）。
    5. re.finditer(pattern, string) 找出所有匹配，返回迭代器，逐个产出 Match
       对象；数据量大时更省内存（和 findall 结果一样，只是惰性）。
    6. re.compile(pattern, flags)   先把模式"编译"成 Pattern 对象，之后反复
       使用该对象的 search/match/findall... 性能更好（重复使用同一模式时）。

三、常用元字符表
    \d   匹配任意数字（等价 [0-9]）
    \D   匹配任意非数字
    \w   匹配字母、数字、下划线（等价 [A-Za-z0-9_]）
    \W   匹配非单词字符
    \s   匹配空白字符（空格、\t、\n 等）
    \S   匹配非空白字符
    .    匹配除换行外的任意字符
    *    前面的字符出现 0 次或多次
    +    前面的字符出现 1 次或多次
    ?    前面的字符出现 0 次或 1 次
    {n}  前面的字符恰好出现 n 次
    {n,} 前面的字符至少出现 n 次
    {n,m}前面的字符出现 n~m 次
    []   字符集合，匹配其中任意一个字符，如 [a-z]、[0-9]
    ()   分组：既做"整体"，也用于提取内容（配合 group）
    |    或：匹配左边或右边，如 猫|狗
    ^    匹配开头（如 ^hello）
    $    匹配结尾（如 world$）
    说明：\d{*} 是【非法写法】——{*} 的 {} 里必须写数字（如 {2}、{2,3}），
    否则会报 re.error: nothing to repeat。

四、分组提取 group()
    Match 对象的 group(0) 返回整个匹配；group(1)、group(2)... 返回第 1、2 个
    分组捕获的内容。groups() 一次性返回所有分组组成的元组。

五、flags 常用项
    re.I / re.IGNORECASE  忽略大小写
    re.M / re.MULTILINE   让 ^ $ 匹配每一行的开头/结尾
    re.S / re.DOTALL      让 . 也能匹配换行符
    re.X / re.VERBOSE     允许模式里写空格和注释，便于阅读
"""

import re


def test_search():
    patter = r'\d{2}'  # 定义正则表达式：\d 代表任意数字，{2} 代表连续 2 个数字
    source = '小明今年204846岁'
    # search：在整个字符串中找第一个匹配（不要求开头）
    result = re.search(patter, source)  # 只验证到第一个匹配的然后就停止了
    print('search 结果:', result)          # 匹配到 '20'
    if result:
        print('search 匹配到的内容:', result.group())  # 输出: 20


def test_match():
    patter = r'\d{2}'  # \d 数字，{2} 连续 2 个数字
    source = '204846岁'
    result = re.match(patter, source)  # match：只验证开头是否匹配
    print('match 结果:', result)         # 开头就是数字，匹配到 '20'
    # 对比：如果 source 开头不是数字（如 '小明20岁'），match 会返回 None


def full_match():
    patter = r'\d{2}'  # 要求整个字符串恰好是 2 个数字
    source = '20'
    result = re.fullmatch(patter, source)  # fullmatch：严格验证整体
    print('fullmatch 结果:', result)         # '20' 完全匹配
    # 若 source 是 '204846'，fullmatch 会返回 None（因为不是"恰好 2 个数字"）


def test_find():
    # 原代码 `r'\d{*}'` 是非法正则：{} 里必须写数字次数，不能是 *。
    # 这里修正为 r'\d+'（\d 数字，+ 表示 1 个或多个），表示"匹配所有连续数字串"
    patter = r'\d+'  # 定义正则表达式：\d 代表数字，+ 代表出现 1 次或多次
    source = '小明今年204846岁'
    result = re.findall(patter, source)  # findall：找出所有匹配，返回列表
    print('findall 结果:', result)         # 输出: ['204846']


def test_iter():
    patter = r'\d{2}'  # 连续 2 个数字
    source = '小明今年204846岁'
    result = re.finditer(patter, source)  # finditer：返回惰性迭代器
    for i in result:   # 一边循环一边查找，功能上与 findall 一样，这个更省内存
        print('finditer 逐项:', i)         # 逐个输出 Match 对象


def test_complie():
    patter = r'\d{2}'    # 连续 2 个数字
    patter = re.compile(patter)  # compile：编译成 Pattern 对象，反复使用性能好
    print('compile 后 fullmatch(\'12\')：', patter.fullmatch('12'))    # 匹配 '12'
    print('compile 后 findall(\'64646\')：', patter.findall('64646'))  # 输出 ['64', '64']


test_search()
test_match()
full_match()
test_find()
test_iter()
test_complie()


# =====================================================================
# 补充示例一：分组提取（group / groups）—— 匹配并提取年月日
# =====================================================================
print('\n===== 补充示例一：分组提取 =====')
date_pattern = r'(\d{4})-(\d{2})-(\d{2})'   # 3 个分组：年-月-日
text = '今天是 2026-08-19，明天是 2026-08-20'
m = re.search(date_pattern, text)
print('group(0) 整个匹配:', m.group(0))     # 输出: 2026-08-19
print('group(1) 年:', m.group(1))            # 输出: 2026
print('group(2) 月:', m.group(2))            # 输出: 08
print('group(3) 日:', m.group(3))            # 输出: 19
print('groups() 所有分组:', m.groups())      # 输出: ('2026', '08', '19')


# =====================================================================
# 补充示例二：findall + 分组提取电话号码 / 邮箱
# =====================================================================
print('\n===== 补充示例二：findall + 分组提取电话/邮箱 =====')
info = '''
联系人1：张三，电话 138-1234-5678，邮箱 zhangsan@example.com
联系人2：李四，电话 139-9876-4321，邮箱 lisi@test.org
'''
# 匹配电话号码：3位-4位-4位，整体加括号变成一个分组
phone_pattern = r'(\d{3}-\d{4}-\d{4})'
phones = re.findall(phone_pattern, info)
print('提取到的电话号码:', phones)     # 输出: ['138-1234-5678', '139-9876-4321']

# 匹配邮箱：用户名@域名（用户名和域名都允许字母数字下划线点）
email_pattern = r'([\w.]+@[\w.]+\.\w+)'
emails = re.findall(email_pattern, info)
print('提取到的邮箱:', emails)         # 输出: ['zhangsan@example.com', 'lisi@test.org']

# 演示 flags：忽略大小写匹配（普通写法大小写敏感，加 re.I 后不区分）
words = 'Hello HELLO hello'
print('大小写敏感匹配 hello:', re.findall(r'hello', words))              # ['hello']
print('忽略大小写匹配 hello:', re.findall(r'hello', words, re.IGNORECASE))  # ['Hello','HELLO','hello']
