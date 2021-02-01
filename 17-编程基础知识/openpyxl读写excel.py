import xlrd
import xlwt
import scipy.stats as stats
import talib as ta
import math
import pandas as pd
import numpy as np
from functools import reduce
from openpyxl.workbook import Workbook
from timeit import default_timer as timer
import datetime
from datetime import datetime
from dateutil.parser import parse
import csv
import tushare as ts
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style

style.use('ggplot')
import seaborn as sns

sns.set()

mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
mpl.rcParams['axes.unicode_minus'] = False

wb = Workbook()
sheet = wb.active
sheet.title = '关于如何读取excel'
sheet['A1'] = '漫威宇宙'
rows = [['宫崎骏', '久石让'], ['龙猫', '千与千寻']]
for i in rows:
    sheet.append(i)
wb.save('/Users/huangning/PycharmProjects/1-Python学习/1-Python练习/4-爬虫课程/动画片.xlsx')
