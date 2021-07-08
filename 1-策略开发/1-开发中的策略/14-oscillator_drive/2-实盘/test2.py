#%%
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string
import datetime

wb = openpyxl.load_workbook("D:/CTA/1-策略开发/1-开发中的策略/14-oscillator_drive/2-实盘/example.xlsx")

sheet = wb["Sheet1"]

print(get_column_letter(sheet.max_column))

print(column_index_from_string("AA"))



# for i in range(1, 27, 1):
#     for j in range(1, 4, 1):
#         print(sheet.cell(row=i, column=j).value)