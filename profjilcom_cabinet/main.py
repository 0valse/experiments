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

        self.sendButton.clicked.connect(self.send)
        self.closeButton.clicked.connect(self.quit)

        self.profs = Profjilcom()
        if not self.profs.authorized:
            self.profs.get_capcha_img()
            pic = QtGui.QPixmap()
            pic.loadFromData(self.profs.captcha_img)
            self.AuthDialog.capcha_label.setPixmap(pic)
            self.auth()

        print(dir(self))

    @pyqtSlot()
    def on_DisconnectButton_clicked(self):
        if self.profs.authorized:
            self.profs.logout()
            self.UserLabel.setText("Unknown")
            self.statusLabel.setText("NOT Authorized")
            self.DisconnectButton.setText("Connect")
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
        if not (hvs_kuhnya or hvs_vannaya or gvs_vannaya or gvs_kuhnya or t1 or t2 or teplo):
            #TODO: show error window
            print("Not enoth params")
        else:
            try:
                self.profs.send_pokazaniya(hvs_kuhnya, hvs_vannaya, gvs_vannaya, gvs_kuhnya, t1, t2, teplo)
            #except NotAthorized:
            #    self.auth()
            except:
                #TODO: show error window
                self.close()
    
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
            #TODO: err not authorized
            print("Err")
            return
        self.UserLabel.setText(user)
        self.statusLabel.setText("Authorized")
        self.DisconnectButton.setText("Disconnect")
        #self.profs.auth(user, pswd, capcha)[0]
    
    def send(self):
        pass


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainFom()
    ui.show()
    sys.exit(app.exec_())
