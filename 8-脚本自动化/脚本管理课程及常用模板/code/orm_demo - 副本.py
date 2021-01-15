import json

from peewee import (
    AutoField,
    CharField,
    Database,
    FloatField,
    Model,
    SqliteDatabase
)

# 使用vn.py运行时目录的SQLite数据库
from vnpy.trader.utility import get_file_path
from vnpy.trader.setting import SETTINGS
path = get_file_path(SETTINGS["database.database"])

# 或者可以手动指定数据库位置
# path = "c:\\users\\administrator\\.vntrader\\database.db"

# 创建数据库对象
db = SqliteDatabase(path)

# 创建数据ORM的类
class DbStrategyData(Model):
    """对应表为dbstrategydata"""

    id =  AutoField()