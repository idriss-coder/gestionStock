# -*- coding: utf-8 -*-
import os
import sqlite3
import sys, time, json

import pandas as pd
from PyQt5 import QtGui, QtWidgets, QtPrintSupport, QtCore
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
import openpyxl


def loadCss(css="main.css"):
    if os.path.exists(f"./css/{css}"):
        with open(f"./css/{css}", "r") as style:
            stylesheet = style.read()
            style.close()
        return stylesheet
    else:
        os.makedirs("./css/")
        with open(f"./css/{css}", "w") as file:
            file.write("*{display:none}")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)
    prog = QtCore.pyqtSignal(str)

    def __init__(self, datas, percent):
        super(Worker, self).__init__()
        self.dbpath = loadpathsql("db.txt")
        self.datas = datas
        self.percent = percent
        self.runs = True

    def upload(self):
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        i = 0
        size = len(self.datas)

        for data in self.datas:
            if self.runs is True:
                stat = f"{i}/{size} articles importés"
                insert_data_re = "INSERT INTO posts(title,prix,qtt,vendu,image,barcode) VALUES(?,?,?,?,?,?)"
                cursor.execute(insert_data_re,
                               [data["designation"], int(data["prix"]), int(data["qtt"]), 0, "default.png",
                                data["codebar"]]
                               )
                connexion.commit()
                self.prog.emit(stat)
                i += 1
        cursor.close()
        connexion.close()
        self.finished.emit("import terminée")

class Home(QtWidgets.QMainWindow):
    def __init__(self):
        super(Home, self).__init__()
        # loader = loadUi("home.ui")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)

        self.win = loadUi("home.ui")
        self.posts = loadUi("posts.ui")
        self.savemodal = loadUi("save.ui")
        self.mois = loadUi("moi.ui")
        self.credit = loadUi("credit.ui")
        self.prints = loadUi("prints.ui")
        self.getModal = loadUi("getModal.ui")
        self.getModal.setModal(True)

        # self.win.setupUi(self)
        # set window icon
        self.banner = "icon.png"
        self.dbpath = loadpathsql("db.txt")

        self.win.setWindowIcon(QtGui.QIcon("./imgs/icon.ico"))
        self.win.icon.setPixmap(QtGui.QPixmap(f"./imgs/{self.banner}"))

        # Modify window
        self.getModal.setWindowFlag(Qt.FramelessWindowHint)
        self.getModal.setAttribute(Qt.WA_TranslucentBackground)
        self.getModal.setWindowTitle("recherche en cour...")

        # app datas
        self.get_app_infos()

        # general infos
        self.app_banner = ""
        self.loaduserinfos()

        # update app name
        self.win.appName.setText(self.app_name)
        self.win.setWindowTitle(self.app_name)
        # sidebar
        self.setIcons(self.win.goHome, "home2.svg")
        self.setIcons(self.win.goPanier, "upload-cloud.svg")
        self.setIcons(self.win.goUsers, "users.svg")
        self.setIcons(self.win.goStat, "database.svg")
        self.setIcons(self.win.goCog, "settings.svg")
        self.setIcons(self.win.iconf, "cld.png")
        # dynamic title
        # router
        self.win.goHome.clicked.connect(self.setHome)
        self.win.goPanier.clicked.connect(self.setPanier)
        self.win.goUsers.clicked.connect(self.setUsers)
        self.win.goStat.clicked.connect(self.setStats)
        self.win.goCog.clicked.connect(self.setGoCog)
        self.win.goinsolved.clicked.connect(self.setGoInsolved)
        # set posts in datasTable

        # disable btn visiblilit
        self.win.success.setVisible(False)
        self.win.error.setVisible(False)
        self.win.success_users.setVisible(False)
        self.win.error_users.setVisible(False)

        self.win.poststable.setColumnCount(4)
        self.win.poststable.setHorizontalHeaderLabels(("Nom du produit", "Prix", "En Stock", "Identifiant", "Vendre"))

        self.win.listall.setColumnCount(4)
        self.win.listall.setHorizontalHeaderLabels(("Nom du produit", "Prix", "En Stock", "Identifiant"))

        self.win.posts_select.setColumnCount(4)
        self.win.posts_select.setHorizontalHeaderLabels(("Nom du produit", "Prix", "Qt", "Total"))

        self.win.tabrapport.setColumnCount(3)
        self.win.tabrapport.setHorizontalHeaderLabels(("Nom du produit", "Prix", "Quantitee"))

        self.win.tabuser.setColumnCount(3)
        self.win.tabuser.setHorizontalHeaderLabels(("Nom d'usage", "Mot de passe", "Identifiant"))

        self.win.tabinsolved.setColumnCount(6)
        self.win.tabinsolved.setHorizontalHeaderLabels(("Nom", "Tel", "Cni", "Somme", "Localisation", "Identifiant"))

        self.win.poststable.setColumnWidth(0, 170)
        self.win.poststable.setColumnWidth(1, 150)
        self.win.poststable.setColumnWidth(2, 70)
        self.win.poststable.setColumnWidth(3, 70)
        self.win.poststable.setColumnWidth(4, 90)

        self.win.listall.setColumnWidth(0, 200)
        self.win.listall.setColumnWidth(1, 100)
        self.win.listall.setColumnWidth(2, 70)
        self.win.listall.setColumnWidth(3, 70)

        self.win.tabuser.setColumnWidth(0, 200)
        self.win.tabuser.setColumnWidth(1, 110)
        self.win.tabuser.setColumnWidth(2, 80)

        self.win.tabrapport.setColumnWidth(0, 200)
        self.win.tabrapport.setColumnWidth(1, 100)
        self.win.tabrapport.setColumnWidth(2, 60)

        # self.win.posts_select.setColumnWidth(0,160)

        self.loadvente()
        self.loaddata()
        self.loaduser()
        self.loadinsolved()
        self.sumdata()
        self.sumdatajour()
        self.setup_connexion()

        # setting page

        # settings params
        self.code = 1
        self.impres = 1
        self.head = 1
        self.sizep = 380
        self.curent_moi = time.localtime().tm_mon
        self.current_year = time.localtime().tm_year
        self.get_app_infos()

        # calling the filter bar
        self.search_filter()
        #self.win.search.textChanged.connect(self.keyPressEvent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter:
            print("Enter pressed ")

    def progress(self):
        global count

        if count > 100:
            self.getModal.close()

        count += 1

    def setup_connexion(self):
        self.win.post_save.clicked.connect(self.save_post)
        self.win.post_save.setIcon(QtGui.QIcon("./imgs/shopping-ba.svg"))

        self.win.refresh.setIcon(QtGui.QIcon("./imgs/refresh.png"))
        self.win.refresh.clicked.connect(self.ref)

        self.win.user_save.clicked.connect(self.add_user)
        self.win.user_save.setIcon(QtGui.QIcon("./imgs/user-plus (1).svg"))

        self.win.select_img.clicked.connect(self.select_banner)
        self.win.select_img.setIcon(QtGui.QIcon("./imgs/image.svg"))

        self.win.save_general.clicked.connect(self.save_general)
        self.win.save_general.setIcon(QtGui.QIcon("./imgs/save.svg"))

        self.win.add_selection.clicked.connect(self.add_selection)
        self.win.add_selection.setIcon(QtGui.QIcon("./imgs/plus-circle.svg"))

        self.win.addstock.clicked.connect(self.addstock)
        self.win.addstock.setIcon(QtGui.QIcon("./imgs/plus-circle.svg"))

        self.win.reset.clicked.connect(self.reset_selection)
        self.win.reset.setIcon(QtGui.QIcon("./imgs/trash.svg"))

        self.win.resetdef.clicked.connect(self.removepost)
        self.win.resetdef.setIcon(QtGui.QIcon("./imgs/trash.svg"))

        self.win.deluser.clicked.connect(self.deluser)
        self.win.deluser.setIcon(QtGui.QIcon("./imgs/trash.svg"))

        self.win.sale.clicked.connect(self.sale)
        self.win.sale.setIcon(QtGui.QIcon("./imgs/shop.svg"))

        self.win.closeSection.clicked.connect(self.endsection)
        self.win.closeSection.setIcon(QtGui.QIcon("./imgs/log-out.svg"))

        self.win.generate.clicked.connect(self.generaterapport)
        self.win.generate.setIcon(QtGui.QIcon("./imgs/file-text.svg"))

        self.win.saveconf.clicked.connect(self.saveconf)

        self.win.resetdb.clicked.connect(self.restore)

        self.win.chooseexcel.clicked.connect(self.chooseexcel)
        self.win.confirmimport.clicked.connect(self.biguploadaconf)

        self.win.solv.clicked.connect(self.solv)

        self.win.search_btn.setIcon(QtGui.QIcon("./imgs/search.svg"))
        self.win.layer.setPixmap(QtGui.QPixmap(f"./imgs/layers (1).svg").scaled(30, 30))
        self.win.list.setPixmap(QtGui.QPixmap(f"./imgs/list.svg").scaled(30, 30))
        self.win.icolist.setPixmap(QtGui.QPixmap(f"./imgs/list.svg").scaled(30, 30))
        self.win.icoadd.setPixmap(QtGui.QPixmap(f"./imgs/upload.svg").scaled(30, 30))
        self.win.icoadduser.setPixmap(QtGui.QPixmap(f"./imgs/user-check (1).svg").scaled(30, 30))
        self.win.icolistuser.setPixmap(QtGui.QPixmap(f"./imgs/list.svg").scaled(30, 30))
        self.win.icorapport.setPixmap(QtGui.QPixmap(f"./imgs/pie-chart.svg").scaled(30, 30))
        self.win.icoqtt.setPixmap(QtGui.QPixmap(f"./imgs/sb2.svg").scaled(60, 60))
        self.win.icosum.setPixmap(QtGui.QPixmap(f"./imgs/sc.svg").scaled(60, 60))

        # rapport connexion ui
        self.win.jour.clicked.connect(self.loadrapportday)
        self.win.mois.clicked.connect(self.loadrapportmois)

        self.win.ok.clicked.connect(self.filter)
        self.win.savepost.clicked.connect(self.savepost)

        self.win.this_mois.clicked.connect(self.mois_modal)

        self.savemodal.savetoexcel.clicked.connect(self.savetoexcel2)

        self.credit.update.clicked.connect(self.updatecredit)
        self.win.showupdate.clicked.connect(self.modalcredit)

        self.win.savepost.setIcon(QtGui.QIcon("./imgs/save.svg"))

        self.prints.direct.clicked.connect(self.directprint)
        self.prints.browser.clicked.connect(self.broserprint)

    def ref(self):
        self.loaddata("")

    def loaddata(self, filter=""):
        self.getModal.txt.setText(f"Chargement des articles...")

        self.getModal.setModal(True)
        self.getModal.show()

        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT * FROM posts WHERE title LIKE ? AND visible = ? ORDER BY id DESC"
        print("start fetch")
        cur.execute(sqlquery, ['%' + filter + '%', 1])
        datas = cur.fetchall()
        size = 50
        try:
            size = len(datas)
        except:
            pass
        self.win.poststable.setRowCount(size)
        self.win.listall.setRowCount(size)

        tablerow = 0
        for row in range(size):
            self.win.poststable.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.poststable.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.poststable.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            self.win.poststable.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f""))
            self.win.poststable.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(f""))
            self.win.poststable.setCellWidget(tablerow, 4, QtWidgets.QLabel(""))
            # list
            self.win.listall.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.listall.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.listall.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            self.win.listall.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f""))
            tablerow += 1

        tablerow = 0
        for row in datas:
            btn = QtWidgets.QPushButton("")
            btn.setObjectName("addcard")
            btn.setStyleSheet(loadCss())
            btn.setIcon(QtGui.QIcon("./imgs/shop.svg"))
            self.win.poststable.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.poststable.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
            if int(row[3]) - int(row[4]) == 0:
                self.win.poststable.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"Rupture de stock"))
            else:
                self.win.poststable.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{int(row[3]) - int(row[4])}"))
            self.win.poststable.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            self.win.poststable.setCellWidget(tablerow, 4, btn)

            # list
            self.win.listall.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.listall.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
            if int(row[3]) - int(row[4]) == 0:
                self.win.listall.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"Rupture de stock"))
            else:
                self.win.listall.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{int(row[3]) - int(row[4])}"))
            self.win.listall.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            tablerow += 1

            # self.getModal.setModal(False)
            # self.getModal.close()
            # self.getModal.close()

        self.timer.start(100)
        cur.close()
        connection.close()

    def loadvente(self):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ?"
        cur.execute(sqlquery, [0])
        datas = cur.fetchall()
        size = 10
        try:
            size = len(datas)
        except:
            pass
        self.win.posts_select.setRowCount(size)
        print(datas)
        tablerow = 0
        for row in range(size):
            self.win.posts_select.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.posts_select.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.posts_select.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            self.win.posts_select.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f""))
            tablerow += 1

        tablerow = 0
        for row in datas:
            self.win.posts_select.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.posts_select.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} F"))
            self.win.posts_select.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            self.win.posts_select.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(
                f"{'{:,}'.format(int(row[0]) * int(row[2]))} F"))
            tablerow += 1
        cur.close()
        connection.close()
        self.sumdata()

    def loaduserinfos(self):
        with open("./datas/user.json", "r") as file:
            self.userinfos = json.load(file)
            self.win.appUser.setText(
                f"<html><head/><body><p align='right'>{self.userinfos['pseudo']}</p></body></html>")
            self.win.goPanier.setVisible(int(self.userinfos['role']))
            self.win.goUsers.setVisible(int(self.userinfos['role']))
            # self.win.goStat.setVisible(int(self.userinfos['role']))
            self.win.goCog.setVisible(int(self.userinfos['role']))

    def loaduser(self, filter=""):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT * FROM users WHERE pseudo LIKE ? ORDER BY id DESC"
        print("start fetch")
        datas = cur.execute(sqlquery, ['%' + filter + '%'])
        size = 10
        try:
            size = len(datas)
        except:
            pass
        self.win.tabuser.setRowCount(size)

        tablerow = 0
        for row in range(size):
            self.win.tabuser.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.tabuser.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.tabuser.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            # list
            tablerow += 1
        tablerow = 0
        for row in datas:
            self.win.tabuser.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.tabuser.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{row[5]}"))
            self.win.tabuser.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            # list
            tablerow += 1

    def loadinsolved(self, filter=""):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT * FROM insolved WHERE solved LIKE ? ORDER BY id DESC"
        cur.execute(sqlquery, [0])
        datas = cur.fetchall()
        size = 10
        try:
            size = len(datas)
        except:
            pass
        self.win.tabinsolved.setRowCount(size)

        tablerow = 0
        for row in range(size):
            self.win.tabinsolved.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.tabinsolved.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.tabinsolved.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            self.win.tabinsolved.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f""))
            self.win.tabinsolved.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(f""))
            self.win.tabinsolved.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(f""))
            # list
            tablerow += 1
        tablerow = 0
        for row in datas:
            self.win.tabinsolved.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.credit.nom.setText(f"{row[1]}")
            self.win.tabinsolved.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{row[2]}"))
            self.credit.tel.setText(f"{row[2]}")
            self.win.tabinsolved.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[4]}"))
            self.credit.cni.setText(f"{row[4]}")
            self.win.tabinsolved.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(f"{row[7]}"))
            self.credit.somme.setValue(int(row[7]))
            self.win.tabinsolved.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(f"{row[3]}"))
            self.credit.localisation.setText(f"{row[3]}")
            self.win.tabinsolved.setItem(tablerow, 5, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            # list
            tablerow += 1

    def loadrapportday(self, filter=""):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mday}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.jour = ? AND vente.mois = ? AND vente.an = ?"
        cur.execute(sqlquery, [1, jour, self.curent_moi, self.current_year])
        datas = cur.fetchall()
        size = 50
        try:
            size = len(datas)
        except:
            pass
        self.win.tabrapport.setRowCount(size)
        print(datas)
        tablerow = 0
        for row in range(size):
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            tablerow += 1

        tablerow = 0
        for row in datas:
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            tablerow += 1
            print(row[0])
        cur.close()
        connection.close()
        self.sumdatajour()
        self.win.current.setText("Jour")

    def loadrapportmois(self, filter=""):
        self.curent_moi = time.localtime().tm_mon
        self.win.this_mois.setText(self.getMois(self.curent_moi))
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mon}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.mois = ? AND vente.an = ?"
        cur.execute(sqlquery, [1, self.curent_moi, self.current_year])
        datas = cur.fetchall()
        size = 50
        try:
            size = len(datas)
        except:
            pass
        self.win.tabrapport.setRowCount(size)
        print(datas)
        tablerow = 0
        for row in range(size):
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            tablerow += 1

        tablerow = 0
        for row in datas:
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            tablerow += 1
            print(row[0])
        cur.close()
        connection.close()
        self.sumdatamois()
        self.win.current.setText("Mois")

    def loadrapportmoisfilt(self, filter=""):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mon}'
        year = time.localtime().tm_year
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.mois = ? AND vente.an = ?"
        cur.execute(sqlquery, [1, filter, self.current_year])
        datas = cur.fetchall()
        size = 50
        try:
            size = len(datas)
        except:
            pass
        self.win.tabrapport.setRowCount(size)
        print(datas)
        tablerow = 0
        for row in range(size):
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
            tablerow += 1

        tablerow = 0
        for row in datas:
            self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
            self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
            self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
            tablerow += 1
            print(row[0])
        cur.close()
        connection.close()
        self.sumdatamoisfilt()
        self.win.current.setText("Mois")

    # app
    def setIcons(self, elem, icon='default.png'):
        try:
            elem.setIcon(QtGui.QIcon(f"./imgs/{icon}"))
        except:
            elem.setPixmap(QtGui.QPixmap(f"./imgs/{icon}").scaled(30, 30))

    def setPage(self, page, title, ico):
        # self.loadvente()
        # self.loaddata()
        self.setIcons(self.win.iconf, icon=f"{ico}")
        self.win.titlef.setText(title)
        self.win.stackedWidget.setCurrentWidget(page)
        self.win.setWindowTitle(title)
        self.win.success_update.setVisible(False)

    # pages
    def setHome(self):
        self.loadvente()
        # self.loaddata()
        self.setPage(self.win.home, "Store", "pn.png")

    def setPanier(self):
        self.win.success.setVisible(False)
        self.win.error.setVisible(False)
        self.setPage(self.win.addproduct, "Televerser un produit", "add.png")

    def setUsers(self):
        self.loaduser()
        self.setPage(self.win.users, "Utilisateurs", "ad.png")
        self.win.success_users.setVisible(False)
        self.win.error_users.setVisible(False)

    def setStats(self):
        mois = time.localtime().tm_mon
        self.loadrapportday()
        self.sumdatajour()
        self.setPage(self.win.stats, "Statistique", "trending-up.svg")
        self.win.this_mois.setText(self.getMois(mois))

    def setGoCog(self):
        self.setPage(self.win.settings, "Paramêtre", "setting.png")

    def setGoInsolved(self):
        self.loadinsolved()
        self.setPage(self.win.page_insolved, "Insolvables", "send.png")

    @staticmethod
    def closeWindow(self):
        exit(0)

    # page_add_post
    def save_post(self):

        self.win.success.setVisible(False)
        self.win.error.setVisible(False)
        # get data
        titre = self.win.title_post.text()
        qtt = self.win.qtt_post.text()
        price = self.win.price_post.text()
        barcode = self.win.barcode.text().lower()
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()

        def verifycode():
            if len(barcode) >= 3:
                re = f"SELECT * FROM posts WHERE barcode = ?"
                cur.execute(re, [barcode])
                codes = cur.fetchall()
                nbcode = 0
                for code in codes:
                    nbcode += 1
                if nbcode >= 1:
                    return True
                else:
                    return False
            else:
                return False

        if not verifycode():
            if titre == "" or qtt == "" or price == "":
                self.win.error.setVisible(True)
                print("error")
                return False
            else:
                print("sauvegarde..")

                # insert in database
                print("...av")
                insert_data_re = "INSERT INTO posts(title,prix,qtt,vendu,image,barcode) VALUES(?,?,?,?,?,?)"
                cur.execute(insert_data_re, [titre, int(price), int(qtt), 0, "default.png", barcode])
                print("...ap")
                self.win.success.setVisible(True)
                # renitialisation des champs
                self.win.title_post.setText("")
                self.win.qtt_post.setValue(1)
                self.win.price_post.setValue(100)
                self.win.barcode.setText("")
                connection.commit()
        else:
            self.showbox(content="Ce produit existe déja en base de donnée")
        cur.close()
        connection.close()
        print(f'{titre, qtt, price}')
        self.loaddata()

    # page_manage_users
    def add_user(self):
        self.win.success_users.setVisible(False)
        self.win.error_users.setVisible(False)
        # get data
        user_name = self.win.user_name.text()
        password = self.win.password.text()
        try:
            if user_name == "" or password == '':
                self.win.error_users.setVisible(True)
                print("error")
                return False
            else:
                connection = sqlite3.connect(self.dbpath)
                cur = connection.cursor()

                # insert in database
                insert_data_re = "INSERT INTO users(pseudo,name,avatar,role,password) VALUES(?,?,?,?,?)"
                cur.execute(insert_data_re, [user_name, "", "avatar.png", 0, password])
                print("...ap")
                self.win.success_users.setVisible(True)
                self.win.user_name.setText("")
                self.win.password.setText("")
                connection.commit()
                connection.close()
        except:
            self.win.error_users.setVisible(True)
        self.loaduser()

    # page_settings
    def select_banner(self):
        select = QtWidgets.QFileDialog.getOpenFileName(filter="*.jpg;*.png;*.ico;*.svg")
        file = select[0]

        if file == '':
            file = self.file
            print("aucune image selectionnée !")
        else:
            self.win.banner_up.setPixmap(QtGui.QPixmap(file).scaled(200, 400, QtCore.Qt.KeepAspectRatio))
            self.ban = file

    def saveconf(self):
        imprim = self.win.imprim.isChecked()
        code = self.win.code.isChecked()
        header = self.win.header.isChecked()
        print(code)
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        cursor.execute(f"UPDATE settings SET impression = {imprim}, codebar = {code}, header = {header} WHERE id = ?",
                       [1])
        connexion.commit()
        cursor.close()
        connexion.close()
        self.get_app_infos()
        self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="success",
                     content="Modifications prisent en compte")

    def save_general(self):
        try:
            # general
            new_app_name = self.win.entreprise.text()
            new_banner = self.ban
            new_banner_name = new_banner.split("/")[-1]

            # upload_files
            with  open(new_banner, "rb") as filer:
                with open(f"./adm/{new_banner_name}", "wb") as file:
                    data = filer.read()
                    file.write(data)

            # Persist in database
            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()

            insert_data_re = "UPDATE settings SET app_name = ?"
            cursor.execute(insert_data_re, [new_app_name])

            insert_data_re = "UPDATE settings SET app_banner = ?"
            cursor.execute(insert_data_re, [new_banner_name])

            connexion.commit()

            cursor.close()
            connexion.close()

            self.win.success_update.setVisible(True)
            self.get_app_infos()
        except:
            # Persist in database
            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()

            insert_data_re = "UPDATE settings SET app_name = ?"
            cursor.execute(insert_data_re, [new_app_name])

            connexion.commit()

            cursor.close()
            connexion.close()

            self.win.success_update.setVisible(True)
            self.get_app_infos()

    def get_app_infos(self):

        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()

        requetes_infos = "SELECT * FROM settings ORDER BY id DESC LIMIT 1"

        for data in cursor.execute(requetes_infos):
            self.app_name = data[1]
            self.app_banner = data[2]
            ban = data[2]
            impression = data[3]
            codebar = data[4]
            header = data[5]

            self.win.appName.setText(self.app_name)
            self.win.imprim.setChecked(int(impression))
            self.win.code.setChecked(int(codebar))
            self.win.header.setChecked(int(header))
            self.code = codebar
            self.impres = impression
            self.head = header

            self.win.barcode.setVisible(self.code)
            self.win.labelcode.setVisible(self.code)

            self.banner = self.app_banner
            self.win.entreprise.setText(self.app_name)
            self.win.banner_up.setPixmap(QtGui.QPixmap(f"./adm/{ban}").scaled(200, 400, QtCore.Qt.KeepAspectRatio))
            self.file = self.app_banner
            print(self.app_name)

        cursor.close()
        connexion.close()

    def search_filter(self):

        def filter():
            search_bar_text = self.win.search.text()
            self.loaddata(filter=search_bar_text)

        def load():
            pass

        self.win.search.textChanged.connect(load)
        self.win.search_btn.clicked.connect(filter);

    # page Manage posts
    def add_selection(self):
        id = self.win.id.text().lower()
        qtt = self.win.qtt.text()

        if id == "":
            print("Entrez un identifiant")
            self.showbox(content="Veillez entrer un identifiant valide !")
        elif qtt == "":
            print("Entrez une quantitée")
            self.showbox(content="Veillez entrer une quantité")
        else:
            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()

            get_id_re = "SELECT * FROM posts WHERE id = ?"

            id_number = 0;
            in_stock = 0;
            vendu = 0;

            for identifiant in cursor.execute(get_id_re, [id]):
                id_number += 1
                in_stock = int(identifiant[3]) - int(identifiant[4])
                vendu = identifiant[4]

            if id_number <= 0:
                get_code_re = "SELECT * FROM posts WHERE barcode = ?"
                cursor.execute(get_code_re, [id])
                data = cursor.fetchall()
                for code in data:
                    id = code[0]
                    id_number += 1
                    in_stock = int(code[3]) - int(code[4])
                    vendu = code[4]

            cursor.close()
            connexion.close()

            if id_number <= 0:
                print("Produit introuvable")
                self.showbox(content="Ce produit n'existe pas!")
            elif int(qtt) <= int(in_stock):
                self.ftime = st = f'{time.localtime().tm_mday}/{time.localtime().tm_mon}/{time.localtime().tm_year}/{time.localtime().tm_hour}/{time.localtime().tm_min} '
                jour = f'{time.localtime().tm_mday}'
                mois = f'{time.localtime().tm_mon}'
                connexion2 = sqlite3.connect(self.dbpath)
                cursor2 = connexion2.cursor()
                insert_vente_re = "INSERT INTO vente(post_id, user_id, qtt, validate, created_at, jour, mois, an) VALUES(?,?,?,?,?,?,?,?)"
                update_post_re = "UPDATE posts SET vendu = ?"
                cursor2.execute(insert_vente_re, [id, 1, qtt, 0, self.ftime, jour, mois, time.localtime().tm_year])
                connexion2.commit()
                cursor2.close()
                connexion2.close()
                print("Produit ajouté avec success :) ")
                self.win.id.setText("")
                self.win.qtt.setText("")
                self.loadvente()
            else:
                print("Entrez une quantitée convenable !")
                self.showbox(content="Stock restant insuffisant !")

    def reset_selection(self):
        self.loadvente()

        connexion3 = sqlite3.connect(self.dbpath)
        cursor3 = connexion3.cursor()
        delete_selection_re = "DELETE FROM vente WHERE validate = ?"
        cursor3.execute(delete_selection_re, [0])
        connexion3.commit()

        self.loadvente()

        cursor3.close()
        connexion3.close()

        self.loadvente()

    def sale(self):
        # PRINT
        if self.impres:
            if self.win.posts_select.rowCount() >= 1:
                self.prints.setModal(True)
                self.prints.setWindowTitle("choix d'impression")
                self.prints.show()

            else:
                self.showbox(content="Aucun contenu à vendre ! ")
        else:
            self.complete()

    def complete(self):
        # insolved
        insolved = self.win.insolved.isChecked()
        if insolved:
            (name, nameok) = self.showdialog(title="Nom", msg="Entrez le nom du client")
            (phone, phoneok) = self.showdialog(title="phone", msg="Entrez le numero de telephone du client")
            (localisation, localisationok) = self.showdialog(title="habitation",
                                                             msg="Entrez le lieu d'habitat du client ")
            (cni, cniok) = self.showdialog(title="CNI", msg="Entrez le numero de la cni du client")
            con = sqlite3.connect(self.dbpath)
            cu = con.cursor()
            cu.execute("SELECT * FROM vente WHERE validate NOT LIKE ? LIMIT 100", [1])
            datas = cu.fetchall()
            ids = []
            somme = 0
            for id in datas:
                ids.append(id[1])
                cu.execute("SELECT prix FROM posts WHERE id = ?", [id[1]])
                prices = cu.fetchall()
                for price in prices:
                    somme += int(price[0])
            cu.execute(
                "INSERT INTO insolved(name, phone, lacalisation, cni, solved, posts_ids, somme) values(?,?,?,?,?,?,?)",
                [name, phone, localisation, cni, 0, str(f"{ids}"), somme])
            con.commit()
            cu.close()
            con.close()
            self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="La client à bien été enregistré",
                         content="La client à bien été enregistré")
            self.win.insolved.setChecked(False)

            print(f"name: {name};  nameok:{nameok} ")

        # validate vente
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()

        # update post
        id = []
        in_stock = []
        qt = []
        cursor.execute("SELECT * FROM vente WHERE validate NOT LIKE ? LIMIT 100", [1])
        datas = cursor.fetchall()
        for identifiant in datas:
            print(f"=============================================={identifiant}===================================")
            print(f"=================================================================================")
            post_id = identifiant[1]
            qtt = identifiant[3]
            id.append(post_id)
            qt.append(qtt)
            get_in_stock_re = f"SELECT * FROM posts WHERE id = ?"
            for stock in cursor.execute(get_in_stock_re, [post_id]):
                in_stock.append(int(stock[4]))
        i = 0
        for num in range(len(id)):
            update_post_re = f"UPDATE posts SET vendu = {int(in_stock[i] + int(qt[i]))} WHERE id = ?"
            cursor.execute(update_post_re, [id[i]])
            connexion.commit()

            self.loadvente()
            self.loaddata()
            i += 1

        # update validate
        update_vente_re = "UPDATE vente SET validate = 1 WHERE validate = ?"
        cursor.execute(update_vente_re, [0])
        connexion.commit()

        cursor.close()
        connexion.close()
        self.loadvente()
        self.loaddata()

        print("Vendus avec success !")

        # user functions

    def endsection(self):
        mainWindow.win.hide()
        exit(0)

        # utils functions

    def showbox(self, msgtype=QtWidgets.QMessageBox.Warning, title="erreur", content="erreur de traitement"):
        msg_box = QtWidgets.QMessageBox(msgtype, title, content)
        msg_box.exec()

    def sumdata(self):
        self.curent_moi = time.localtime().tm_mon
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ?"
        datas = cur.execute(sqlquery, [0])

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        self.win.qt.setText(f"{qtt}")
        self.win.ptt.setText(f"{'{:,}'.format(ptt)} FCFA")

        cur.close()
        connection.close()

    def sumdatap(self):
        self.curent_moi = time.localtime().tm_mon
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ?"
        datas = cur.execute(sqlquery, [0])

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        cur.close()
        connection.close()
        return qtt, ptt

    def sumdatajour(self):
        self.curent_moi = time.localtime().tm_mon
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mday}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.jour = ? AND vente.an = ?"
        datas = cur.execute(sqlquery, [1, jour, time.localtime().tm_year])

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        self.win.qtt_2.setText(f"+{qtt}")
        self.win.ptt_2.setText(f"{'{:,}'.format(ptt)} FCFA")

        cur.close()
        connection.close()

    def sumdatafilter(self):
        du = int(self.win.du.text())
        au = int(self.win.au.text())
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mday}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ?  AND vente.jour >= ? AND vente.jour <= ? AND vente.mois = ? AND vente.an = ?"
        cur.execute(sqlquery, [1, du, au, self.curent_moi, time.localtime().tm_year])
        datas = cur.fetchall()

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        self.win.qtt_2.setText(f"+{qtt}")
        self.win.ptt_2.setText(f"{'{:,}'.format(ptt)} FCFA")

        cur.close()
        connection.close()

    def sumdatamois(self):
        self.curent_moi = time.localtime().tm_mon
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mon}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.mois = ? AND vente.an = ?"
        datas = cur.execute(sqlquery, [1, jour, time.localtime().tm_year])

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        self.win.qtt_2.setText(f"+{qtt}")
        self.win.ptt_2.setText(f"{'{:,}'.format(ptt)} FCFA")

        cur.close()
        connection.close()

    def sumdatamoisfilt(self):
        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        jour = f'{time.localtime().tm_mon}'
        sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ? AND vente.mois = ? AND vente.an = ?"
        datas = cur.execute(sqlquery, [1, self.curent_moi, time.localtime().tm_year])

        qtt = 0
        ptt = 0
        i = 0
        for row in datas:
            qtt += int(row[0])
            lqtt = int(row[0])
            ptt += (lqtt * int(row[2]))
            print(f"index{i}:{row[0]} ")
            print(f"index{i}:{row[1]} ")
            i += 1

        self.win.qtt_2.setText(f"+{qtt}")
        self.win.ptt_2.setText(f"{'{:,}'.format(ptt)} FCFA")

        cur.close()
        connection.close()

    # page televersement
    def removepost(self):
        id = self.win.id_2.text()
        if id == "":
            self.showbox(content="Entrez un identifiant valide")
        else:
            if self.verifyid(id) == 1:
                self.deleteid(id)
                self.loaddata()
            else:
                self.showbox(content="Produit introuvale")

    def verifyid(self, idp):
        i = 0;
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        for id in cursor.execute("SELECT * FROM posts WHERE id = ? AND visible = ?", [idp, 1]):
            i += 1
        cursor.close()
        connexion.close()
        if i == 0:
            return 0
        else:
            return 1

    def updateqtt(self, idp, qtt):
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        dbqtt = 0;
        dbvendu = 0;
        for dbd in cursor.execute("SELECT qtt,vendu FROM posts WHERE id = ?", [idp]):
            dbqtt += int(dbd[0])
            dbvendu += int(dbd[1])
        fdb = dbqtt - dbvendu
        cursor.execute(f"UPDATE posts SET qtt = {qtt + fdb}, vendu = {0} WHERE id = ? ", [idp])
        connexion.commit()
        cursor.close()
        connexion.close()
        self.loaddata()

    def deleteid(self, idp):
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        cursor.execute(f"UPDATE posts set visible = {0}  WHERE id = ?", [idp])
        connexion.commit()
        cursor.close()
        connexion.close()

    def addstock(self):
        id = self.win.id_2.text()

        if self.verifyid(id):
            self.modal = self.posts
            self.modal.setModal(True)
            self.modal.setWindowTitle("Mettre à jour un produit")
            self.modal.iconedit.setPixmap(QtGui.QPixmap("./imgs/shopping-ba.svg").scaled(40, 40))
            add = self.modal.addst
            sub = self.modal.subst
            add.setChecked(True)
            sub.setChecked(False)

            post = self.getpost(id)

            self.modal.title.setText(post[0][1])

            self.modal.product.setText(post[0][1])
            self.modal.price.setValue(post[0][2])
            self.modal.qtt.setValue(0)
            self.modal.codebar.setText(post[0][6])
            self.qtindb = int(post[0][3])
            self.venduindb = int(post[0][4])

            self.modal.addstock.clicked.connect(self.updatepost)
            self.modal.exec()
            self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="success",
                         content=f"Mise à jour reussis !")
        else:
            self.showbox(content="Entrez un identifiant valide")

    def updatepost(self):
        try:
            add = self.modal.addst
            sub = self.modal.subst
            id = self.win.id_2.text()
            title = self.posts.product.text()
            price = self.posts.price.text()
            qtt = int(self.posts.qtt.text())
            codebar = self.posts.codebar.text()
            newqtt = qtt + self.venduindb
            if add.isChecked():
                newqtt = self.qtindb + qtt
            elif sub.isChecked():
                newqtt = self.qtindb - qtt

            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()
            cursor.execute(f"UPDATE posts set title = ?, prix = ?, qtt = ?, barcode = ? WHERE id = {id}",
                           [title, price, newqtt, codebar])
            connexion.commit()
            cursor.close()
            connexion.cursor()
            self.loaddata()
            self.posts.title.setText(title)
            self.modal.close()
            return True
        except:
            self.showbox(content="Error")
            return False

    def getpost(self, id):
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        cursor.execute("SELECT * FROM posts WHERE id like ?", [id])
        data = cursor.fetchall()
        cursor.close()
        connexion.close()
        print(data)
        return data

    def showdialog(self, title="Quantitée", msg="Entrez la quantitée à rechargé"):
        text, ok = QtWidgets.QInputDialog.getText(self, title, msg)
        return (text, ok)

    # page manage users
    def deluser(self):
        id = self.win.id_3.text()
        if id == '':
            self.showbox(content="Entrez un identifiant !")
        else:
            if self.verifyuser(id) == 1:
                self.removeuser(id)
                self.loaduser()
                self.win.id_3.setText("")
            else:
                self.showbox(content="Cet utilisateur n'existe pas")

    def removeuser(self, idp):
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", [idp])
        connexion.commit()
        cursor.close()
        connexion.close()

    def verifyuser(self, idp):
        i = 0;
        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        for id in cursor.execute("SELECT * FROM users WHERE id = ?", [idp]):
            i += 1
        cursor.close()
        connexion.close()
        if i == 0:
            return 0
        else:
            return 1

    # page rapport
    def exporttoexcel(self, path):

        jour = f"Rapport.du.{time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year}"
        columHeaders = []
        t = self.win.tabrapport
        ta = QtWidgets.QTableWidget
        for j in range(t.model().columnCount()):
            columHeaders.append(t.horizontalHeaderItem(j).text())

        df = pd.DataFrame(columns=columHeaders)

        for row in range(t.rowCount()):
            for col in range(t.columnCount()):
                df.at[row, columHeaders[col]] = t.item(row, col).text()

        df.to_csv(f'{path}/{jour}.csv', index=False)

    def exportpoststoexcel(self, path):
        jour = f"{time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year}({time.localtime().tm_hour}-{time.localtime().tm_min}-{time.localtime().tm_sec})"
        columHeaders = ["designation", "prix", "qtt", "codebar"]
        t = self.win.tabrapport
        ta = QtWidgets.QTableWidget

        df = pd.DataFrame(columns=columHeaders)

        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()
        cursor.execute("SELECT title, prix, qtt, barcode FROM posts")
        datas = cursor.fetchall()
        cursor.execute("SELECT vendu FROM posts")
        vendus = cursor.fetchall()
        i = 0
        x = 0
        init = 0
        for row in datas:
            y = 0
            for ro in row:
                if y == 2:
                    try:
                        df.at[i, columHeaders[y]] = int(ro) - int(vendus[x][init])
                    except:
                        df.at[i, columHeaders[y]] = int(ro) - int(vendus[0][int(x) - 1])
                else:
                    df.at[i, columHeaders[y]] = ro

                y += 1
            i += 1
            x += 1
        cursor.close()
        connexion.close()
        df.to_html(f'{path}/produits{jour}.html', index=False)
        df.to_excel(f'{path}/produits{jour}.xlsx', index=False)

    def generaterapport(self):
        try:
            fold = QtWidgets.QFileDialog.getExistingDirectory()
            self.exporttoexcel(fold)
            self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="Operation terminée ",
                         content=f"Votre fichier à été exporté dans le dossier {fold}")
        except:
            print("Operation annulée")

    # Additional settings
    def chooseexcel(self):
        select = QtWidgets.QFileDialog.getOpenFileName(filter="*.xlsx;*.xlsm;*.xltx;*.xltm")
        self.file = select[0]

        if self.file == '':
            self.showbox(content="Aucun fichier selectionné !")
        else:
            self.excel = self.file
            self.win.chooseexcel.setText(os.path.basename(self.excel))
            self.win.nameexcel.setText(self.excel)

    def endUpload(self, param):
        # self.getModal.close()
        self.IHprocess.quit()
        self.win.chooseexcel.setText("uploader une autre liste...")
        self.win.nameexcel.setText("")

        self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="upload reussis",
                     content="Vos produits ont été correctement importés !")
        self.win.pc.setText("Importer les produits via un fichier excel")
        self.excel = ""
        self.loaddata()

    def progUpload(self, status):
         self.prg_dialog.setWindowTitle(status)
         self.prg_dialog.setValue(self.prg_dialog.value() + 1)

    def start(self):
        self.work.upload()

    def biguploadaconf(self):

        print("upload en cour...")

        if len(self.excel) >= 1:
            self.win.pc.setText("Importation en cour...")
            datas = self.bigupload(self.excel)
            self.size_datas = datas

            self.IHprocess = QtCore.QThread(self)
            self.work = Worker(datas, "")
            self.work.moveToThread(self.IHprocess)
            self.IHprocess.started.connect(self.start)
            self.work.finished.connect(self.endUpload)
            self.work.prog.connect(self.progUpload)
            self.IHprocess.start()

            self.first = 1

            self.prg_dialog = QtWidgets.QProgressDialog("Importation des articles", "Stopper l'importation", self.first, len(datas))
            self.prg_dialog.setModal(True)
            self.prg_dialog.canceled.connect(self.abord_process)
            self.prg_dialog.resize(1200/2, 1920/8)
            self.prg_dialog.setWindowTitle("Importation...")
            self.prg_dialog.show()

            """
            size = len(datas)
            i = 1

            self.progress()
            """
            """except:
                self.showbox(
                    content="Une erreur c'est produit l'ors de l'importation de vos produits: "
                            "-verifier que le format de redaction à eté respecte;"
                            "-Verifier si votre fichier n'est pas endomgé  ")"""
        else:
            self.showbox(
                content="Veillez choisir un fichier !")

    def abord_process(self):
        self.IHprocess.quit()
        self.work.runs = False

    def bigupload(self, excelfile):

        file = excelfile

        if os.path.exists(file):
            excel = openpyxl.load_workbook(file)
            sheet = excel.active
            rows = sheet.rows
            header = [cell.value for cell in next(rows)]

            all_datas = []

            for row in rows:
                data = {}
                for title, cell in zip(header, row):
                    data[title] = cell.value
                all_datas.append(data)

            return all_datas

    def restore(self):
        conf = True
        if conf:
            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()

            cursor.execute("DELETE FROM posts", [])
            connexion.commit()

            cursor.execute("DELETE FROM users WHERE id NOT LIKE ?", [1])
            connexion.commit()

            cursor.execute("DELETE FROM vente", [])
            connexion.commit()

            cursor.execute("DELETE FROM insolved", [])
            connexion.commit()

            cursor.close()
            connexion.close()

            self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="Restoration reusis",
                         content="Vos statistique de vente, produit ont été restoré !")

    # print options
    def handlePrint(self):
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.handlePaintRequest(dialog.printer())

    def handlePreview(self):
        dialog = QtPrintSupport.QPrintPreviewDialog()
        dialog.paintRequested.connect(self.handlePaintRequest)
        dialog.exec_()

    def handlePaintRequest(self, printer):
        document = QtGui.QTextDocument()
        document.adjustSize()
        table_format = QtGui.QTextTableFormat()
        table_format.setHeaderRowCount(1)
        table_format.setWidth(self.sizep)
        cursor = QtGui.QTextCursor(document)
        if int(self.head):
            cursor.insertHtml(f"<img src='./adm/{self.banner}'/>")
        cursor.insertBlock()
        table = cursor.insertTable(
            self.win.posts_select.rowCount() + 1, self.win.posts_select.columnCount(), table_format)
        heading = ("Designation", "Prix unique", "Quantitée", "Prix Total")

        for head in heading:
            cursor.insertHtml(f"<b>{head}</b>")
            cursor.movePosition(QtGui.QTextCursor.NextCell)
        for row in range(table.rows() - 1):
            for col in range(table.columns()):
                cursor.insertText(self.win.posts_select.item(row, col).text())
                cursor.movePosition(QtGui.QTextCursor.NextCell)
        table.appendRows(1)
        cursor = table.cellAt(self.win.posts_select.rowCount() + 1, 0).lastCursorPosition()
        cursor.insertHtml(f"<b>Total</b>")
        cursor = table.cellAt(self.win.posts_select.rowCount() + 1, 3).lastCursorPosition()
        cursor.insertHtml(f"<b>{'{:,}'.format(self.sumdatap()[1])} FCFA</b>")

        document.end()
        document.print_(printer)

    # solf page
    def solv(self):
        solver = self.win.solver.text()
        if solver == "":
            self.showbox(content="Entrez un identifiant valide !")
        else:
            con = sqlite3.connect(self.dbpath)
            cur = con.cursor()
            cur.execute("UPDATE insolved SET solved = 1 WHERE id = ?", [int(solver)])
            con.commit()
            con.close()
            self.loadinsolved()
            self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="Success", content="Requête prise en compte ")
            self.win.solver.setText("")

    # FILTER CONF
    def filter(self):
        du = int(self.win.du.text())
        au = int(self.win.au.text())

        if au >= du:
            connexion = sqlite3.connect(self.dbpath)
            cursor = connexion.cursor()
            sqlquery = f"SELECT vente.qtt, posts.title, posts.prix FROM vente LEFT JOIN posts ON vente.post_id = posts.id WHERE vente.validate = ?  AND vente.jour >= ? AND vente.jour <= ? AND vente.mois = ?"
            cursor.execute(sqlquery, [1, du, au, self.curent_moi])
            datas = cursor.fetchall()
            size = 50
            try:
                size = len(datas)
            except:
                pass
            self.win.tabrapport.setRowCount(size)
            print(datas)
            tablerow = 0
            for row in range(size):
                self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f""))
                self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f""))
                self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f""))
                tablerow += 1

            tablerow = 0
            for row in datas:
                self.win.tabrapport.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(f"{row[1]}"))
                self.win.tabrapport.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(f"{'{:,}'.format(row[2])} FCFA"))
                self.win.tabrapport.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(f"{row[0]}"))
                tablerow += 1
                print(row[0])
            cursor.close()
            connexion.close()
            self.sumdatafilter()
            self.win.current.setText(f"{du}-{au}")
        else:
            self.showbox(content="Date invalide !")

    def savetoexcel2(self):
        fold = QtWidgets.QFileDialog.getExistingDirectory()
        self.exportpoststoexcel(fold)
        self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="Operation terminée ",
                     content=f"Votre fichier à été exporté dans le dossier {fold}")
        self.modal2.close()
        return True

    def savepost(self):

        self.modal2 = self.savemodal
        self.modal2.setModal(True)
        self.modal2.setWindowTitle("sauvegarde...")
        self.modal2.show()

    def getMois(self, mois):
        mois_tables = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet", "Aout", "Septembre", "Octobre",
                       "Novembre", "Decembre"]
        mois = mois - 1
        if mois <= 12:
            return mois_tables[mois]

    def mois_modal(self):
        mois = self.mois
        mois.setModal(True)

        def filter_moi():
            moi = int(mois.moi.text())
            self.filter_moi(moi)
            mois.close()

        mois.filt.clicked.connect(filter_moi)
        mois.show()

    def filter_moi(self, moi):
        print(moi)
        self.curent_moi = moi
        self.win.this_mois.setText(self.getMois(moi))
        self.loadrapportmoisfilt(filter=moi)

    def modalcredit(self):
        self.credit.setWindowTitle("Mise à jour")
        id = self.win.solver.text()

        connection = sqlite3.connect(self.dbpath)
        cur = connection.cursor()
        sqlquery = f"SELECT * FROM insolved WHERE solved LIKE ? AND id = ? LIMIT 1"
        cur.execute(sqlquery, [0, int(id)])
        datas = cur.fetchall()
        size = len(datas)
        for row in datas:
            self.credit.nom.setText(f"{row[1]}")
            self.credit.tel.setText(f"{row[2]}")
            self.credit.cni.setText(f"{row[4]}")
            self.credit.somme.setValue(int(row[7]))
            self.credit.localisation.setText(f"{row[3]}")

        if size == 0:
            self.showbox(content="Identifiant invalide")
        else:
            self.credit.setModal(True)
            self.credit.show()

    def updatecredit(self):
        id = self.win.solver.text()
        nom = self.credit.nom.text()
        tel = self.credit.tel.text()
        cni = self.credit.cni.text()
        somme = self.credit.somme.value()
        localisation = self.credit.localisation.text()

        connexion = sqlite3.connect(self.dbpath)
        cursor = connexion.cursor()

        cursor.execute(f"UPDATE insolved set name = ?, phone = ?, lacalisation = ?, cni = ?, somme = ? WHERE id = {id}",
                       [nom, tel, localisation, cni, somme])

        connexion.commit()
        cursor.close()
        connexion.close()
        self.credit.close()

        self.loadinsolved()
        self.showbox(msgtype=QtWidgets.QMessageBox.Information, title="success !", content="Mise à jours reussis !")

    def printtoweb(self, path=os.path.join("\\", "Users", os.getlogin(), "Desktop")):
        jour = f"facture.{time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year}-{time.localtime().tm_hour}.{time.localtime().tm_min}.{time.localtime().tm_sec}"
        columHeaders = []

        t = self.win.posts_select
        ta = QtWidgets.QTableWidget
        for j in range(t.model().columnCount()):
            columHeaders.append(t.horizontalHeaderItem(j).text())

        df = pd.DataFrame(columns=columHeaders)

        for row in range(t.rowCount()):
            for col in range(t.columnCount()):
                df.at[row, columHeaders[col]] = t.item(row, col).text()

        if not os.path.exists(os.path.join(path, "facture")):
            os.makedirs(os.path.join(path, "facture"))

        fpath = os.path.join(path, 'facture', f'{jour}')

        df.to_excel(f"{fpath}.xlsx", index=False)
        df.to_html(f"{fpath}.html", index=False)

        with open(f"{fpath}.html", "a") as fact:
            fact.write(f"""
                <table class='tnb'>
                  <td colspan="2">Total:</td>
                  <td></td>
                  <td></td>
                  <td><b>{'{:,}'.format(self.sumdatap()[1])} FCFA</b></td>
                </table>""")
            fact.write("""
                	<style>
                        *{
                            font-family: Inter, sans-serif;
                            padding: 0;
                            margin: 0;
                            box-sizing: border-box;
                            text-align: center;
                        }
                        table{
                            border-collapse: collapse;
                            background: #fff;
                            width: 100%;
                            font-size: 0.55rem;
                            padding: 0.5px;
                            border:solid 0.5px rgba(0,0,0,.3);
                            text-align: center;
                        }
                        table tr td, table tr th{
                            padding: 0;
                        }
                        table td{
                            background: rgba(0, 0, 0, .01);
                        }
                        .tnb{
                            border: none;
                            margin-top:1px;
                            text-align: right;
                        }
                        .tnb *{
                            text-align: right;
                        }
                    </style>
                <script>
                  print()
                </script>
            """)

        os.startfile(f"{fpath}.html")

    def directprint(self):
        self.handlePreview()
        self.prints.close()
        self.complete()

    def broserprint(self):
        self.printtoweb()
        self.prints.close()
        self.complete()


mainWindow = Home()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow.win.show()
    try:
        sys.exit(app.exec_())
    except:
        print("exiting...")
