# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FormHello.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FormHello(object):
    def setupUi(self, FormHello):
        FormHello.setObjectName("FormHello")
        FormHello.resize(940, 577)
        self.LabelHello = QtWidgets.QLabel(FormHello)
        self.LabelHello.setGeometry(QtCore.QRect(300, 200, 201, 111))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.LabelHello.setFont(font)
        self.LabelHello.setObjectName("LabelHello")
        self.btnClose = QtWidgets.QPushButton(FormHello)
        self.btnClose.setGeometry(QtCore.QRect(340, 340, 80, 20))
        self.btnClose.setObjectName("btnClose")

        self.retranslateUi(FormHello)
        QtCore.QMetaObject.connectSlotsByName(FormHello)

    def retranslateUi(self, FormHello):
        _translate = QtCore.QCoreApplication.translate
        FormHello.setWindowTitle(_translate("FormHello", "Demo2_2"))
        self.LabelHello.setText(_translate("FormHello", "Hello, by UI Designer"))
        self.btnClose.setText(_translate("FormHello", "关闭"))
