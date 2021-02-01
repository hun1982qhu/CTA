# 测量程序运行时间命令
# 第一种方法
from timeit import default_timer as timer
tic = timer()
# 待测试的代码
toc = timer()
print(toc - tic) # 输出的时间，秒为单位
# 第二种方法
import time
start = time.time()
# 待测试的代码
end = time.time()
print('Running time: {} Seconds’.format(end-start))
