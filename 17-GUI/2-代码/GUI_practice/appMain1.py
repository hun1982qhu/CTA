#%%
import sys
from PyQt5 import QtWidgets
import ui_FormHello

app = QtWidgets.QApplication(sys.argv)
baseWidget = QtWidgets.QWidget()

ui = ui_FormHello.Ui_FormHello()
ui.setupUi(baseWidget)

baseWidget.show()

sys.exit(app.exec_())