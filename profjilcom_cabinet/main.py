# -*- coding: utf-8 -*-

# pie charts http://matplotlib.org/examples/pie_and_polar_charts/pie_demo_features.html

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

        self.closeButton.clicked.connect(self.goout)
        self.sendButton.clicked.connect(self.send)

        self.profs = Profjilcom()
        self.pokaz = PokazaniyaDB()
        self.pokaz.create_table(self.profs.username)
        self.pokaz.connect(self.profs.username)

        self.AuthDialog = AuthDialog()

    def set_authorize(self, authorized):
        if authorized:
            self.authorized = True
            self.UserLabel.setText(self.profs.username)
            self.statusLabel.setText("Авторизован")
            self.DisconnectButton.setText("Выйти")
            self.sendButton.setEnabled(True)
        else:
            self.authorized = False
            self.UserLabel.setText("Аноним")
            self.statusLabel.setText("Не авторизован")
            self.DisconnectButton.setText("Войти на сайт")
            self.sendButton.setEnabled(False)

    @property
    def authorized(self):
        return self.profs.authorized
    @authorized.setter
    def authorized(self, authorized):
        self.profs.authorized = authorized

    def set_form_values(self):
        if self.profs.username is not None:
            self.AuthDialog.userEdit.setText(self.profs.username)
            self.AuthDialog.passwordEdit.setFocus()
        else:
            self.AuthDialog.userEdit.setFocus()

        self.hvs_hvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.hvs_hvs_vannaya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_kuhnya.setValidator(QtGui.QIntValidator())
        self.gvs_gvs_vannaya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_elektroenergiya.setValidator(QtGui.QIntValidator())
        self.prochie_pokazaniya_t2_noch.setValidator(QtGui.QIntValidator())
        self.potreblenie_tepla_schetchik_1.setValidator(QtGui.QIntValidator())

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.PokazaniyaTab), "История показаний")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SendTab), "Отправить показания")

        #check needs auth
        self.set_authorize(self.auth())

    def auth(self):
        return self._connect(auth_url)

    def auth_form(self):
        ret = False

        self.AuthDialog.capchaEdit.clear()
        self.profs.get_auth_form_values()
        self._set_capcha_img()

        self.AuthDialog.show()

        if self.AuthDialog.exec_() == QtWidgets.QDialog.Accepted:
            user = self.AuthDialog.userEdit.text()
            pswd = self.AuthDialog.passwordEdit.text()
            capcha = self.AuthDialog.capchaEdit.text()

            try:
                ret = self.profs.auth(user, pswd, capcha)
            except NotAthorized:
                self.show_error("Ошибка авторизации", "Не верный логин или пароль!")
            except SiteStructFail:
                self.show_error("Ошибка сайта!", "Структура сайта изменена, обратитесь к разработчику!")
            else:
                self.UserLabel.setText(user)
                #self.set_authorize(True)

                self.profs.username = user
                self.sendButton.setEnabled(True)
                self.profs.save()

        return ret

    def _connect(self, url):
        ret = self.profs.connect(url)
        if not ret:
            if self.profs.status_code == 403:
                print('403')
                self.set_authorize(False)
                return self.auth_form()

            if self.profs.status_code // 500 == 1:
                self.show_error("Ошибка сервера", "Сервер вернул ошибку!")
                return False

            self.show_error("Ошибка соединения", "Не удаётся соединиться с сервером!")

        #except SiteStructFail:
        #    self.show_error("Ошибка сайта", "Структура сайта изменена, обратитесь к разработчику!")
        return ret

    def get_pokazaniya(self):
        if self.authorized:
            #TODO: send to db pokazania in other connection
            self.profs.sync2db(self.profs.get_all_pokazaniya())

        self.model = QSqlTableModel(self, db=self.pokaz.db)
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

        # for i in range(self.model.rowCount()):
        #    self.tableView.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def _set_capcha_img(self):
        self.profs.get_capcha_img()
        pic = QtGui.QPixmap()
        pic.loadFromData(self.profs.captcha_img)
        self.AuthDialog.capcha_label.setPixmap(pic)

    @pyqtSlot()
    def on_DisconnectButton_clicked(self):
        if self.authorized:
            self.profs.logout()
            self.set_authorize(False)
        else:
            self._connect(auth_url)

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
                self._connect(auth_url)
            except:
                self.show_error("Ошибка соединения", "Не удаётся соединиться с сервером!")
        else:
            self.show_error("Пустые поля", "Все поля должны быть заполнены!")
    
    def goout(self):
        self.close()

    def show_warning(self, title, msg):
        return self._show_MSG(QtWidgets.QMessageBox.warning, title, msg)
    def show_error(self, title, msg):
        return self._show_MSG(QtWidgets.QMessageBox.critical, title, msg)
    def _show_MSG(self, status=QtWidgets.QMessageBox.warning, title="", msg=""):
        return status(self, title, msg,
                        QtWidgets.QMessageBox.Cancel,
                        QtWidgets.QMessageBox.Cancel)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainFom()
    ui.show()
    ui.set_form_values()
    ui.get_pokazaniya()
    sys.exit(app.exec_())
