# 在做VNPY 策略参数优化的时候， 优化数量多的时候要好几天，有时候也不知道完成数量，只能干等。
# 就稍微改了下代码，加入log显示完成数量和总数量，心里面有个底。
# 代码是在VNPY 1.9.2里面的因为我还在1.9.2的版本泥潭里，2.0之后直接用应该也可以的，只要稍微改下变量名称。
# 实质内容，就是python多进程共享变量访问更新，python提供几个不同的多进程变量共享的方法，比如使用可变对象queue。
# 这里其实只用定义一个int类型的counter，每个进程跑完后，counter加一，并在log中记录。
# 这里用了一个multiprocessing.Manager类，Manager可以对定义共享变量，和锁管理
# 把下面代码加入到class BacktestingEngine的runParallelOptimization方法中


#----------------------------------------------------------------------
def runParallelOptimization(self, strategyClass, optimizationSetting):
    """并行优化参数"""
    # 获取优化设置
    settingList = optimizationSetting.generateSetting()
    targetName = optimizationSetting.optimizeTarget
    # 检查参数设置问题
    if not settingList or not targetName:
        self.output(u'优化设置有问题，请检查')
    # 多进程优化，启动一个对应CPU核心数量的进程池
    pool = multiprocessing.Pool(multiprocessing.cpu_count()-1, maxtasksperchild = 10)
    l = []
    length0 = len(settingList)  # 获得参数优化带运行条
    manger =  multiprocessing.Manager() # 定义一个多进程管理对象
    counter = manger.Value('i',0) # 定义一个共享变量记录完成条目，int类型的
    lock = manger.Lock() # 顶一个访问锁，如果counter被一个进程修改时候，加锁，
    for setting in settingList:
        # 把刚刚顶一个的作为参数传入每个进程，实现变量共享
        l.append(pool.apply_async(optimize, (strategyClass, setting,
                                             targetName, self.mode,
                                             self.startDate, self.initDays, self.endDate,
                                             self.slippage, self.rate, self.size, self.priceTick,
                                             self.dbName, self.symbol,counter,lock,length0))) 
    pool.close()
    pool.join()
    # 显示结果
    resultList = [res.get() for res in l]
    resultList.sort(reverse=True, key=lambda result:result[1])
    return resultList

# 然后在optimize中，定义counter加1
#----------------------------------------------------------------------
def optimize(strategyClass, setting, targetName,
             mode, startDate, initDays, endDate,
             slippage, rate, size, priceTick,
             dbName, symbol,counter,lock,length0):
    """多进程优化时跑在每个进程中运行的函数"""
    ......
    engine.runBacktesting()
    # 当优化完成时候，counter加1
    with lock:
        counter.value += 1
    # 为了使用engine的log显示，更改calculateDailyResult，传入counter.value, length0
    engine.calculateDailyResult(counter.value, length0)
# 为了在log中显示，不得不修改下calculateDailyResult，其实这样改源代码不太合适
# 反正1.9.2已经被我搞得乱了，仅作参考，不合适的更新方法。
#----------------------------------------------------------------------
def calculateDailyResult(self,count = 0,length0 = 0):
    """计算按日统计的交易结果"""
    self.output(u'计算按日统计结果')
    # 显示完成数
    if count != 0:
        self.output(u'执行完成个数 %s / %s' % (count,length0))