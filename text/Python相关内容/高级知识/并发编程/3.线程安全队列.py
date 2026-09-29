"""
================================================================================
知识点：线程安全队列 —— 生产者/消费者模式与 queue.Queue
================================================================================

【核心概念】
1. 生产者-消费者模式
   - "生产者"（Producer）负责生产数据/消息并放入队列；
   - "消费者"（Consumer）负责从队列取出数据并处理。
   - 两者通过队列"解耦"：生产者不关心谁消费、何时消费；消费者不必等生产者。
   - 队列充当"缓冲 + 中转"，是最经典的多线程协作模型。

2. queue.Queue 是线程安全的
   - 标准库 queue.Queue 内部自动加锁，多个线程同时 put/get 不会出现数据错乱，
     因此可以放心地在多线程间共享同一个 Queue 对象。
   - 对比：普通 list/dict 多线程并发读写会出现"竞争条件"（数据不一致），
     需要自己加锁（见第 4 个文件）；Queue 已经替我们处理好了。

3. put / get 的阻塞行为
   - put(item)：放入数据。队列满（达到 maxsize）且 block=True（默认）时，
     当前线程会阻塞等待，直到队列有空位。
   - get()：取出数据。队列为空且 block=True（默认）时，当前线程会阻塞等待，
     直到有数据到来。
   - 这正是"消费者 while True get"能一直挂着等消息的原因：队列空时它阻塞而非报错。

4. maxsize 的作用
   - Queue(maxsize=N) 限制队列最多容纳 N 个元素，起"限流/背压"作用，
     防止生产者无限生产撑爆内存；maxsize <= 0 表示无限容量。

5. 为什么消费者要设 daemon=True？
   - 消费者通常是"永不退出"的 while True 死循环，专门等消息。
   - 若非守护线程，程序会永远等它结束而无法退出。
   - 设为守护线程后：主线程结束时（其他业务线程都完成），守护消费者被强制终止，
     程序才能正常退出。

【注意事项与易错点】
   - 本例只 start() 不 join()：生产者是非守护线程，主线程会等它们跑完；
     消费者是守护线程，主线程结束时自动被终止。
   - get(timeout=N) 超时会抛 queue.Empty，可避免永久阻塞。
   - 更规范的退出方式：生产完放入"哨兵值"（如 None）通知消费者结束（见补充示例）。
"""

from queue import Queue
from threading import Thread


class MsgProducer(Thread):   # 生产者：负责生产消息
    def __init__(self, name: str, count: int, queue: Queue):
        super().__init__()
        self.name = name
        self.count = count    # 要生产多少条消息
        self.queue = queue    # 共享的线程安全队列

    def run(self) -> None:
        for i in range(self.count):
            msg = f'{self.name} - {i}'
            self.queue.put(msg)   # 放入队列（线程安全）；队列满时会阻塞等待


class MsgCustomer(Thread):   # 消费者：负责取出并处理消息
    def __init__(self, name: str, queue: Queue):
        super().__init__()
        self.name = name
        self.queue = queue
        self.daemon = True    # 守护线程：主线程结束后消费者被强制终止，程序才能退出

    def run(self):
        while True:                          # 死循环：一直等待消息
            msg = self.queue.get(block=True) # 队列空时阻塞等待，有消息才返回
            print(f'{self.name} - {msg}\n', end='')


queue = Queue(3)              # 创建容量为 3 的线程安全队列（maxsize=3）
ls = []
ls.append(MsgProducer('PA', 10, queue))   # 生产者 PA，生产 10 条
ls.append(MsgProducer('PB', 10, queue))   # 生产者 PB，生产 10 条
ls.append(MsgProducer('PC', 10, queue))   # 生产者 PC，生产 10 条
ls.append(MsgCustomer('CA', queue))       # 消费者 CA（守护线程）
ls.append(MsgCustomer('BA', queue))       # 消费者 BA（守护线程）
for i in ls:
    i.start()                             # 依次启动所有线程


# ==============================================================================
# 补充示例：用"哨兵值（None）"优雅地通知消费者结束（更规范的生产者-消费者写法）
# ==============================================================================
def demo_sentinel():
    import time

    def producer(q: Queue, count: int):
        """生产 count 条数据，最后为每个消费者放一个哨兵值 None 表示"没有更多数据了"。"""
        for i in range(count):
            q.put(f'data-{i}')
            time.sleep(0.05)
        # 有 2 个消费者就放 2 个哨兵，确保每个消费者都能收到结束信号
        q.put(None)
        q.put(None)
        print('生产者已放完所有数据并发出结束信号\n', end='')

    def consumer(q: Queue, name: str):
        """不断 get，直到遇到哨兵值 None 才退出循环（不再依赖守护线程强杀）。"""
        while True:
            item = q.get()
            if item is None:                  # 收到结束信号
                print(f'{name} 收到结束信号，退出\n', end='')
                break
            print(f'{name} 处理 {item}\n', end='')

    q = Queue()
    t_p = Thread(target=producer, args=(q, 5))
    t_c1 = Thread(target=consumer, args=(q, '消费者-1'))
    t_c2 = Thread(target=consumer, args=(q, '消费者-2'))

    t_p.start()
    t_c1.start()
    t_c2.start()
    t_p.join()    # 等待生产者放完
    t_c1.join()   # 两个消费者收到哨兵后都会正常退出，可以 join 等待
    t_c2.join()
    print('所有生产者和消费者都已结束，主线程结束')


if __name__ == '__main__':
    demo_sentinel()
