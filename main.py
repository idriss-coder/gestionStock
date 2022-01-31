# -*- coding: utf-8 -*-
import json
import os
import sqlite3

from PyQt5 import QtWidgets, QtCore
import sys, time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
from PyQt5.uic import loadUi

class Worker(QtCore.QObject):
    def __init__(self):
        super(Worker, self).__init__()

    def loadhome(self):
        from home import Home
        self.win = Home()

def loadpathsql(filepath):
    default = "./datas/pystock.db"
    db = default
    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                db = file.readline()
        else:
            db = default
    except:
        db = default
    return db

count = 0
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.loginui = loadUi("main.ui")
        self.splash = loadUi("splash.ui")

        self.thread = QtCore.QThread(self)
        self.worker = Worker()
        self.thread.started.connect(self.worker.loadhome)
        self.worker.moveToThread(self.thread)

        self.splash.setWindowFlag(Qt.FramelessWindowHint)
        self.splash.setAttribute(Qt.WA_TranslucentBackground)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        self.timer.start(40)
        self.timer.singleShot(0, lambda : self.splash.cm.setText("Bienvenue"))
        self.timer.singleShot(500, lambda : self.splash.cm.setText("Demarage des services..."))
        self.timer.singleShot(1000, lambda : self.splash.cm.setText("Chargement de la base de donnée..."))
        self.timer.singleShot(1001, self.startProcess)
        self.timer.singleShot(8000, lambda : self.splash.cm.setText("Initialisation..."))
        self.splash.show()

        self.loginui.setWindowTitle("connexion")
        self.dbpath = loadpathsql("db.txt")

        #editing
        self.loginui.setWindowFlag(Qt.FramelessWindowHint)
        self.loginui.setAttribute(Qt.WA_TranslucentBackground)
        self.loginui.connect.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=5, xOffset=2, yOffset=2, color=QtGui.QColor(0, 0,0, 10)))


        self.setup_connexion()
        #config
        self.loginui.log.setVisible(False)

    def setup_connexion(self):
        self.loginui.exit.clicked.connect(self.closeWindow)
        self.loginui.connect.clicked.connect(self.login)

    def startProcess(self):
        global count
        self.thread.start()

    #functions
    def login(self):
        #logins details
        self.pseudo = self.loginui.epseudo.text()
        self.password = self.loginui.epassword.text()
        print(f"Pseudo: {self.pseudo}")
        print(f"Password: {self.password}")
        print(f"{self.geometry()}")
        #window connection
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()

        # Get pseudo in database
        username = "SELECT * FROM users WHERE pseudo = ?"
        password = ""
        pseudo = ""
        role = ""
        id = ""
        for user in cur.execute(username, [self.pseudo]):
            password = user[5]
            pseudo = user[1]
            role = user[4]
            id = user[0]

        if self.pseudo == "" or self.password == "":
            self.loginui.log.setVisible(True)
        else:
            if self.pseudo == pseudo:
                if password == self.password:
                    with open("./datas/user.json", "w") as file:
                        json.dump({
                                    "id":id,
                                    "role":role,
                                    "pseudo":pseudo,
                                    "password":password,
                                    "start_time": f'{time.localtime().tm_mday}/{time.localtime().tm_mon}/{time.localtime().tm_year}/{time.localtime().tm_hour}/{time.localtime().tm_min}',
                                   },
                                  file,indent=4)

                    self.worker.win.loaduserinfos()
                    self.worker.win.win.show()
                    self.loginui.close()

                else:
                    self.loginui.log.setVisible(True)
            else:
                self.loginui.log.setVisible(True)

        connection.close()

    def progress(self):
        global count

        self.splash.load.setValue(count)


        if count > 100:
            self.timer.stop()

            self.splash.close()
            self.loginui.show()
            self.thread.quit()

        count += 1

    #system
    def closeWindow(self):
        exit(0)

app = QApplication(sys.argv)
mainWindow = MainWindow()
try:
    sys.exit(app.exec_())
except:
    mainWindow.thread.quit()
    print("exiting...")