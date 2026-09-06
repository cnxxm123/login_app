'''
任务进阶 (Task Advanced) —— 任务的取消、超时与并发等待

【核心概念】
1. task.cancel()：向任务发出"取消请求"。它并不会立刻终止任务，
   而是在任务内部抛出一个 asyncio.CancelledError 异常；
   如果任务正挂在某个 await 上，就会在那里收到取消信号。
2. task.done()：判断任务是否已结束。只要任务正常结束、被取消或抛出异常，都算结束。
3. asyncio.wait_for(aw, timeout)：给一个可等待对象设置超时。
   超时后会【取消】被等待的任务（默认行为），并向等待方抛出 asyncio.TimeoutError。
4. asyncio.shield(aw)：给任务"套一层护盾"。wait_for 超时想取消任务时，
   shield 会替任务挡下取消请求，让任务继续在后台运行（避免"超时就把后台任务中断"）。
5. asyncio.gather(*aws, return_exceptions=False)：并发等待多个可等待对象。
   - 返回所有任务的返回值组成的列表（按传入顺序）；
   - return_exceptions=True 时，某个任务抛异常不会立刻打断整体，
     而是把异常对象作为对应位置的结果返回，由我们自己判断处理；
   - return_exceptions=False（默认）时，第一个异常会直接向外抛出。

【工作原理】
事件循环统一调度所有任务。取消、超时本质都是向任务注入 CancelledError，
任务可以在 except asyncio.CancelledError 中做清理工作（如关闭文件、释放资源），
清理完毕后通常应重新抛出异常，让任务真正结束。

【使用场景】
- 取消任务：用户点击"停止下载"、任务已无继续执行的价值时；
- 超时控制：请求外部 API 时限制最长时间，防止程序一直卡住；
- shield 保护：后台任务（如正在写文件、上报数据）不希望被超时/取消影响时。

【注意事项与易错点】
1. cancel() 只是发出请求。如果任务捕获了 CancelledError 却不重新抛出，
   任务的"取消"就会失效，容易造成逻辑混乱。
2. 对被取消的任务调用 result() 会抛出 CancelledError。
3. wait_for 超时默认会取消任务；如果不想取消，应配合 shield 使用。
4. 使用 shield 后仍需 await 原任务，确保主流程等后台任务真正结束。
5. gather 使用 return_exceptions=True 时，正常任务返回结果，出错任务返回异常对象，
   需要自己区分处理。
'''
import asyncio


async def play_music(music: str):
    """播放音乐：耗时 3 秒，用来模拟一个耗时任务。"""
    print(f'开始播放{music}')
    await asyncio.sleep(3)   # 模拟播放 3 秒
    print(f'播放完成{music}')
    return music


async def my_cancel():   # 知识点演示 1：主动取消任务
    task_1 = asyncio.create_task(play_music('A'))   # A 需要播放 3 秒
    await asyncio.sleep(1)    # 只等 1 秒，此时任务 A 肯定还没播完
    if not task_1.done():     # 判断任务是否已完成（这里显然是未完成）
        task_1.cancel()       # 取消任务：向任务注入 CancelledError
    # 被取消后再次 await，会抛出 CancelledError，需要捕获避免程序报错
    try:
        await task_1
    except asyncio.CancelledError:
        print('任务A已被取消')
    # 注意：输出中不会出现"播放完成A"，因为任务被取消了


async def time_out_cancel():   # 知识点演示 2：任务超时自动取消
    task_2 = asyncio.create_task(play_music('B'))   # B 需要播放 3 秒
    try:
        # wait_for 最多等待 2 秒；超时后会自动取消 task_2，并抛出 TimeoutError
        await asyncio.wait_for(task_2, 2)
    except TimeoutError:
        print('任务超时，已被自动取消')
    # task_2 在 wait_for 超时那一刻就被取消了，因此不会再打印"播放完成B"


async def time_out():   # 知识点演示 3：超时提醒但不取消任务（shield 保护）
    task_3 = asyncio.create_task(play_music('C'))
    try:
        # shield 相当于给 task_3 套了护盾：wait_for 超时想取消它时会被挡下，
        # 所以任务 C 会继续在后台播放完（3 秒），不会被中断
        await asyncio.wait_for(asyncio.shield(task_3), 2)
    except TimeoutError:
        print('任务超时（只是提醒，任务C仍在后台继续运行）')
        # 由于任务没被取消，这里需要继续 await 原任务，等它真正结束
        await task_3
    # 最终会打印"播放完成C"，说明任务没被取消


async def my_gather():   # 知识点演示 4：gather 并发等待多个任务
    task_4 = asyncio.create_task(play_music('D'))
    # gather 会自动并发执行并等待所有任务完成，相当于一次等完多个任务
    # return_exceptions=True：某个任务出错时不会中断整体，而是把异常作为结果返回
    result = await asyncio.gather(task_4, play_music('E'), return_exceptions=True)
    print('gather 返回结果：', result)   # 正常时应为 ['D', 'E']


# ================== 依次运行四个知识点演示 ==================
asyncio.run(my_cancel())        # 演示取消任务
asyncio.run(time_out_cancel())  # 演示超时自动取消
asyncio.run(time_out())         # 演示 shield 保护任务不被取消
asyncio.run(my_gather())        # 演示 gather 并发等待


# ================== 补充示例 1：捕获 CancelledError 做清理 ==================
async def cleanup_task():
    try:
        print('任务开始，等待中...')
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        # 任务被取消时，可以在这里做清理工作（关闭文件、释放资源等）
        print('捕获到取消信号，正在清理资源...')
        raise   # 清理完毕后重新抛出，让任务真正以"被取消"的状态结束（推荐做法）


async def demo_cancel_cleanup():
    task = asyncio.create_task(cleanup_task())
    await asyncio.sleep(1)
    task.cancel()   # 发出取消请求
    try:
        await task
    except asyncio.CancelledError:
        print('任务已取消并完成清理')


asyncio.run(demo_cancel_cleanup())


# ================== 补充示例 2：gather 与 return_exceptions 的异常处理 ==================
async def may_fail(name: str, fail: bool):
    await asyncio.sleep(1)
    if fail:
        raise ValueError(f'{name} 出错了')
    return f'{name} 成功'


async def demo_gather_exceptions():
    results = await asyncio.gather(
        may_fail('任务1', False),   # 正常返回字符串
        may_fail('任务2', True),    # 抛出异常，但不会打断整体
        return_exceptions=True,     # 异常作为返回值，而不是直接抛出
    )
    for r in results:
        print(type(r).__name__, '->', r)   # 正常的是 str，出错的是 ValueError 对象


asyncio.run(demo_gather_exceptions())
