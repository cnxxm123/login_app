"""
================================================================================
知识点：线程池 —— ThreadPoolExecutor
================================================================================

【核心概念】
1. 为什么要用线程池？
   - 线程的创建和销毁相对比较昂贵，频繁地创建/销毁线程不利于高性能。
   - 线程池：预先创建一批线程放在池中复用。有任务时从池中取空闲线程执行，
     执行完线程回到池中继续等待下一个任务，避免反复创建销毁的开销。
   - 可以理解为"线程一直循环等任务：没有任务就停在那里，有任务就继续执行"。

2. Future 对象
   - submit() 返回一个 Future 对象，代表"一个未来才完成的任务"。
   - future.result() 会阻塞当前线程，直到该任务执行完成并返回其结果。
   - 注意：submit() 只是"提交任务"，任务可能还没执行完，必须用 result() 获取结果。

3. max_workers 参数
   - ThreadPoolExecutor(max_workers=N) 指定池中最多 N 条线程。
   - 不传时，默认值由 CPU 决定（Python 3.8+ 默认 min(32, os.cpu_count()+4)），
     比较适合 I/O 密集任务；可按需手动调整。

4. with 语句（上下文管理器）的语义
   - 退出 with 时会自动调用 shutdown(wait=True)：
     * 不再接收新任务；
     * 阻塞等待池中所有已提交任务执行完成后才退出。
   - 所以在 with 块结束后，所有任务一定已经执行完，非常省心。

【submit 与 map 的区别】
   - submit(func, *args)：提交"一个"任务，可传任意参数，返回 Future。
   - map(func, iterable)：用同一函数处理可迭代对象中的每个元素（批量提交），
     返回按传入顺序产出结果的迭代器。

【注意事项与易错点】
   - result() 不传超时可能无限阻塞，可传 result(timeout=N)。
   - 任务内抛出的异常不会立刻抛出，而是延迟到调用 result() 时才抛出。
   - 避免用关键字（如 result）作为变量名覆盖标准语义。
"""

from concurrent.futures import ThreadPoolExecutor
import time


def task(name: str):
    print(f'{name} - set1\n', end='')
    time.sleep(1)          # 模拟耗时操作
    print(f'{name} - set2\n', end='')
    return f'{name} - 完成'


with ThreadPoolExecutor() as executr:  # 线程池支持上下文管理器；退出 with 时会等待所有任务完成
    # submit：提交"一个"任务，返回 Future 对象；任务不同、参数不同时用 submit
    result_1 = executr.submit(task, 'a')
    result_2 = executr.submit(task, 'b')

    # Future.result() 会阻塞等待该任务完成并返回其结果
    print(result_1.result())   # 若 result_1 还没执行完，主线程会在这里阻塞等待
    print(result_2.result())

with ThreadPoolExecutor() as executr:
    # map：同一个函数处理多个参数，适合"任务相同、参数不同"的批量场景
    result = executr.map(task, ['c', 'b'])
    for i in result:
        print(i)


# ==============================================================================
# 补充示例 1：指定 max_workers 并批量提交任务（收集 Future 列表后统一取结果）
# ==============================================================================
def add(a: int, b: int) -> int:
    return a + b


def demo_max_workers():
    with ThreadPoolExecutor(max_workers=3) as pool:   # 明确池中最多 3 条线程
        futures = []
        for x in range(5):
            futures.append(pool.submit(add, x, x * 10))   # 批量提交并保存 Future
        for f in futures:
            print(f'结果 = {f.result()}')    # result() 阻塞等待各自任务完成


# ==============================================================================
# 补充示例 2：as_completed —— 谁先完成就先处理谁的结果（不必按提交顺序）
# ==============================================================================
from concurrent.futures import as_completed


def slow_task(sec: float, tag: str) -> str:
    time.sleep(sec)
    return f'{tag} 睡了 {sec} 秒'


def demo_as_completed():
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(slow_task, sec, f'task-{sec}') for sec in [2, 1, 0.5, 3]]
        for f in as_completed(futures):   # 按"完成先后"而不是"提交顺序"产出结果
            print(f'完成: {f.result()}\n', end='')


if __name__ == '__main__':
    demo_max_workers()
    demo_as_completed()
