"""
================================================================================
知识点：线程锁 —— Lock 与 Condition（条件变量）
================================================================================

【核心概念】
1. 竞争条件（Race Condition）与数据不一致
   - 当多个线程在同一时刻访问/修改同一份数据时，可能产生数据丢失、覆盖、
     不完整等问题。
   - 例如"两个线程同时读到旧值、各自 +1、再写回"，导致结果比预期小。
   - 锁（Lock）是解决这一问题的常用手段。

2. Lock 的两种写法
   - 手动写法：lock.acquire() ... lock.release()，必须成对出现，
     忘记 release() 会导致其他线程永久阻塞（死锁）。
   - 推荐写法：with lock: ...，with 退出时自动释放锁（即使中途抛异常也会释放）。

3. 工作原理
   - 一个线程拿到锁后，其他想拿锁的线程会阻塞等待，直到持锁线程释放，
     从而保证"同一时刻只有一个线程执行被保护的代码段"（互斥访问）。

4. 死锁的产生与避免
   - 死锁：多个线程互相持有对方需要的锁、互不相让，导致所有线程永久阻塞。
   - 常见成因：锁忘记释放；嵌套加锁顺序不一致；获取锁后抛异常导致未释放。
   - 避免方法：
     * 尽量使用 with 语句（自动释放）。
     * 加锁粒度尽量小、持锁时间尽量短。
     * 多把锁时，所有线程保持一致的加锁顺序，避免交叉等待。
     * 可用 acquire(timeout=...) 限制等待时间，超时后放弃，避免永久阻塞。

5. Condition（条件变量）的工作机制
   - Condition 是更高级的同步原语，用于线程间"协调"：条件不满足时阻塞等待，
     条件满足后由其他线程唤醒。
   - wait()：释放锁并阻塞当前线程，直到被其他线程唤醒（唤醒后自动重新获取锁）。
   - notify()：唤醒一个正在等待的线程。
   - notify_all()：唤醒所有正在等待的线程。
   - 典型应用：有界队列（生产者-消费者）——队列满时生产者 wait，消费者取走后
     notify；队列空时消费者 wait，生产者放入后 notify。

【注意事项与易错点】
   - wait() 必须在持锁状态下调用（with cond: 或 acquire 之后），否则报 RuntimeError。
   - 条件判断要用 while 而不是 if（防止"虚假唤醒"，被唤醒后要重新检查条件）。
   - 普通 Lock 不可重入：同一线程重复 acquire 同一把锁会死锁；需要可重入请用 RLock。
"""

import time
from threading import Thread, Lock, Condition

# 创建一把全局锁
lock = Lock()


def task(name: str):
    global lock
    for i in range(100):
        lock.acquire()  # 上锁：同一时刻只允许一个线程进入下面 3 条打印语句
        print(f'{name} - {i} - set1')
        print(f'{name} - {i} - set2')
        print(f'{name} - {i} - set3')
        lock.release()  # 解锁：必须成对出现，忘了 release 会导致其他线程永久阻塞


t1 = Thread(target=task, args=('a',))
t2 = Thread(target=task, args=('b',))
t3 = Thread(target=task, args=('c',))

t1.start()
t2.start()
t3.start()

t1.join()
t2.join()
t3.join()

# ------------------------------------------------------------------------------
# 下面的 SaveQueue 是用 Condition 实现的一个"线程安全有界队列"（保留注释形式）。
# 它演示了生产者-消费者场景下 wait / notify_all 的配合使用。
# 想运行它，可取消注释并配合下方的 MsgProducer / MsgCustomer 一起使用。
# ------------------------------------------------------------------------------
# class SaveQueue:
#     def __init__(self, size: int):
#         self.size = size
#         self.__item_list = []
#         self.__condition = Condition()
#
#     def put(self, value):
#         # with self.__condition 相当于 acquire + 结束时自动 release
#         with self.__condition:  # 上锁，支持上下文管理器
#             while len(self.__item_list) >= self.size:   # 用 while 防止虚假唤醒
#                 self.__condition.wait()  # 队列满：释放锁并睡眠，等消费者取走数据后唤醒
#             self.__item_list.insert(0, value)
#             self.__condition.notify_all()   # 叫醒所有正在睡眠的线程（等待数据的消费者）
#         # 退出 with 自动解锁（原代码里的 release 可省略）
#
#     def get(self):
#         with self.__condition:  # 上锁
#             while len(self.__item_list) == 0:    # 队列空：睡眠并释放锁，等生产者放入数据
#                 self.__condition.wait()
#             result = self.__item_list.pop()
#             self.__condition.notify_all()   # 叫醒所有正在睡眠的线程（等待空位的生产者）
#         return result
#
# class MsgProducer(Thread):  # 生产者，生产消息
#     def __init__(self, name: str, count: int, queue):
#         super().__init__()
#         self.name = name
#         self.count = count
#         self.queue = queue
#
#     def run(self) -> None:
#         for i in range(self.count):
#             msg = f'{self.name} - {i}'
#             self.queue.put(msg)
#
# class MsgCustomer(Thread):  # 消费者，处理消息
#     def __init__(self, name: str, queue):
#         super().__init__()
#         self.name = name
#         self.queue = queue
#         self.daemon = True
#
#     def run(self):
#         while True:
#             msg = self.queue.get()
#             print(f'{self.name} - {msg}\n', end='')
#
# queue = SaveQueue(3)
# ls = []
# ls.append(MsgProducer('PA', 10, queue))
# ls.append(MsgProducer('PB', 10, queue))
# ls.append(MsgProducer('PC', 10, queue))
# ls.append(MsgCustomer('CA', queue))
# ls.append(MsgCustomer('BA', queue))
# for i in ls:
#     i.start()


# ==============================================================================
# 补充示例 1：演示"竞争条件"—— 不加锁计数结果错误，加锁后结果正确
# ==============================================================================
import threading

count_no_lock = 0      # 不加锁保护的共享变量
count_lock = 0         # 加锁保护的共享变量
lock_demo = threading.Lock()


def add_no_lock(n: int):
    global count_no_lock
    for _ in range(n):
        count_no_lock += 1   # 读-改-写三步并非原子操作，多线程下会互相覆盖，导致结果偏小


def add_with_lock(n: int):
    global count_lock
    for _ in range(n):
        with lock_demo:      # with 语句：进入自动上锁，退出自动解锁（推荐写法）
            count_lock += 1


def demo_race():
    global count_no_lock, count_lock
    count_no_lock, count_lock = 0, 0

    threads1 = [Thread(target=add_no_lock, args=(100000,)) for _ in range(5)]
    for t in threads1:
        t.start()
    for t in threads1:
        t.join()
    print(f'不加锁：期望 500000，实际 = {count_no_lock}（通常小于期望值，数据丢失）')

    threads2 = [Thread(target=add_with_lock, args=(100000,)) for _ in range(5)]
    for t in threads2:
        t.start()
    for t in threads2:
        t.join()
    print(f'加锁后：期望 500000，实际 = {count_lock}（结果正确）')


# ==============================================================================
# 补充示例 2：用 Condition 实现"厨师做菜 + 吃货吃饭"的协作（wait / notify）
# ==============================================================================
food_ready = False            # 共享条件：食物是否已做好
condition = Condition()


def cook():
    """厨师：做菜需要时间，完成后通知吃货可以开吃。"""
    global food_ready
    time.sleep(1)             # 模拟做菜耗时
    with condition:
        food_ready = True     # 更新共享条件
        print('厨师：菜做好了，通知吃货')
        condition.notify()    # 唤醒一个正在 wait 的线程（吃货）


def eater():
    """吃货：没菜就先等（释放锁并阻塞），被唤醒后再检查条件并开吃。"""
    global food_ready
    with condition:
        while not food_ready:          # 用 while 重新检查条件（防止虚假唤醒）
            print('吃货：还没有菜，先等着...')
            condition.wait()           # 释放锁并阻塞，等厨师 notify 唤醒
        print('吃货：开吃！')


def demo_condition():
    c = Thread(target=cook)
    e = Thread(target=eater)
    e.start()    # 先让吃货进入等待状态
    c.start()
    e.join()
    c.join()


if __name__ == '__main__':
    demo_race()
    demo_condition()
