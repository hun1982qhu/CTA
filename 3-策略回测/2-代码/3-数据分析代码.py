from vnpy.trader.database import database_manager

output("开始加载历史数据")
bars = database_manager.load_bar_data(    
    symbol=symbol, 
    exchange=exchange, 
    interval=interval, 
    start=start, 
    end=end,
)
output(f"历史数据加载完成，数据量：{len(bars)}")

def output(msg):
    """"""
    print(f"{datetime.now()}\t{msg}")