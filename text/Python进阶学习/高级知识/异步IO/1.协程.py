'''
协程 (Coroutine) —— 异步编程的基础

【核心概念】
协程是一个可以被"挂起(suspend)"和"恢复(resume)"的函数，Python 中通过 async/await 关键字实现。
- async def 定义的是一个"协程函数"，调用它并不会立即执行函数体，
  而是返回一个"协程对象(coroutine object)"，必须由事件循环来驱动它执行。
- await 用于等待一个可等待对象(awaitable)。当协程执行到 await 时会"挂起"，
  把控制权交还给事件循环，让事件循环去调度执行其它已经就绪的协程。
- 事件循环(event loop)是异步编程的核心调度器：它不停地从任务队列中挑选
  "可以继续执行"的协程来运行，遇到 await 挂起就切走，从而实现"单线程内的并发"。

【工作原理】
asyncio.run() 是 Python 3.7+ 提供的异步入口函数，它做的事情是：
1. 创建一个新的事件循环；
2. 把传入的协程对象包装成任务并运行，直到协程执行结束；
3. 关闭事件循环，释放资源。
简单理解：asyncio.run(main()) 就是把 main() 这个协程"扔进"事件循环里去执行。

【使用场景】
异步编程适合处理大量"耗时等待"而不是"密集计算"的操作，例如：
- 网络 IO：下载/上传文件、请求 HTTP 接口；
- 数据库操作：写入、查询（主要耗时在等待数据库返回结果）；
- 文件读写。
当程序大部分时间都花在"等待"上时，异步可以利用这些等待时间去执行别的任务，
从而提升整体的吞吐量。

【注意事项与易错点】
1. 协程对象不会自动执行！必须通过 await、asyncio.run() 或 asyncio.create_task()
   来驱动它，否则会得到 "coroutine was never awaited" 的 RuntimeWarning。
2. 只有在 await 处才会让出控制权。如果协程里有一段密集的 CPU 计算（没有 await），
   这段代码会阻塞整个事件循环，导致其它任务无法执行。
3. 异步并不能加速 CPU 密集型任务（如大规模数值计算），这类任务更适合多线程/多进程。
4. 一个协程对象只能被 await 一次，重复 await 会报错。
5. 异步代码中不要使用 time.sleep()，它会阻塞整个事件循环，
   应该使用 asyncio.sleep() 才能实现挂起并让出控制权。

【协程 vs 生成器 vs 线程】
- 生成器(Generator)：用 yield 实现，通过 next()/send() 手动驱动，本质是惰性求值、用于迭代。
- 协程(Coroutine)：用 async/await 实现，由事件循环自动调度，用于并发 IO。
- 线程(Thread)：由操作系统调度，多个线程真正并行（受 GIL 限制），切换开销大，
  且共享数据需要加锁保护；而协程切换开销极小，在单线程内即可实现高并发。
'''
import asyncio


async def calculate(n1: int, n2: int):   # async def 定义的是"协程函数"，调用后返回协程对象
    print(n1 + n2)                       # 函数体要到事件循环真正运行它时才会执行


async def main():
    # await 表示等待：main 协程在这里"挂起"，把控制权交给事件循环，
    # 等 calculate(1, 2) 这个协程执行结束后再继续往下走。
    await calculate(1, 2)


# asyncio.run() 的作用：创建事件循环 -> 运行 main 协程 -> 关闭事件循环
asyncio.run(main())


# ================== 补充示例 1：协程对象不会立即执行 ==================
async def say_hello():
    print('hello')
    await asyncio.sleep(1)
    print('world')


# 注意：下面这行只是"创建"了一个协程对象，函数体并【没有】执行！
coro = say_hello()
print('协程对象（未执行）:', coro)  # 输出类似 <coroutine object say_hello at 0x...>
coro.close()  # 关闭这个从未执行的协程对象，避免程序退出时报 "coroutine was never awaited" 警告

# 必须把协程交给事件循环才会真正运行：
asyncio.run(say_hello())


# ================== 补充示例 2：await 挂起让出控制权，事件循环调度并发 ==================
async def task(name: str, seconds: int):
    print(f'{name} 开始，预计耗时 {seconds} 秒')
    # 遇到 await 就挂起，把控制权让给事件循环；
    # 事件循环趁机去执行另一个已经就绪的任务，从而实现"并发"。
    await asyncio.sleep(seconds)
    print(f'{name} 结束')
    return name


async def main2():
    # create_task 把协程包装成任务并交给事件循环并发调度（详见 2.创建任务.py）
    t1 = asyncio.create_task(task('任务A', 2))
    t2 = asyncio.create_task(task('任务B', 3))
    # 两个任务几乎同时开始，总耗时约 3 秒，而不是串行执行的 2+3=5 秒
    await t1
    await t2


asyncio.run(main2())
