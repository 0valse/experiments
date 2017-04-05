# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5.QtCore import Qt
from PyQt5 import QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtSql import QSqlTableModel

from prof import Profjilcom, PokazaniyaDB, URL, auth_url
from prof import NotAthorized, ConfFail, ServerError, SiteStructFail


class AuthDialog(QtWidgets.QDialog):
    def __init__(self, *args):
        super(AuthDialog, self).__init__(*args)
        loadUi('authenticationdialog.ui', self)


class MainFom(QtWidgets.QWidget):
    def __init__(self, *args):
        super(MainFom, self).__init__(*args)

        loadUi('main.ui', self)

        self.closeButton.clicked.connect(self.quit)
        self.sendButton.clicked.connect(self.send)

        self.profs = Profjilcom()

        self.AuthDialog = AuthDialog()

        if self.profs.user is not None:
            self.AuthDialog.userEdit.setText(self.profs.username)
            self.AuthDialog.passwordEdit.setFocus()
        if self.profs.password is not None:
            self.AuthDialog.passwordEdit.setText(self.profs.password)
            self.AuthDialog.savepass_checkBox.setChecked(True)
            self.AuthDialog.capchaEdit.setFocus()

        try:
            self.profs.connect(auth_url)
        except NotAthorized:
            self.profs.authorized = False
            self.auth()
            #self.show_warning("Ошибка авторизации", "Требуется сначала авторизоваться!")
        except ConfFail:
            self.show_error("Ошибка соединения", "Не удаётся соединиться с сервером!")
        except ServerError:
            self.show_error("Ошибка сервера", "Сервер вернул ошибку!")
        except SiteStructFail:
            self.show_error("Ошибка сайта", "Структура сайта изменена, обратитесь к разработчику!")

        print('Create table', PokazaniyaDB().create_tables(self.profs.username))

        self.hvs_hvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.hvs_hvs_vannaya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_vannaya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_elektroenergiya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_t2_noch.setValidator(QtGui.QIntValidator())
        self.potreblenie_tepla_schetchik_1.setValidator(QtGui.QIntValidator())

        self.model = QSqlTableModel(self)
        self.model.setTable(self.profs.username)
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model.select()

        self.model.setHeaderData(0, Qt.Horizontal, "Дата")
        self.model.setHeaderData(1, Qt.Horizontal, "ХВС Кухня")
        self.model.setHeaderData(2, Qt.Horizontal, "ХВС Ванная")
        self.model.setHeaderData(3, Qt.Horizontal, "ГВС Кухня")
        self.model.setHeaderData(4, Qt.Horizontal, "ГВС Ванная")
        self.model.setHeaderData(5, Qt.Horizontal, "Электричество\nДень")
        self.model.setHeaderData(6, Qt.Horizontal, "Электричество\nНочь")
        self.model.setHeaderData(7, Qt.Horizontal, "Отопление")
        self.tableView.setModel(self.model)

        #for i in range(self.model.rowCount()):
        #    self.tableView.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.PokazaniyaTab), "История показаний")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SendTab), "Отправить показания")

        if self.profs.authorized:
            pokazs = self.profs.get_all_pokazaniya()
            print(pokazs)
            print(self.profs.username)
            self.profs.sync2db(pokazs)

    def _set_capcha_img(self):
        self.profs.get_capcha_img()
        pic = QtGui.QPixmap()
        pic.loadFromData(self.profs.captcha_img)
        self.AuthDialog.capcha_label.setPixmap(pic)

    @pyqtSlot()
    def on_DisconnectButton_clicked(self):
        if self.profs.authorized:
            self.profs.logout()
            self.UserLabel.setText("Аноним")
            self.statusLabel.setText("Не авторизован")
            self.DisconnectButton.setText("Соединиться")
            self.sendButton.setEnabled(True)
        else:
            self.auth()

    def send(self):
        hvs_kuhnya = self.hvs_hvs_kuhnya.text()
        hvs_vannaya = self.hvs_hvs_vannaya.text()
        gvs_kuhnya = self.gvs_gvs_kuhnya.text()
        gvs_vannaya = self.gvs_gvs_vannaya.text()
        t1 = self.prochie_pokazaniya_elektroenergiya.text()
        t2 = self.prochie_pokazaniya_t2_noch.text()
        teplo = self.potreblenie_tepla_schetchik_1.text()

        if (hvs_kuhnya and hvs_vannaya and gvs_vannaya and gvs_kuhnya and t1 and t2 and teplo):
            try:
                self.profs.send_pokazaniya(hvs_kuhnya, hvs_vannaya, gvs_vannaya, gvs_kuhnya, t1, t2, teplo)
            except NotAthorized:
                self.show_warning("Ошибка авторизации", "Требуется сначала авторизоваться!")
                self.auth()
            except:
                self.show_error("Ошибка соединения", "Не удаётся соединиться с сервером!")
        else:
            self.show_error("Пустые поля", "Все поля должны быть заполнены!")
    
    def quit(self):
        self.profs.logout()
        self.close()

    def auth(self):
        try:
            self._set_capcha_img()
        except SiteStructFail:
            self.show_error("Ошибка сайта", "Структура сайта изменена, обратитесь к разработчику!")
            return

        self.AuthDialog.capchaEdit.clear()
        self.AuthDialog.show()
        
        if self.AuthDialog.exec_() == QtWidgets.QDialog.Accepted:
            user = self.AuthDialog.userEdit.text()
            pswd = self.AuthDialog.passwordEdit.text()
            capcha = self.AuthDialog.capchaEdit.text()
        else:
            return

        try:
            self.profs.auth(user, pswd, capcha)
        except NotAthorized:
            self.show_error("Ошибка авторизации", "Не верный логин или пароль!")
        else:
            self.UserLabel.setText(user)
            self.statusLabel.setText("Авторизован")
            self.DisconnectButton.setText("Разьединить")

            self.profs.username = user
            if self.AuthDialog.savepass_checkBox.isChecked():
                self.profs.password = pswd
            self.sendButton.setEnabled(True)
            self.profs.save()

    def show_warning(self, title, msg):
        return self._show_MSG(QtWidgets.QMessageBox.warning, title, msg)
    def show_error(self, title, msg):
        return self._show_MSG(QtWidgets.QMessageBox.critical, title, msg)
    def _show_MSG(self, status=QtWidgets.QMessageBox.warning, title="", msg=""):
        result = status(self, title, msg,
                        QtWidgets.QMessageBox.Cancel,
                        QtWidgets.QMessageBox.Cancel)
        return result


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainFom()
    ui.show()
    sys.exit(app.exec_())
