echo "hello world"

copy .\QtAPP\Dialog.ui Dialog.ui
pyuic -o mainwindow_test.py MainWindow.ui
