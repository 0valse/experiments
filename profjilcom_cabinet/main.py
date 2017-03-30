# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot

from prof import Profjilcom, NotAthorized


class AuthDialog(QtWidgets.QDialog):
    def __init__(self, *args):
        super(AuthDialog, self).__init__(*args)
        loadUi('authenticationdialog.ui', self)


class MainFom(QtWidgets.QWidget):
    def __init__(self, *args):
        super(MainFom, self).__init__(*args)

        loadUi('main.ui', self)

        self.AuthDialog = AuthDialog()

        self.closeButton.clicked.connect(self.quit)

        self.hvs_hvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.hvs_hvs_vannaya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_vannaya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_elektroenergiya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_t2_noch.setValidator(QtGui.QIntValidator())
        self.potreblenie_tepla_schetchik_1.setValidator(QtGui.QIntValidator())

        for i in range(7):
            self.tableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.PokazaniyaTab), "История показаний")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SendTab), "Отправить показания")

        self.profs = Profjilcom()
        if not self.profs.authorized:
            self.profs.get_capcha_img()
            pic = QtGui.QPixmap()
            pic.loadFromData(self.profs.captcha_img)
            self.AuthDialog.capcha_label.setPixmap(pic)
            self.auth()

    @pyqtSlot()
    def on_DisconnectButton_clicked(self):
        if self.profs.authorized:
            self.profs.logout()
            self.UserLabel.setText("Аноним")
            self.statusLabel.setText("Не авторизован")
            self.DisconnectButton.setText("Соединиться")
        else:
            self.auth()

    @pyqtSlot()
    def on_sendButton_clicked(self):
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
            self.show_error("Ошибка авторизации", "Ошибка авторизации. Не верный логин или пароль!")
        else:
            self.UserLabel.setText(user)
            self.statusLabel.setText("Авторизован")
            self.DisconnectButton.setText("Разьединить")

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
