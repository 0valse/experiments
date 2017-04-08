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


from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlDriver

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

    def __del__(self):
        if self.db.isOpen():
            self.db.close()

    def create_table(self, user):
        query = QSqlQuery(self.db)
        ret = query.exec_("""
            CREATE TABLE IF NOT EXISTS {table} (
            {d} TEXT NOT NULL UNIQUE,
            {hv} TEXT NOT NULL,
            {hk} TEXT NOT NULL,
            {gv} TEXT NOT NULL,
            {gk} TEXT NOT NULL,
            {t1} TEXT NOT NULL,
            {t2} TEXT NOT NULL,
            {T} TEXT NOT NULL);""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user)
        )
        if not ret:
            print(query.lastError().text())
        return ret

    def _test_data(self, user,
                   values={'HVS_vanna': '0 м3', 'HVS_kuhnya': '8 м3', 'GVS_vanna': '0 м3', 'GVS_kuhnya': '5 м3',
                   'T1': '349 кВт', 'T2': '13 кВт', 'Teplo': '41,569кВт.', 'Date': '2016-01-25'}):
        query = QSqlQuery(self.db)
        query.prepare("""REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                        VALUES (:{d}, :{hv}, :{hk}, :{gv}, :{gk}, :{t1}, :{t2}, :{T});""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo,
            table=query.driver().escapeIdentifier(user, QSqlDriver.TableName))
        )
        query.bindValue(':%s' % Date, values[Date])
        query.bindValue(':%s' % HVS_vanna, values[HVS_vanna])
        query.bindValue(':%s' % HVS_kuhnya, values[HVS_kuhnya])
        query.bindValue(':%s' % GVS_vanna, values[GVS_vanna])
        query.bindValue(':%s' % GVS_kuhnya, values[GVS_kuhnya])
        query.bindValue(':%s' % T1, values[T1])
        query.bindValue(':%s' % T2, values[T2])
        query.bindValue(':%s' % Teplo, values[Teplo])
        ret = query.exec_()
        if not ret:
            print(query.lastError().text())
        return ret


class PokazaniyaDB(FakeDB):
    def __init__(self, test_init=False):
        if test_init:
            self.connect()
            print('Test create', self.create_table('anon'))
            print('Insert test data', self._test_data('anon'))
        else:
            self.connect(os.path.join(os.path.expanduser("~"),
                         ".config", "profjilcom", "prof.db"))

    def save2db(self, user, args):
        #arg: list of dict
        self.db.transaction()
        query = QSqlQuery(self.db)
        for kwargs in args:
            query.prepare("""REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                                    VALUES (:{d}, :{hv}, :{hk}, :{gv}, :{gk}, :{t1}, :{t2}, :{T});""".format(
                d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
                gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo,
                table=query.driver().escapeIdentifier(user, QSqlDriver.TableName))
            )

            query.bindValue(':%s' % Date, kwargs[Date])
            query.bindValue(':%s' % HVS_vanna, kwargs[HVS_vanna])
            query.bindValue(':%s' % HVS_kuhnya, kwargs[HVS_kuhnya])
            query.bindValue(':%s' % GVS_vanna, kwargs[GVS_vanna])
            query.bindValue(':%s' % GVS_kuhnya, kwargs[GVS_kuhnya])
            query.bindValue(':%s' % T1, kwargs[T1])
            query.bindValue(':%s' % T2, kwargs[T2])
            query.bindValue(':%s' % Teplo, kwargs[Teplo])
        print('commit', self.db.commit())


class Conf:
    config = ConfigParser()
    account = "ACCOUNT"
    COOKS = requests.utils.cookiejar_from_dict({'has_js': '1'})
    username = None
    last_update = datetime.now().date().isoformat()

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
        self.username = d.get('username', None)
        self.last_update = d.get("last_update", datetime.now().date().isoformat())
        self.cookies.update(self._loads(d.get('cookies', self._dumps(dict()))))

    def _dumps(self, raw):
        return base64.encodebytes((pickle.dumps(raw))).decode()
    def _loads(selfs, raw):
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

    def save(self):
        self.config.set(self.account, 'username', self.username)
        self.config.set(self.account, 'last_update', self.last_update)
        self.config.set(self.account, 'cookies', self._dumps(self.COOKS))
        with open(self.conf_file, 'w') as f:
            self.config.write(f)


class Profjilcom(Conf):
    def __init__(self):
        super(Profjilcom, self).__init__()

        self.response = None
        self.status_code = None
        self.form_id = None
        self.form_value = None
        self.captcha_sid = None
        self.captcha_token = None
        self.captcha_img = None
        self.authorized = False

    def connect(self, url=URL):
        r = requests.get(url, headers=headers, cookies=self.cookies)
        r.close()
        #if resp.status_code == 403:
        #    raise NotAthorized("Not authorized access")
        #if resp.status_code // 500 == 1:
        #    raise ServerError("Server size error")
        #if not resp.ok:
        #    raise ConnectionError("Coud not connect to %s. Code: %s" % (url, resp.status_code))
        self.response = r.text
        self.status_code = r.status_code
        self.cookies.update(r.cookies)

        return r.ok

    def get_auth_form_values(self):
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
        self.connect(urljoin(URL, "/logout"))
        self.authorized = False

    def auth(self, user, pswd, capcha):
        if (self.form_id == None or 
        self.form_value == None or
        self.captcha_sid == None or
        self.captcha_token == None):
            raise SiteStructFail("No form data")

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
        ret = r.ok

        self.cookies.update(r.cookies)

        if r.status_code == 302:
            r = requests.get(pokaz_url,
                             cookies=self.cookies, headers=headers)
            r.close()
            ret = r.ok

            if r.status_code == 403:
                raise NotAthorized("Not authorized access")

        self.authorized = True
        self.username = user
        self.cookies.update(r.cookies)  # update session cookies
        self.save()

        self.response = r.text
        self.status_code = r.status_code

        return ret

    
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
                               list(dict(HVS_vanna=str(hvs_vannaya), HVS_kuhnya=str(hvs_kuhnya),
                                         GVS_vanna=str(gvs_vannaya), GVS_kuhnya=str(gvs_kuhnya),
                                         T1=str(t1), T2=str(t2), Teplo=str(teplo),
                                         Date=str(datetime.now().date().isoformat()))
                                    )
                               )
        return r.status_code, r

    def get_all_pokazaniya(self):
        # TODO: delet tested data
        return [{'HVS_vanna': '38 м3', 'HVS_kuhnya': '82 м3', 'GVS_vanna': '48 м3', 'GVS_kuhnya': '26 м3', 'T1': '2,616 кВт', 'T2': '718 кВт', 'Teplo': '11,718кВт.', 'Date': '2017-03-26'}, {'HVS_vanna': '35 м3', 'HVS_kuhnya': '78 м3', 'GVS_vanna': '45 м3', 'GVS_kuhnya': '25 м3', 'T1': '2,483 кВт', 'T2': '678 кВт', 'Teplo': '11,174кВт.', 'Date': '2017-02-21'}, {'HVS_vanna': '30 м3', 'HVS_kuhnya': '68 м3', 'GVS_vanna': '39 м3', 'GVS_kuhnya': '22 м3', 'T1': '2,016 кВт', 'T2': '578 кВт', 'Teplo': '9,057кВт.', 'Date': '2016-12-26'}, {'HVS_vanna': '25 м3', 'HVS_kuhnya': '64 м3', 'GVS_vanna': '36 м3', 'GVS_kuhnya': '21 м3', 'T1': '1,835 кВт', 'T2': '536 кВт', 'Teplo': '7,999кВт.', 'Date': '2016-11-23'}, {'HVS_vanna': '22 м3', 'HVS_kuhnya': '58 м3', 'GVS_vanna': '32 м3', 'GVS_kuhnya': '20 м3', 'T1': '1,603 кВт', 'T2': '473 кВт', 'Teplo': '7,146кВт.', 'Date': '2016-10-25'}, {'HVS_vanna': '19 м3', 'HVS_kuhnya': '53 м3', 'GVS_vanna': '28 м3', 'GVS_kuhnya': '18 м3', 'T1': '1,402 кВт', 'T2': '409 кВт', 'Teplo': '6,477кВт.', 'Date': '2016-09-25'}, {'HVS_vanna': '16 м3', 'HVS_kuhnya': '46 м3', 'GVS_vanna': '24 м3', 'GVS_kuhnya': '16 м3', 'T1': '1,268 кВт', 'T2': '335 кВт', 'Teplo': '6,477кВт.', 'Date': '2016-08-23'}, {'HVS_vanna': '12 м3', 'HVS_kuhnya': '39 м3', 'GVS_vanna': '21 м3', 'GVS_kuhnya': '15 м3', 'T1': '1,155 кВт', 'T2': '267 кВт', 'Teplo': '6,477кВт.', 'Date': '2016-07-24'}, {'HVS_vanna': '9 м3', 'HVS_kuhnya': '33 м3', 'GVS_vanna': '21 м3', 'GVS_kuhnya': '15 м3', 'T1': '1,045 кВт', 'T2': '219 кВт', 'Teplo': '6,477кВт.', 'Date': '2016-06-23'}, {'HVS_vanna': '7 м3', 'HVS_kuhnya': '28 м3', 'GVS_vanna': '17 м3', 'GVS_kuhnya': '13 м3', 'T1': '943 кВт', 'T2': '171 кВт', 'Teplo': '6,477кВт.', 'Date': '2016-05-24'}, {'HVS_vanna': '5 м3', 'HVS_kuhnya': '24 м3', 'GVS_vanna': '13 м3', 'GVS_kuhnya': '11 м3', 'T1': '854 кВт', 'T2': '137 кВт', 'Teplo': '6,450кВт.', 'Date': '2016-04-23'}, {'HVS_vanna': '2 м3', 'HVS_kuhnya': '18 м3', 'GVS_vanna': '7 м3', 'GVS_kuhnya': '8 м3', 'T1': '696 кВт', 'T2': '83 кВт', 'Teplo': '5,889кВт.', 'Date': '2016-03-23'}, {'HVS_vanna': '1 м3', 'HVS_kuhnya': '13 м3', 'GVS_vanna': '2 м3', 'GVS_kuhnya': '6 м3', 'T1': '526 кВт', 'T2': '28 кВт', 'Teplo': '5,062кВт.', 'Date': '2016-02-20'}, {'HVS_vanna': '0 м3', 'HVS_kuhnya': '8 м3', 'GVS_vanna': '0 м3', 'GVS_kuhnya': '5 м3', 'T1': '349 кВт', 'T2': '13 кВт', 'Teplo': '41,569кВт.', 'Date': '2016-01-25'}]
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

            tmp.append(dict(HVS_vanna=str(hvs_vannaya), HVS_kuhnya=str(hvs_kuhnya),
                            GVS_vanna=str(gvs_vannaya), GVS_kuhnya=str(gvs_kuhnya),
                            T1=str(t1), T2=str(t2), Teplo=str(teplo),
                            Date=str(datetime.strptime(date.replace(" ", ""),
                                        '%m/%d/%Y-%H:%M').date().isoformat()))
                       )
            line += 1

        return tmp

    def sync2db(self, pokaz):
        self.last_update = datetime.now().date().isoformat()
        PokazaniyaDB().save2db(self.username, pokaz)
        self.save()
