"""
================================================================================
知识点：线程进阶 —— 继承 Thread 创建线程、守护线程（daemon）、join
================================================================================

【核心概念】
1. 创建线程的两种方式
   - 方式一（见上一个文件）：Thread(target=函数, args=(参数,))，把"函数"交给线程执行。
   - 方式二（本文件）：自定义类继承 threading.Thread，重写 run() 方法。
     线程被 start() 启动后会自动调用 run()，run() 里就是该线程要执行的任务。

2. self.name 是 Thread 的内建属性（会被重写）
   - Thread 类内部本身就有一个 name 属性（线程名），默认形如 "Thread-1"、"Thread-2"。
   - 在子类 __init__ 里写 self.name = 'xxx'，实际上会"覆盖"父类的内建属性，
     把它改成了我们自己的值。
   - 更规范的做法：super().__init__(name='自定义名') 把线程名交给父类管理，
     自己的业务数据用独立属性（如 self.label）保存，避免覆盖 name 丢失线程身份信息。

3. daemon 守护线程
   - 线程分"守护线程（daemon=True）"和"非守护线程（daemon=False，默认）"。
   - 守护线程：主线程结束后会被强制终止（无论是否执行完）。
   - 非守护线程：主线程结束不会杀死它，程序会等所有非守护线程执行完才退出。
   - 使用场景：守护线程适合日志打印、心跳检测等"非关键"任务；关键任务用
     非守护线程 + join() 等待完成。

4. join() 的作用
   - 谁调用 join()，谁就阻塞等待"被 join 的线程"执行结束。
   - 易错点：漏掉 join() 可能导致主线程提前结束。虽然本例 t_2 是守护线程、
     主线程结束它会被终止（不报错），但输出可能不完整、行为不可控，所以应补上 join()。

【工作原理】
   - start() 内部会新开一条线程，并在该线程中自动调用 run()；
     因此 run() 不要手动调用，更不要把它当普通方法直接调。
   - run() 的执行和主线程是并发的（由操作系统调度，顺序不确定）。

【注意事项与易错点】
   - run() 不能有返回值（返回值会被忽略）；想拿计算结果，应使用线程安全的
     容器（如 queue.Queue，见第 3 个文件）或 concurrent.futures（见第 5 个文件）。
   - 同一线程对象 start() 之后不能再 start()；join() 也只在 start() 之后有意义。
   - 守护线程里尽量避免操作共享资源/文件，因为主线程退出时它可能随时被"掐断"。
"""

from threading import Thread
import time


class MyThread(Thread):
    """通过继承 Thread 类来创建线程。"""

    def __init__(self, name: str, count: int):
        super().__init__()          # 必须先调用父类初始化，否则 Thread 内部状态不完整
        self.name = name            # 覆盖 Thread 内建的 name 属性（当作业务标识用）
        self.count = count          # 自定义属性：要打印多少次
        self.daemon = True          # 守护线程：主线程结束后守护线程自动结束，一般用于非关键性线程（如打印日志）

    def run(self) -> None:          # 重写 run 方法：子线程 start() 后会自动调用
        for n in range(self.count):
            print(f'{self.name}-{n}\n', end='')
            time.sleep(0.01)        # 睡眠 0.01 秒，模拟耗时，也让线程调度更明显


t_1 = MyThread('a', 20)   # 创建线程对象 a
t_2 = MyThread('b', 20)   # 创建线程对象 b

t_1.start()   # 启动后会自动调用 run 方法
t_2.start()

t_1.join()    # 主线程等待 t_1 执行结束
t_2.join()    # 补上 t_2.join()：等待 t_2 结束，避免主线程提前结束导致输出不完整

print('所有线程执行完毕，主线程结束')


# ==============================================================================
# 补充示例 1：更规范地设置线程名 —— super().__init__(name=...)
# ==============================================================================
class NamedThread(Thread):
    """推荐写法：线程名交给父类管理，业务标识用独立属性。"""

    def __init__(self, label: str, count: int):
        super().__init__(name=f'线程-{label}')   # 线程名交给父类维护
        self.label = label          # 业务标识用独立属性，避免覆盖内建 name
        self.count = count

    def run(self) -> None:
        for n in range(self.count):
            # 这里 self.name 是父类维护的线程名（如 '线程-A'）
            print(f'{self.name}({self.label}) - {n}\n', end='')
            time.sleep(0.01)


def demo_named_thread():
    a = NamedThread('A', 5)
    b = NamedThread('B', 5)
    a.start()
    b.start()
    a.join()
    b.join()


# ==============================================================================
# 补充示例 2：对比"守护线程"与"非守护线程"在程序退出时的区别
# ==============================================================================
class GuardThread(Thread):
    """非守护线程：执行 3 次，共约 0.9 秒。"""

    def run(self) -> None:
        for i in range(3):
            print(f'普通线程 第{i}步\n', end='')
            time.sleep(0.3)
        print('普通线程 执行完毕\n', end='')


class DaemonThread(Thread):
    """守护线程：执行 10 次，共约 3 秒；主线程结束时会被强制终止。"""

    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self) -> None:
        for i in range(10):
            print(f'守护线程 第{i}步\n', end='')
            time.sleep(0.3)
        print('守护线程 执行完毕\n', end='')


def demo_daemon():
    normal = GuardThread()
    daemon = DaemonThread()
    normal.start()
    daemon.start()
    normal.join()   # 只等待普通线程跑完
    # 普通线程约 0.9 秒就结束了，此时守护线程才执行约 3 步；
    # 主线程随之结束，守护线程被强制终止（"执行完毕"一般不会打印）
    print('主线程结束 —— 注意：守护线程还没跑完就被终止了')


if __name__ == '__main__':
    demo_named_thread()
    demo_daemon()
