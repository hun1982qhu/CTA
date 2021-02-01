from vnpy.trader.utility import ArrayManager


def calculate_adaptive_channel(am: ArrayManager, n: int, dev: float):
    """"""
    ma = am.sma(n)
    std = am.std(n)
    
    boll_up = ma + std * dev
    boll_down =  ma - std * dev

    kk_up = ma + atr * dev 
    kk_down =  ma - atr * dev

    donchian_up = am.high[-n:].max()
    donchian_down = am.low[-n:].min()

    channel_up =  max(boll_up, kk_up, donchian_up)
    channel_down = min(boll_down, kk_down, donchian_down)

    return channel_up, channel_down




        
    