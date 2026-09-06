"""
================================================================================
知识点：进程池 —— ProcessPoolExecutor
================================================================================

【核心概念】
1. 为什么要用进程池？
   - 启动一个进程比启动一个线程昂贵得多，频繁创建/销毁进程对系统性能影响更大。
   - 进程池：预先创建一批进程复用，任务提交给池子，空闲进程执行完后再回池等待，
     避免反复创建销毁进程的开销，也避免进程数量失控耗尽系统资源。

2. 结合 if __name__ == '__main__' 保护
   - Windows 上创建子进程采用 spawn 方式（子进程会重新导入脚本文件）。
   - 若进程池写在模块顶层，子进程导入时又会执行创建进程池的代码，导致无限递归。
   - 因此必须把进程池相关代码放在 if __name__ == '__main__': 保护块内（跨平台安全）。

3. submit / map / result
   - submit(func, *args)：提交单个任务，返回 Future 对象。
   - future.result()：阻塞等待任务完成并获取返回值。
   - map(func, iterable)：批量提交同一函数处理多个参数，返回结果迭代器。
   - 用法与线程池（ThreadPoolExecutor）几乎一致，只是底层用的是"进程"。

4. 多进程 vs 多线程怎么选？
   - CPU 密集型（大量计算）：用多进程（绕过 GIL，真正并行利用多核）。
   - I/O 密集型（网络/文件/等待）：用多线程（开销小，等待空档切换线程即可）。
   - 资源参考：设备剩余资源较多时可用多进程；资源紧张时用多线程更稳妥。

【注意事项与易错点】
   - 传给进程池的函数（包括参数）必须能被 pickle 序列化：
     不能是 lambda、闭包或嵌套在函数内部的函数，必须定义在模块顶层。
   - 子进程打印输出顺序不可控。
   - 任务抛出的异常要等调用 result() 时才暴露。
   - 进程数（max_workers）默认由 CPU 核心数决定，不要盲目开太多。
"""

from concurrent.futures import ProcessPoolExecutor
import time


def task(name: str):
    print(f'{name} - set1\n', end='')
    time.sleep(1)          # 模拟耗时操作
    print(f'{name} - set2\n', end='')
    return f'{name} - 完成'   # 不一定要有返回值；有返回值时用 result() 获取


def heavy_calc(x: int) -> int:
    """一个 CPU 计算任务：必须定义在模块顶层，才能被 spawn 子进程导入并序列化。"""
    total = 0
    for i in range(x):
        total += i * i
    return total


if __name__ == '__main__':
    with ProcessPoolExecutor() as executr:  # 进程池支持上下文管理器；退出时等待所有任务完成
        # submit：提交单个任务，返回 Future 对象
        result_1 = executr.submit(task, 'a')   # 启动一条进程执行任务
        result_2 = executr.submit(task, 'b')

        print(result_1.result())   # result() 阻塞等待任务完成并返回结果
        print(result_2.result())

    with ProcessPoolExecutor() as executr:  # 进程池支持上下文管理器
        # map：同一函数处理多个参数，返回结果迭代器
        result = executr.map(task, ['c', 'b'])
        for i in result:
            print(i)

    # ==========================================================================
    # 补充示例：指定 max_workers + 批量提交 CPU 计算任务
    # ==========================================================================
    with ProcessPoolExecutor(max_workers=4) as pool:   # 明确进程池最多 4 个进程
        futures = [pool.submit(heavy_calc, 2_000_000) for _ in range(6)]
        for f in futures:
            print(f'计算结果 = {f.result()}\n', end='')
