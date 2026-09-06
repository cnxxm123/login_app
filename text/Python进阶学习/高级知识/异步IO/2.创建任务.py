'''
创建任务 (Task) —— 实现真正的并发调度

【核心概念】
asyncio.create_task(coro) 会把一个协程对象包装成"任务"(Task)，
并把它立即交给事件循环调度：任务一旦被创建，就会在事件循环的下一个循环点开始执行。
这与直接 await 协程完全不同：
- await coro：按顺序等待，await 完一个才轮到下一个，本质是"串行"的；
- create_task(coro)：把任务"扔进"事件循环的任务队列，多个任务并发执行，
  总耗时接近其中最长的那个任务，而不是所有任务耗时之和。

【工作原理】
事件循环会在各个任务之间快速切换（单线程内协作式调度）：
任务 a 执行到 await asyncio.sleep(2) 时挂起，让出控制权；
事件循环立刻转去执行任务 b，b 执行到 await asyncio.sleep(3) 时也挂起；
于是 a 和 b 几乎同时"并行等待"。总耗时约 3 秒（取最长者），而不是串行的 5 秒。

【asyncio.sleep 的意义】
asyncio.sleep(n) 用来模拟一个"耗时的 IO 等待"（网络请求、数据库查询、文件读写等）。
它返回一个可等待对象，必须用 await 挂起，否则任务不会真正让出控制权。
IO 等待期间 CPU 是空闲的，事件循环正是利用这段空闲时间去执行其它任务，
这就是异步并发的价值所在。

【time.perf_counter】
perf_counter() 返回一个高精度计时器（纳秒级），常用于测量代码执行耗时。
由于它是单调递增的（不受系统时间调整影响），比 time.time() 更适合做性能测试。
用法：time1 = time.perf_counter() ... time2 = time.perf_counter()，time2 - time1 即耗时。

【使用场景】
凡是"耗时等待"密集的操作都适合：网络通讯（下载/上传）、数据库读写、文件 IO 等。

【注意事项与易错点】
1. create_task 创建的任务必须 await（或加入 gather），否则程序可能在任务执行完之前退出。
2. 任务在创建后的下一个事件循环周期才开始执行，不是创建时立即同步执行。
3. await 协程对象 vs await 任务：两者都能等待结果，但任务在创建时就已经"并发启动"了；
   而直接 await 协程是"创建后立刻顺序等待"，没有并发效果。
4. 千万不要在协程里用 time.sleep() 模拟等待，它会阻塞整个事件循环，让并发失效。
'''
import asyncio
import time
import aiofiles


# 耗时的网络通讯（下载或上传东西）、数据库的写入和查询、文件的读写都可以使用异步 IO
async def call_api(name: str, delay: int):
    print(f'{name}-start')
    # asyncio.sleep 模拟耗时等待（比如发起一个网络请求、等待数据库响应）
    # 这里会"挂起"当前任务，把控制权让给事件循环，让它去执行其它任务
    await asyncio.sleep(delay)
    # 使用 aiofiles 进行异步文件写入，写入过程不会阻塞事件循环
    async with aiofiles.open('787.txt', 'a', encoding='utf-8') as f:
        await f.write('hello async')   # 真正执行写入操作（把字符串写进文件）
    print(f'{name}-end')


async def main():
    time1 = time.perf_counter()   # 记录开始时间（高精度计时）

    # create_task 把协程包装成任务并立即交给事件循环调度（并发启动）
    # 任务 a sleep 2 秒，任务 b sleep 3 秒，两者几乎同时开始执行
    a = asyncio.create_task(call_api('a', 2))
    b = asyncio.create_task(call_api('b', 3))

    # 注意：任务 a、b 创建后，main 继续执行到这里，await a 使 main 进入等待状态，
    # 事件循环转而执行任务 a（以及已经就绪的任务 b）。
    # 因为任务 a sleep 2 秒、任务 b sleep 3 秒，所以 a 先完成。
    await a                     # main 等待 a 完成；期间 a、b 其实都在并发执行
    print('a完成')              # a 已完成，b 还在等待状态，所以 main 可以先执行这一行
    await b                     # 再等待 b 完成，main 要等 b 结束才能继续
    print('b完成')

    time2 = time.perf_counter()   # 记录结束时间
    # 并发执行的总耗时约 3 秒（取 a、b 中最长的），而不是串行的 2+3=5 秒
    print(f'总耗时: {time2 - time1:.2f} 秒')


asyncio.run(main())


# ================== 补充示例：await 协程 vs await 任务（串行 vs 并发） ==================
async def work(name: str, seconds: int):
    print(f'{name} 开始')
    await asyncio.sleep(seconds)   # 模拟耗时等待
    print(f'{name} 结束')


async def demo_await_coro():
    """直接 await 协程：串行执行，总耗时 = 两个任务耗时之和（约 4 秒）"""
    t0 = time.perf_counter()
    await work('串行任务1', 2)
    await work('串行任务2', 2)     # 必须等上一个完成才轮到下一个
    print(f'串行耗时: {time.perf_counter() - t0:.2f} 秒')


async def demo_create_task():
    """create_task 创建任务：并发执行，总耗时 ≈ 最长任务耗时（约 2 秒）"""
    t0 = time.perf_counter()
    t1 = asyncio.create_task(work('并发任务1', 2))   # 两个任务并发启动
    t2 = asyncio.create_task(work('并发任务2', 2))
    await t1
    await t2
    print(f'并发耗时: {time.perf_counter() - t0:.2f} 秒')


asyncio.run(demo_await_coro())
asyncio.run(demo_create_task())
