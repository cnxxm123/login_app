"""
================================================================================
知识点：多线程基础 —— 进程与线程、线程的创建与启动（threading.Thread）
================================================================================

【核心概念】
1. 进程（Process）
   - 操作系统中正在运行的一个任务/程序实例；现代操作系统都支持"多进程并发"。
   - 每个进程拥有独立的 CPU 时间片、内存地址空间、文件句柄等资源，
     进程之间的数据默认是"隔离"的，互不干扰。

2. 线程（Thread）
   - 线程是进程内部的一条"执行流"，一个进程内可以同时并发运行多个线程。
   - 同一进程内的线程共享该进程的 CPU、内存等资源，因此线程之间可以直接
     读写同一份全局数据（这也是"线程安全"问题的根源，见第 4 个文件）。
   - 创建和销毁线程比创建和销毁进程廉价得多。

【工作原理】
   - 一个 .py 文件被运行时就是一个进程，入口默认只有一条"主线程"（MainThread）。
   - 通过 threading.Thread 创建"子线程"；调用 start() 后，子线程开始独立
     （并发）执行 target 指定的函数。
   - 子线程执行完会自动结束；线程对象一旦结束（或已 start）后不能再 start()，
     否则抛 RuntimeError。

【多线程在什么场景下提升效率？】
   - I/O 密集场景（网络请求、文件读写、数据库访问、等待用户输入）：
     线程大部分时间都在"等待"，CPU 空闲，多线程可以利用等待空档执行其他任务，
     显著提升整体吞吐量。
   - CPU 密集场景（纯计算）：由于 Python 有 GIL（全局解释器锁），同一时刻只有
     一条线程能执行 Python 字节码，多线程几乎无法提速。此时应改用"多进程"
     （见第 6、7 个文件）。

【start() / join() 的作用】
   - start()：启动线程（必须调用，否则线程不会运行）。
   - join()：等待该子线程结束；主线程调用 t.join() 后会阻塞，直到线程 t 跑完。
   - 若主线程先结束，非守护子线程仍会继续执行；但一般建议显式 join() 等待子线程
     完成后再收尾，保证输出完整、行为可控。

【注意事项与易错点】
   - 传参必须用 args=，且 args 接收"元组"：传一个参数要写 args=(100,)，
     逗号不能丢（(100) 只是 int 而不是元组）。
   - 线程的执行顺序由操作系统调度决定，是不确定的，不要假设"先 start 先执行完"。
   - 主线程与子线程是"并发"关系，不是调用关系；子线程报错不会自动影响主线程。
"""

from threading import Thread


def task(count: int):
    """子线程要执行的函数：依次打印 0 到 count-1。"""
    for n in range(count):
        print(n)


# 创建线程对象：target 传函数，args 传"元组"形式的参数
thread_1 = Thread(target=task, args=(100,))   # 注意 (100,) 的逗号：表示含 1 个元素的元组
thread_2 = Thread(target=task, args=(70,))

thread_1.start()   # 主线程执行到这一行时，子线程 1 被启动，开始独立运行
thread_2.start()   # 子线程 2 启动（线程对象一旦结束，后面不能再启动）

thread_1.join()    # 主线程在此阻塞等待子线程 1 结束，保证打印完整
thread_2.join()    # 主线程在此阻塞等待子线程 2 结束

print('Main thread end')


# ==============================================================================
# 补充示例 1：认识"主线程"与"子线程"，观察线程名与参数传递
# ==============================================================================
import threading


def show_thread_info(n: int, label: str):
    """打印当前运行这段代码的线程名称。"""
    # threading.current_thread() 返回当前正在执行的线程对象，.name 是其名称
    print(f'[{label}] 当前线程名 = {threading.current_thread().name}, 参数 n = {n}')


def demo_thread_info():
    # 主线程的名字固定是 "MainThread"
    print(f'主线程名 = {threading.current_thread().name}')
    # 创建两个子线程，分别传入不同参数（元组）
    a = Thread(target=show_thread_info, args=(1, '线程A'))
    b = Thread(target=show_thread_info, args=(2, '线程B'))
    a.start()
    b.start()
    a.join()
    b.join()


# ==============================================================================
# 补充示例 2：演示"I/O 密集"任务用多线程加速（对比串行与并发耗时）
# ==============================================================================
import time


def io_task(name: str):
    """模拟一次 I/O 等待（例如网络请求、读写文件），期间 CPU 基本空闲。"""
    time.sleep(0.5)   # 模拟 0.5 秒的等待
    print(f'{name} 完成一次 I/O 操作')


def demo_io_speedup():
    # 串行：4 次依次执行，每次等 0.5 秒 → 总耗时约 2 秒
    start = time.time()
    for i in range(4):
        io_task(f'串行{i}')
    print(f'串行耗时: {time.time() - start:.2f} 秒')

    # 并发：4 个线程同时等待 → 总耗时约 0.5 秒
    start = time.time()
    threads = [Thread(target=io_task, args=(f'并发{i}',)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f'多线程耗时: {time.time() - start:.2f} 秒')


if __name__ == '__main__':
    demo_thread_info()
    demo_io_speedup()
