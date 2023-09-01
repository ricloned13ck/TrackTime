import os
import sqlite3
import sys
import time
from datetime import datetime
from subprocess import check_output
from threading import Thread

import psutil
import win32gui
import win32process
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QGridLayout

import widget

programms = open('progs.cfg').read().split('\n')


class Worker(QThread):
    def run(self):
        th_0, th_1, th_2 = Thread(target=app.exec_), Thread(target=monitoring_without_active), Thread(
            target=monitoring_with_active)

        th_0.start(), th_1.start(), th_2.start()
        th_0.join(), th_1.join(), th_2.join()


def get_active_window_title():
    active_window_name = None
    if os.name == 'nt':
        try:
            active_window_name = psutil.Process(
                win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]).name()
        except Exception:
            pass
    else:
        try:
            active_window_name = check_output(["/usr/bin/xdotool", "getactivewindow", "getwindowname"]).strip()
        except Exception:
            pass
    return active_window_name


def get_process_info():
    start_time = {x: 10 ** 10 for x in programms}
    for process in psutil.process_iter():
        with process.oneshot():
            if process.name() in programms:
                name = process.name()
                try:
                    create_time = datetime.fromtimestamp(process.create_time())
                except OSError:
                    create_time = datetime.fromtimestamp(psutil.boot_time())
                if start_time[name] > time.mktime(create_time.timetuple()) + create_time.microsecond / 1E6:
                    start_time[name] = time.mktime(create_time.timetuple()) + create_time.microsecond / 1E6

    return start_time


def monitoring_without_active():
    conn_not_active = sqlite3.connect('time.sqlite')
    cursor_not_active = conn_not_active.cursor()
    for x in programms:
        cursor_not_active.execute(f"""CREATE TABLE IF NOT EXISTS  {str(x[:-4]).upper()}(
           time INT PRIMARY KEY);
        """)
        conn_not_active.commit()

    last = {x: 0 for x in programms}
    while True:
        now_time = time.time()
        starting_time = get_process_info()

        for process in programms:
            time_process = (now_time - starting_time[process]) / 60
            if time_process >= 1440 or time_process <= 0:
                cursor_not_active.execute(f"SELECT time FROM {str(process[:-4]).upper()};")
                res = cursor_not_active.fetchall()
                all_time = sum([x[0] for x in res])
                # print(f'В приложении {str(process[:-4]).upper()} Вы провели {all_time} минут')
                try:
                    cursor_not_active.execute(
                        f"insert or ignore into {str(process[:-4]).upper()} values ({last[process]});")
                    conn_not_active.commit()
                except:
                    cursor_not_active.execute(
                        f"insert or ignore into {str(process[:-4]).upper()} values (0);")
                    conn_not_active.commit()
            if 1440 >= time_process >= 0:
                last[process] = time_process
                # print(f'Приложение {str(process[:-4]).upper()} работает уже {time_process} минут')
        # print("\033c", end="")


def monitoring_with_active():
    last_active = get_active_window_title()
    last_time = time.time()
    conn_active = sqlite3.connect('time_active.sqlite')
    cursor_active = conn_active.cursor()
    for x in programms:
        cursor_active.execute(f"""CREATE TABLE IF NOT EXISTS  {str(x[:-4]).upper()}(
               time INT PRIMARY KEY);
            """)
        conn_active.commit()
    while True:
        active = get_active_window_title()
        if last_active != active and active is not None and last_active is not None and last_active in programms:
            now_time = time.time()
            cursor_active.execute(f"SELECT time FROM {str(last_active[:-4]).upper()};")
            res = cursor_active.fetchone()
            try:
                cursor_active.execute(
                    f"update {str(last_active[:-4]).upper()} set time = {res[0] + (now_time - last_time) / 60};")
                conn_active.commit()
            except:
                if res is None:
                    cursor_active.execute(
                        f"insert into {str(last_active[:-4]).upper()} values (0);")
                    conn_active.commit()
                    cursor_active.execute(
                        f"update {str(last_active[:-4]).upper()} set time = {(now_time - last_time) / 60};")
                    conn_active.commit()
                else:
                    cursor_active.execute(
                        f"insert into {str(last_active[:-4]).upper()} values (res[0]);")
                    conn_active.commit()

            last_time = now_time
            last_active = active
        elif last_active not in programms and last_active != active:
            last_time = time.time()
            last_active = active


class Widget(QtWidgets.QMainWindow, widget.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class MainWindow(QtWidgets.QWidget):
    timer = QTimer()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(870, 540))
        self.setWindowTitle("TrackTime")

        scrollArea = QtWidgets.QScrollArea()
        content_widget = QtWidgets.QWidget()
        scrollArea.setWidget(content_widget)
        scrollArea.setWidgetResizable(True)
        grid = QtWidgets.QGridLayout(content_widget)
        self.box = QtWidgets.QHBoxLayout()
        self.box.addWidget(scrollArea)
        self.setLayout(self.box)

        self.classes = [Widget() for i in range(len(programms))]
        [grid.addWidget(self.classes[i], i // 3, i % 3) for i in range(len(programms))]
        [self.classes[i].name.setText(programms[i]) for i in range(len(programms))]

        conn_not_active = sqlite3.connect('time.sqlite')
        cursor_not_active = conn_not_active.cursor()
        conn_active = sqlite3.connect('time_active.sqlite')
        cursor_active = conn_active.cursor()

        for i in range(len(programms)):
            process = programms[i]
            cursor_not_active.execute(f"SELECT time FROM {str(process[:-4]).upper()};")
            res = cursor_not_active.fetchall()
            all_time = sum([x[0] for x in res])

            cursor_active.execute(f"SELECT time FROM {str(process[:-4]).upper()};")
            active_time = cursor_active.fetchone()
            if active_time is None:
                active_time = (0,)
            self.classes[i].active_time.setText("Active Time: " + str(round(active_time[0], 1)) + ' minutes')
            self.classes[i].all_time.setText("All Time: " + str(round(all_time, 1)) + ' minutes')

        QThread.msleep(100)
        self._thread = Worker(self)
        self._thread.start()

        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.timeStep)
        self.timer.start()

    def timeStep(self):
        conn_not_active = sqlite3.connect('time.sqlite')
        cursor_not_active = conn_not_active.cursor()
        conn_active = sqlite3.connect('time_active.sqlite')
        cursor_active = conn_active.cursor()

        for i in range(len(programms)):
            process = programms[i]
            cursor_not_active.execute(f"SELECT time FROM {str(process[:-4]).upper()};")
            res = cursor_not_active.fetchall()
            all_time = sum([x[0] for x in res])

            cursor_active.execute(f"SELECT time FROM {str(process[:-4]).upper()};")
            active_time = cursor_active.fetchone()
            if active_time is None:
                active_time = (0,)
            self.classes[i].active_time.setText("Active Time: " + str(round(active_time[0], 1)) + ' minutes')
            self.classes[i].all_time.setText("All Time: " + str(round(all_time, 1)) + ' minutes')


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
