import sys
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QGridLayout

import widget


class ExampleApp(QtWidgets.QMainWindow, widget.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(870, 540))
        self.setWindowTitle("My App")

        scrollArea = QtWidgets.QScrollArea()
        content_widget = QtWidgets.QWidget()
        scrollArea.setWidget(content_widget)
        scrollArea.setWidgetResizable(True)
        grid = QtWidgets.QGridLayout(content_widget)


        x, y = 266, 270
        classes = [ExampleApp() for i in range(10)]
        [grid.addWidget(classes[i], i // 3, i % 3) for i in range(10)]
        classes[0].name.setText('123')
        classes[1].name.setText('1223')

        self.box = QtWidgets.QHBoxLayout()
        self.box.addWidget(scrollArea)

        self.setLayout(self.box)


StyleSheet = '''
QFrame{
    background: rgb(150,150,250);
    opacity: 100;
}
'''



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    window = MainWindow()
    window.show()
    app.exec_()
