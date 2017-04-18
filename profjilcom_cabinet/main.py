# -*- coding: utf-8 -*-

# pie charts http://matplotlib.org/examples/pie_and_polar_charts/pie_demo_features.html

from PyQt5.QtCore import Qt, QRegExp, QTimer
from PyQt5 import QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtSql import QSqlTableModel

from prof import (Profjilcom, PokazaniyaDB, auth_url,
                  previos_month, num2month, cur_month, cur_year,
                  NotAthorized, ConfFail, ServerError, SiteStructFail)
from prof import GVS_kuhnya, GVS_vanna, HVS_kuhnya, HVS_vanna, T1, T2, Teplo



class AuthDialog(QtWidgets.QDialog):
    def __init__(self, *args):
        super(AuthDialog, self).__init__(*args)
        loadUi('authenticationdialog.ui', self)


class MainFom(QtWidgets.QWidget):
    def __init__(self, *args):
        super(MainFom, self).__init__(*args)

        loadUi('main.ui', self)

        self.profs = Profjilcom()
        self.pokaz = PokazaniyaDB()
        self.pokaz.create_table(self.profs.username)

        self.AuthDialog = AuthDialog()

        self.porazanie_previos_month = dict()
        self.porazanie_cur_month = dict()

        #подпись на сигналы
        self.closeButton.clicked.connect(self.goout)
        self.sendButton.clicked.connect(self.send)

        #общий таймер
        self.timer = QTimer()

        # сигналы отправляются на слоты всех labels
        self.gvs_gvs_kuhnya.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.gvs_kuhnya_plus_editingFinished)

        self.gvs_gvs_vannaya.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.gvs_vannaya_plus_editingFinished)

        self.hvs_hvs_kuhnya.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.hvs_kuhnya_plus_editingFinished)

        self.hvs_hvs_vannaya.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.hvs_vannaya_plus_editingFinished)

        self.prochie_pokazaniya_elektroenergiya.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.label_t1_plus_editingFinished)

        self.prochie_pokazaniya_t2_noch.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.label_t2_plus_editingFinished)

        self.potreblenie_tepla_schetchik_1.textEdited.connect(self.timer_timeout)
        self.timer.timeout.connect(self.label_teplo_plus_editingFinished)

        self.pokaz_list = list()

    def set_authorize(self, authorized):
        if authorized:
            self.authorized = True
            self.UserLabel.setText(self.profs.username)
            self.statusLabel.setText("Авторизован")
            self.DisconnectButton.setText("Выйти")
            # self.sendButton.setEnabled(True)
        else:
            self.authorized = False
            self.UserLabel.setText("Аноним")
            self.statusLabel.setText("Не авторизован")
            self.DisconnectButton.setText("Войти на сайт")
            # self.sendButton.setEnabled(False)

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

        rx = QRegExp('\d+[,.]{0,1}\d{0,2}')
        self.hvs_hvs_kuhnya.setValidator(QtGui.QRegExpValidator(rx))
        self.hvs_hvs_vannaya.setValidator(QtGui.QRegExpValidator(rx))
        self.gvs_gvs_kuhnya.setValidator(QtGui.QRegExpValidator(rx))
        self.gvs_gvs_vannaya.setValidator(QtGui.QRegExpValidator(rx))
        self.prochie_pokazaniya_elektroenergiya.setValidator(QtGui.QRegExpValidator(rx))
        self.prochie_pokazaniya_t2_noch.setValidator(QtGui.QRegExpValidator(rx))
        self.potreblenie_tepla_schetchik_1.setValidator(QtGui.QRegExpValidator(rx))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.PokazaniyaTab),
            "История показаний")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SendTab),
            "Отправить показания")

        self.label_mounth.setText("""<html><head/><body>
            <p><span style=" font-weight:600;">%s</span>.</p><
            /body></html>""" % num2month(cur_month()))

        # self.label_hvs_kuhnya_plus.setVisible(False)
        # self.label_hvs_vannaya_plus.setVisible(False)
        # self.label_gvs_kuhnya_plus.setVisible(False)
        # self.label_gvs_vannaya_plus.setVisible(False)
        # self.label_t1_plus.setVisible(False)
        # self.label_t2_plus.setVisible(False)
        # self.label_teplo_plus.setVisible(False)

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
                # self.sendButton.setEnabled(True)
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

    def _set_plus(self, vidget, old, cur):
        diff = cur - old
        ed = 'м<span style=" vertical-align:super;">3</span>'
        old_str = '{old} {ed} в прошлом месяце'.format(old=old, ed=ed)
        if diff < 0:
            html = '''<html>
            <head/>
            <body>
                <p>
                    {old_str}
                </p>
            </body>
            </html>'''.format(old_str=old_str)
        else:
            html = '''<html>
            <body>
                <p>
                    <span style="font-weight:600;">
                    +{diff}
                    </span>
                     {ed} к показаниям за {prev_month} ({old_str})
                </p>
            </body>
            </html>'''.format(
                diff=diff,
                ed=ed,
                old_str=old_str,
                prev_month=num2month(previos_month())
            )
        vidget.setText(html)

    def _update_pokaz_list(self, item):
        if item not in self.pokaz_list:
            self.pokaz_list.append(item)
        return len(self.pokaz_list)

    def _del_pokaz_list_item(self, item):
        if item in self.pokaz_list:
            self.pokaz_list.remove(item)
        return len(self.pokaz_list)

    def check_sendButton_visible(self):
        if self.authorized and len(self.pokaz_list) >= 7:
            self.sendButton.setEnabled(True)
        else:
            self.sendButton.setEnabled(False)

    def timer_timeout(self):
        self.timer.stop()
        self.timer.start(1000)

    def hvs_vannaya_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.hvs_hvs_vannaya.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(HVS_vanna)
        else:
            self._update_pokaz_list(HVS_vanna)
        prev_pokazanie = float(self.porazanie_previos_month.get(HVS_vanna))

        self._set_plus(self.label_hvs_vannaya_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def gvs_vannaya_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.gvs_gvs_vannaya.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(GVS_vanna)
        else:
            self._update_pokaz_list(GVS_vanna)
        prev_pokazanie = float(self.porazanie_previos_month.get(GVS_vanna))
        
        self._set_plus(self.label_gvs_vannaya_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def hvs_kuhnya_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.hvs_hvs_kuhnya.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(HVS_kuhnya)
        else:
            self._update_pokaz_list(HVS_kuhnya)
        prev_pokazanie = float(self.porazanie_previos_month.get(HVS_kuhnya))
        
        self._set_plus(self.label_hvs_kuhnya_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def gvs_kuhnya_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.gvs_gvs_kuhnya.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(GVS_kuhnya)
        else:
            self._update_pokaz_list(GVS_kuhnya)
        prev_pokazanie = float(self.porazanie_previos_month.get(GVS_kuhnya))
        
        self._set_plus(self.label_gvs_kuhnya_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def label_t1_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.prochie_pokazaniya_elektroenergiya.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(T1)
        else:
            self._update_pokaz_list(T1)
        prev_pokazanie = float(self.porazanie_previos_month.get(T1))

        self._set_plus(self.label_t1_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def label_t2_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.prochie_pokazaniya_t2_noch.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(T2)
        else:
            self._update_pokaz_list(T2)
        prev_pokazanie = float(self.porazanie_previos_month.get(T1))

        self._set_plus(self.label_t2_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()

    def label_teplo_plus_editingFinished(self):
        self.timer.stop()
        try:
            cur_pokazanie = float(self.potreblenie_tepla_schetchik_1.text())
        except ValueError:
            cur_pokazanie = 0
            self._del_pokaz_list_item(Teplo)
        else:
            self._update_pokaz_list(Teplo)
        prev_pokazanie = float(self.porazanie_previos_month.get(Teplo))
        
        self._set_plus(self.label_teplo_plus, prev_pokazanie, cur_pokazanie)
        self.check_sendButton_visible()


    def get_pokazaniya(self):
        if self.authorized:
            #TODO: send to db pokazania in other connection
            self.profs.sync2db(self.profs.get_all_pokazaniya())
            #try:
            #    self.profs.sync2db(self.profs.get_all_pokazaniya())
            #except:
            #    self.show_error("Ошибка сайта!", "Структура сайта изменена, обратитесь к разработчику!")
            #    return

        self.model = QSqlTableModel(self, db=self.pokaz.db)
        self.model.setTable(self.profs.username)
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model.select()

        self.model.setHeaderData(0, Qt.Horizontal, "Дата")
        self.model.setHeaderData(1, Qt.Horizontal, 'ХВС Кухня, м3')
        self.model.setHeaderData(2, Qt.Horizontal, 'ХВС Ванная, м3')
        self.model.setHeaderData(3, Qt.Horizontal, 'ГВС Кухня, м3')
        self.model.setHeaderData(4, Qt.Horizontal, 'ГВС Ванная, м3')
        self.model.setHeaderData(5, Qt.Horizontal, "Электричество\nДень, КВт/ч")
        self.model.setHeaderData(6, Qt.Horizontal, "Электричество\nНочь, КВт/ч")
        self.model.setHeaderData(7, Qt.Horizontal, "Отопление, КВт/ч")
        self.tableView.setModel(self.model)

        # for i in range(self.model.rowCount()):
        #    self.tableView.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.porazanie_previos_month = self.pokaz.get_month_pokaz(self.profs.username, previos_month())
        print(self.porazanie_previos_month)
        self.porazanie_cur_month = self.pokaz.get_last_pokaz(self.profs.username)
        print(self.porazanie_cur_month)

        self._set_previos(self.label_hvs_kuhnya_plus, HVS_kuhnya)
        self._set_previos(self.label_hvs_vannaya_plus, HVS_vanna)
        self._set_previos(self.label_gvs_kuhnya_plus, GVS_kuhnya)
        self._set_previos(self.label_gvs_vannaya_plus, GVS_vanna)
        self._set_previos(self.label_t1_plus, T1)
        self._set_previos(self.label_t2_plus, T2)
        self._set_previos(self.label_teplo_plus, Teplo)

    def _set_previos(self, vidget, pokaz_name):
        old_str = self.porazanie_previos_month.get(pokaz_name, None)
        if old_str is not None:
            html = '''<html>
            <head/>
    <body>
        <p>{old_str} м<span style=" font-weight:400; vertical-align:super;">3</span> в прошлом месяце.</p>
    </body>
            </html>'''.format(old_str=old_str)
            vidget.setText(html)
            vidget.setVisible(True)
        else:
            vidget.setVisible(False)


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
        hvs_kuhnya = float(self.hvs_hvs_kuhnya.text().replace(',', '.'))
        hvs_vannaya = float(self.hvs_hvs_vannaya.text().replace(',', '.'))
        gvs_kuhnya = float(self.gvs_gvs_kuhnya.text().replace(',', '.'))
        gvs_vannaya = float(self.gvs_gvs_vannaya.text().replace(',', '.'))
        t1 = float(self.prochie_pokazaniya_elektroenergiya.text().replace(',', '.'))
        t2 = float(self.prochie_pokazaniya_t2_noch.text().replace(',', '.'))
        teplo = float(self.potreblenie_tepla_schetchik_1.text().replace(',', '.'))

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
