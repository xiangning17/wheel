# AsyncExecutor多线程执行器

**<font size=4 color=blue>S:</font>**

实现深度优先网页爬虫（假设网站只有三个层级）。如下：

    def get_url(url):
        print url   # 输出当前url
        children = parse_and_get_children(url)  # 获取下一级链接
        for child in children:
            get_url()
 
使用多线程改进，选用‘concurrent.futures’包中的ThreadPoolExecutor

    pool = ThreadPoolExecutor()
    
    def get_url(url):
        print url   # 输出当前url
        children = parse_and_get_children(url)  # 获取下一级链接
        
        results = pool.map(get_url, children)   # 注意，此处是递归
        
        for r in results:   # results为返回值集合的迭代器
            pass

在以上实现中，后面的对结果的迭代是必须的，不然主线程会因为执行完退出。
而pool中的线程又是守护线程，因而程序将不会等待子线程执行完成而提前结束。

不过虽然都是等待，但使用线程池的等待却也比单个线程的等待更有效率。
因为线程池是同时执行n个任务，然后等待n个任务都完成。
而单线程是只有一个线程执行任务。

假设有n个线程，同事任务的个数也是n。
那么我们在获取第一个任务的结果时应该会等待时间t。
但是当我们获取到第一个任务的结果时，其他任务也基本完成了，因而不用继续等待了。
于是使用线程池时我们的等待时间从n*t变为了t。

但在我们上面实现的代码中，情况又不一样，由于必须实现这个等待结果的过程。
这里我们又在其中递归调用**get_url**,当我们第一次在主线程调用get_url时（还是假设线程数与每次的子链接数都是n），
把task1, task2, ..., taskn都分发出去投入到线程池后，主线程就进入了等待。

再考虑thread1的执行情况！
此时thread1正在执行task1，同样task1会分发n个子任务并等待其结果。

**<font color=red>但是！！！</font>**
task1在进入等待的时候，会导致所在线程thread1进入wait的状态而持续占用线程资源。
同理，其他n-1个线程也一样。
于是n个线程都在等待，没有线程可以继续处理由task1等任务分发出的子任务。
但是task1又必须等待子任务返回才能返回，于是，就死锁了！！！

所以，我们<font size=5 color=red>不能在使用线程池时使用递归的程序结构！</font>

所以使用ThreadPoolExecutor时，必须要修改程序结构才能达到要求。

那其实造成这种现象的原因是因为我们必须等待map执行的结果返回，导致task不能及时在完成实际处理后立即释放线程资源。

那是否可以不等待结果呢？反正我们的函数又没有返回值。

但我们前面讨论过，若不等待，程序会提前结束。

鉴于此，来寻求一种方案在不改变递归结构的情况下，解决这个问题。
    
**<font size=4 color=blue>T:</font>**

实现可使用递归函数的线程池

**<font size=4 color=blue>A:</font>**

1. 分析问题，发现由于未涉及函数返回值，因此等待任务的结果并不是必须的。
这个等待纯粹是因为需要知道任务是否已完成以便主线程退出，不然会导致提前结束程序。
那是否能找到另一种方法来判定是否所有任务都已完成？

2. 分析ThreadPoolExecutor的实现，发现map方法的实现还是使用submit对单个任务进行提交，
而submit返回的是一个future对象,我们可以使用`future.result()`来在future对象上等待其返回值。
更重要的是，future提供一个任务完成回调接口`future.add_done_callback()`能够在不等待的情况下使调用者得到任务完成的通知。
这为解决问题提供了线索。

3. 根据`add_done_callback`设计一个中间层AsyncExecutor，其包含一个计数器，可以对当前还未完成的任务进行记录。
对外提供`join()`接口，若计数器不为0，使调用者在一个Condition上等待，当所有任务完成，其会被自动唤醒。

4. 为使用方便，增加装饰器使用方式。

**<font size=4 color=blue>R:</font>**

完成了既定目标，实现了AsyncExecutor类。
改造之前代码为：

    from AsyncExecutor import AsyncExecutor

    pool = AsyncExecutor(10)
    
    def get_url(url):
        print url   # 输出当前url
        children = parse_and_get_children(url)  # 获取下一级链接
        
        for child in children:
            pool.submit(get_url, child)     # 提交任务
        
    get_url('http://www.test.com/')
    pool.join() # 等待任务完成退
    
或者使用更简洁的装饰器方式：

    from AsyncExecutor import async
    
    @async_executor(10)
    def get_url(url):
        print url   # 输出当前url
        children = parse_and_get_children(url)  # 获取下一级链接
        
        for child in children:
            get_url(child)
        
    get_url('http://www.test.com/')
    get_url.join() # 等待任务完成退出程序
    
可以看到，装饰器模式下，代码结构基本没有变化。只需要在函数声明时加上`@async`装饰，
并在随后使用`函数名.join()`等待所有任务结束即可。
