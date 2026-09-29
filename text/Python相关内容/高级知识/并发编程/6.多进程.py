"""
================================================================================
知识点：多进程 —— multiprocessing.Process
================================================================================

【核心概念】
1. 为什么需要多进程？
   - Python 的 GIL（全局解释器锁）使得同一进程内同一时刻只有一条线程执行
     Python 字节码，因此"多线程"对 CPU 密集型（纯计算）任务几乎无法提速。
   - "多进程"的每个进程都有自己独立的解释器和 GIL，可真正利用多核 CPU 并行计算，
     所以 CPU 密集型任务应使用多进程。

2. 进程拥有独立的内存
   - 每个进程都有自己独立的内存地址空间，进程之间的数据默认不共享。
   - 子进程是主进程的"副本"，各自修改全局变量互不影响（见补充示例 1）。
   - 如需跨进程共享数据，要使用 multiprocessing 提供的 Queue / Pipe / Value /
     Array 等专门工具，普通全局变量是做不到的。

3. 为什么必须写在 if __name__ == '__main__': 里？
   - Windows 上创建子进程采用 spawn 方式：子进程会"重新导入"当前脚本文件。
   - 若创建进程的代码写在模块顶层，子进程重新导入时会再次执行创建进程的代码，
     造成无限递归创建进程，直接报错/崩溃。
   - 因此 multiprocessing 相关代码必须放在 if __name__ == '__main__': 保护块内
     （Linux/macOS 默认 fork 方式通常没问题，但为了跨平台必须加上）。

4. join() 的作用
   - process.join()：主进程阻塞等待该子进程结束。
   - 多个子进程时，先全部 start() 再统一 join()，让它们真正并行执行。

【注意事项与易错点】
   - Process(target=..., args=(...)) 的参数同样用元组传递。
   - 子进程打印输出顺序不可控（多进程并行打印）。
   - 启动进程比启动线程昂贵得多，进程数量别开太多，否则耗尽系统资源
     （数量多时建议用进程池控制，见第 7 个文件）。
"""

import time
import threading
from multiprocessing import Process


def task(name: str, count: int):
    print(f'{name} - start\n', end='')
    result = 0
    for i in range(count):          # 一段简单的 CPU 计算
        result += (i + 1)
    time.sleep(1)                   # 模拟其他耗时操作
    print(f'{name} - end -with {result}')


def start_process_1():
    # 创建单个进程对象：target 传函数，args 传参数元组
    process = Process(target=task, args=('a', 100))
    process.start()  # 启动子进程（多进程一定要在 if __name__ == '__main__': 内启动）
    process.join()   # 主进程等待该子进程结束


def start_process_2():
    arg_list = [('s', 100), ('q', 99)]
    # 使用列表推导式生成包含多个进程对象的列表
    processes = [Process(target=task, args=(name, count)) for name, count in arg_list]
    for i in processes:
        i.start()        # 先全部启动（并行执行）
    for j in processes:
        j.join()         # 再逐个等待结束


# ==============================================================================
# 补充示例 1：演示"进程间不共享普通全局变量"（子进程各自持有一份副本）
# ==============================================================================
shared_value = 0        # 普通全局变量


def change_value():
    global shared_value
    shared_value = 100
    print(f'子进程把 shared_value 改成了 {shared_value}\n', end='')


def demo_not_shared():
    global shared_value
    shared_value = 0
    p = Process(target=change_value)
    p.start()
    p.join()
    # 子进程修改的是它自己的副本，主进程里的 shared_value 不受影响
    print(f'主进程里 shared_value 仍然是 {shared_value}（未被子进程修改）')


# ==============================================================================
# 补充示例 2：CPU 密集任务 —— 多进程并行比多线程更快（绕过 GIL）
# ==============================================================================
def cpu_task(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def demo_cpu_intensive():
    n = 10_000_000   # 计算量较大的数
    # 用 4 个线程并行（受 GIL 限制，几乎无法真正并行）
    start = time.time()
    threads = [threading.Thread(target=cpu_task, args=(n,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f'4 个线程（受 GIL 限制）耗时: {time.time() - start:.2f} 秒')

    # 用 4 个进程并行（各自独立解释器，真正利用多核）
    start = time.time()
    processes = [Process(target=cpu_task, args=(n,)) for _ in range(4)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    print(f'4 个进程（真正并行）耗时: {time.time() - start:.2f} 秒')


if __name__ == '__main__':
    start_process_1()
    start_process_2()
    demo_not_shared()
    demo_cpu_intensive()
