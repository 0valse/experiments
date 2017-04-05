import os
from re import search
import platform
from datetime import datetime
import pickle
import base64

OS = platform.system() # Darwin, Linux, Windows

#http://stackoverflow.com/questions/34966303/how-to-save-load-cookies-to-from-qnetworkaccessmanager
#http://webhamster.ru/mytetrashare/index/mtb0/1453285930d1wftkzohm

import requests
from configparser import ConfigParser
from urllib.parse import urljoin


from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from lxml import etree

URL = 'http://cabinet.profjilkom.ru/'
pokaz_url = urljoin(URL, '/node/1')
archive_url = "http://cabinet.profjilkom.ru/node/1/submissions"
auth_url = urljoin(URL, '/node/1?destination=node%2F1')

headers = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Accept-Encoding': ', '.join(('gzip', 'deflate')),
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'Referer': 'http://cabinet.profjilkom.ru/node/1'}

captcha_img = r'<img\ssrc="(/image_captcha/\d+/\d+)"\s(.+)'  #//*[@id="user-login-form"]/div/fieldset/img
captcha_sid = r'<input\stype="hidden"\sname="captcha_sid"\sid="edit-captcha-sid"\svalue="(.+)"'  #//*[@id="edit-captcha-sid"]
captcha_token = r'<input\stype="hidden"\sname="captcha_token"\sid="edit-captcha-token"\svalue="(.+)"'  #//*[@id="edit-captcha-token"]
form_id_value = r'<input type="hidden"\sname="form_build_id"\sid=".+"\svalue="(.+)"'  #//*[@id="form-52f7f685bd015e6e7342ba36b143ab8d"]
form_id = r'<input\stype="hidden"\sname="form_build_id"\sid="(.+)"\svalue=".+"'  #//*[@id="edit-user-login-block"]

hvs_hvs_kuhnya = 'submitted[hvs][hvs_kuhnya]'
hvs_hvs_vannaya = 'submitted[hvs][hvs_vannaya]'
gvs_gvs_kuhnya = 'submitted[gvs][gvs_kuhnya]'
gvs_gvs_vannaya = 'submitted[gvs][gvs_vannaya]'
prochie_pokazaniya_elektroenergiya = 'submitted[prochie_pokazaniya][elektroenergiya]'
prochie_pokazaniya_t2_noch = 'submitted[prochie_pokazaniya][t2_noch]'
potreblenie_tepla_schetchik_1 = 'submitted[potreblenie_tepla][schetchik_1]'




Date = "Date"
HVS_vanna = "HVS_vanna"
HVS_kuhnya = "HVS_kuhnya"
GVS_vanna = "GVS_vanna"
GVS_kuhnya = "GVS_kuhnya"
T1 = "T1"
T2 = "T2"
Teplo = "Teplo"
User = "User"


class NotAthorized(ConnectionError):
    pass


class SiteStructFail(Exception):
    pass


class DBFail(Exception):
    pass


class ConfFail(Exception):
    pass

class ServerError(ConnectionError):
    pass



#windows config in С:\ Users \ [user name] \ AppData \ Local \ [ (Project Name) or (AssemblyCompany) ] \ [name project_cashBuild] \ [AssemblyVersion] \ user.config


class FakeDB:
    db = None

    def connect(self, db=":memory:"):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(db)
        if not self.db.open():
            raise DBFail("Cann`t connect to db")
        self.query = QSqlQuery()

    def __del__(self):
        if self.db is not None:
            self.db.close()

    def create_tables(self, user):
        return self.query.exec_("""
            CREATE TABLE {table} (
            {d}	INTEGER NOT NULL UNIQUE,
            {hv}	INTEGER NOT NULL,
            {hk}	INTEGER NOT NULL,
            {gv}	INTEGER NOT NULL,
            {gk}	INTEGER NOT NULL,
            {t1}	INTEGER NOT NULL,
            {t2}	INTEGER NOT NULL,
            {T}	INTEGER NOT NULL);""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user)
        )

    def _test_data(self, user):
        return self.query.exec_("""REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                VALUES(datetime('now'), '10 м', '11 м', '12 м', '45 м', '10 к', '12 к', '134 к');""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user))


class PokazaniyaDB(FakeDB):
    def __init__(self, test_init=False):
        if test_init:
            self.connect()
            print('Test create', self.create_tables('anon'))
            print('Insert test data', self._test_data('anon'))
        else:
            self.connect(os.path.join(os.path.expanduser("~"),
                         ".config", "profjilcom", "prof.db"))

    def save2db(self, user, args):
        #arg: list of dict
        for kwargs in args:
            self.query.prepare("""
                REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                VALUES (:{d}, :{hv}, :{hk}, :{gv}, :{gk}, :{t1}, :{t2}, :{T});""".format(
                d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
                gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user)
            )
            self.query.bindValue(":%s" % Date, kwargs[Date])
            self.query.bindValue(":%s" % HVS_vanna, kwargs[HVS_vanna])
            self.query.bindValue(":%s" % HVS_kuhnya, kwargs[HVS_kuhnya])
            self.query.bindValue(":%s" % GVS_vanna, kwargs[GVS_vanna])
            self.query.bindValue(":%s" % GVS_kuhnya, kwargs[GVS_kuhnya])
            self.query.bindValue(":%s" % T1, kwargs[T1])
            self.query.bindValue(":%s" % T2, kwargs[T2])
            self.query.bindValue(":%s" % Teplo, kwargs[Teplo])
            self.query.exec_()


class Conf:
    config = ConfigParser()
    section = "COOKIES"
    account = "ACCOUNT"
    COOKS = requests.utils.cookiejar_from_dict({'has_js': '1'})
    username = None
    pswd = None

    def __init__(self):
        self.conf_file = os.path.join(os.path.expanduser("~"),
                                      ".config", "profjilcom", "prof.ini")
        if not os.path.exists(os.path.dirname(self.conf_file)):
            os.makedirs(os.path.dirname(self.conf_file))
        if not os.path.exists(self.conf_file):
            try:
                with open(self.conf_file, 'w+b') as f:
                    f.close()
            except:
                raise ConfFail("Have not access to config file!")

        self.config.read(self.conf_file)

        if not self.config.has_section(self.account):
            self.config.add_section(self.account)

        d = dict(self.config.items(self.account))
        self.pswd = d.get('password', None)
        self.username = d.get('username', None)
        self.cookies.update(self._loads(d.get('cookies', self._dumps(dict()))))

    def _dumps(self, raw):
        print(raw)
        return base64.encodebytes((pickle.dumps(raw))).decode()
    def _loads(selfs, raw):
        print(raw)
        return pickle.loads(base64.decodebytes(raw.encode()))

    @property
    def cookies(self):
        return self.COOKS

    @property
    def user(self):
        return self.username
    @user.setter
    def user(self, username):
        self.username = username

    @property
    def password(self):
        return self.pswd
    @password.setter
    def password(self, password):
        self.pswd = password

    def save(self):
        self.config.set(self.account, 'username', self.username)
        self.config.set(self.account, 'password', self.pswd)
        self.config.set(self.account, 'cookies', self._dumps(self.COOKS))
        with open(self.conf_file, 'w') as f:
            self.config.write(f)


class Profjilcom(Conf):
    def __init__(self):
        super(Profjilcom, self).__init__()

        self.response = None
        self.form_id = None
        self.form_value = None
        self.captcha_sid = None
        self.captcha_token = None
        self.captcha_img = None
        self.authorized = False

    def connect(self, url=URL):
        resp = requests.get(url, headers=headers, cookies=self.cookies)
        resp.close()
        if resp.status_code == 403:
            raise NotAthorized("Not authorized access")
        if resp.status_code // 500 == 1:
            raise ServerError("Server size error")
        if not resp.ok:
            raise ConnectionError("Coud not connect to %s. Code: %s" % (url, resp.status_code))
        self.response = resp.content.decode()

        self._form()  # form sets

    def _form(self):
        sf_id = search(form_id, self.response)
        if not sf_id:
            raise SiteStructFail("No sf_id find")
        self.form_id = sf_id.group(1)
        
        sf_id_val = search(form_id_value, self.response)
        if not sf_id_val:
            raise SiteStructFail("No sf_id_val find")
        self.form_value = sf_id_val.group(1)
        
        ca_sid =  search(captcha_sid, self.response)
        if not ca_sid:
            raise SiteStructFail("No ca_sid find")
        self.captcha_sid = ca_sid.group(1)
        
        ca_tok = search(captcha_token, self.response)
        if not ca_tok:
            raise SiteStructFail("No ca_tok find")
        self.captcha_token = ca_tok.group(1)
        
        return True
    
    def get_capcha_img(self):
        if not self.authorized:
            self.connect(URL)

        s = search(captcha_img, self.response)
        if not s:
            raise SiteStructFail("No capcha img url find")
        capcha_url = urljoin(URL, s.group(1))
        r = requests.get(capcha_url, headers=headers)
        r.close()
        if not r.ok:
            raise ConnectionError("Coud not connect to %s" % URL)
        self.captcha_img = r.content

    
    def logout(self):
        requests.get(urljoin(URL, "/logout"), headers=headers, cookies=self.cookies)
        self.authorized = False

    def auth(self, user, pswd, capcha):
        if (self.form_id == None or 
        self.form_value == None or
        self.captcha_sid == None or
        self.captcha_token == None):
            raise Exception("No form data")
        form = {
                    "name": user,
                    "pass": pswd,
                    "captcha_sid": self.captcha_sid,
                    "captcha_token": self.captcha_token,
                    "captcha_response": capcha,
                    "op": '%D0%92%D1%85%D0%BE%D0%B4+%D0%B2+%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D1%83',  #Вход+в+систему
                    "form_build_id": self.form_value,
                    "form_id": "user_login_block"
                }
        r = requests.post(auth_url, form,
                          cookies=self.cookies, headers=headers, allow_redirects=False)
        r.close()
        self.cookies.update(r.cookies)

        if r.status_code == 302:
            r = requests.get(pokaz_url,
                             cookies=self.cookies, headers=headers)
            r.close()
            if r.status_code == 403:
                print('403')
                raise NotAthorized("Not authorized access")

        self.authorized = True

        self.username = user
        self.password = pswd
        self.save()

    
    def send_pokazaniya(self, hvs_kuhnya, hvs_vannaya, gvs_kuhnya, gvs_vannaya, t1, t2, teplo):
        form = {
            hvs_hvs_kuhnya: hvs_kuhnya, 
            hvs_hvs_vannaya: hvs_vannaya,
            gvs_gvs_kuhnya: gvs_kuhnya,
            gvs_gvs_vannaya: gvs_vannaya, 
            prochie_pokazaniya_elektroenergiya: t1,
            prochie_pokazaniya_t2_noch: t2,
            potreblenie_tepla_schetchik_1: teplo,
            "op": '%D0%9E%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D1%82%D1%8C',  #отправить
                }
        r = requests.post(pokaz_url, form, cookies=self.cookies,
                          headers=headers, allow_redirects=False)
        r.close()
        if r.status_code == 403:
            raise NotAthorized("Not authorized access")
        if not r.ok:
            raise ConnectionError("Coud not connect to %s. Errcode: %s" % (pokaz_url, r.status_code))
        PokazaniyaDB().save2db(self.username,
                               list(dict(HVS_vanna=hvs_vannaya, HVS_kuhnya=hvs_kuhnya, GVS_vanna=gvs_vannaya,
                                         GVS_kuhnya=gvs_kuhnya, T1=t1, T2=t2, Teplo=teplo,
                                         Date=datetime.now().timestamp())
                                    )
                               )
        return r.status_code, r

    def get_all_pokazaniya(self):
        # get main page
        r = requests.get(archive_url,
                         cookies=self.cookies, headers=headers)
        r.close()
        tree = etree.HTML(r.text)
        line = 1
        tmp = list()
        while True:
            xdate = tree.xpath('//*[@id="squeeze"]/div/div/div[2]/table[1]/tbody/tr[%d]/td[2]' % line)
            xlink = tree.xpath('//*[@id="squeeze"]/div/div/div[2]/table[1]/tbody/tr[%d]/td[3]/a' % line)

            if len(xdate) < 1:
                break
            date = xdate[0].xpath('text()')[0]
            link = xlink[0].xpath('@href')[0]

            # get html page by URL
            r = requests.get(urljoin(URL, link),
                             cookies=self.cookies, headers=headers)
            r.close()

            #parse
            p = etree.HTML(r.text)
            hvs_kuhnya = p.xpath('//*[@id="edit-submitted-hvs-hvs-kuhnya"]')[0].xpath('text()')[0]
            hvs_vannaya = p.xpath('//*[@id="edit-submitted-hvs-hvs-vannaya"]')[0].xpath('text()')[0]
            gvs_kuhnya = p.xpath('//*[@id="edit-submitted-gvs-gvs-kuhnya"]')[0].xpath('text()')[0]
            gvs_vannaya = p.xpath('//*[@id="edit-submitted-gvs-gvs-vannaya"]')[0].xpath('text()')[0]
            t1 = p.xpath('//*[@id="edit-submitted-prochie-pokazaniya-elektroenergiya"]')[0].xpath('text()')[0]
            t2 = p.xpath('//*[@id="edit-submitted-prochie-pokazaniya-t2-noch"]')[0].xpath('text()')[0]
            teplo = p.xpath('//*[@id="edit-submitted-potreblenie-tepla-schetchik-1"]')[0].xpath('text()')[0]

            tmp.append(dict(HVS_vanna=hvs_vannaya, HVS_kuhnya=hvs_kuhnya, GVS_vanna=gvs_vannaya,
                 GVS_kuhnya=gvs_kuhnya, T1=t1, T2=t2, Teplo=teplo,
                 Date=datetime.strptime(date.replace(" ", ""),
                                        '%m/%d/%Y-%H:%M').timestamp())
                       )
            line += 1

        return tmp

    def sync2db(self, pokaz):
        print(self.username)
        PokazaniyaDB().save2db(self.username, pokaz)
