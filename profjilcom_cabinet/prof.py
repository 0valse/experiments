import os
from re import compile, match, search
from requests_toolbelt.multipart.encoder import MultipartEncoder
import platform
from datetime import datetime
import pickle
import base64
import platform

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
adres_pomeshcheniya = 'submitted[dannye_zhilogo_pomeshcheniya][adres_pomeshcheniya]'
nomer_licevogo_scheta = 'submitted[dannye_zhilogo_pomeshcheniya][nomer_licevogo_scheta]'
hvs_hvs_schetchik_3 = 'submitted[hvs][hvs_schetchik_3]'  #//*[@id="edit-submitted-hvs-hvs-schetchik-3"]
hvs_hvs_schetchik_4 = 'submitted[hvs][schetchik_4]'  #//*[@id="edit-submitted-hvs-schetchik-4"]
gvs_gvs_schetchik_3 = 'submitted[gvs][gvs_schetchik_3]' #//*[@id="edit-submitted-gvs-gvs-schetchik-3"]
gvs_gvs_schetchik_4 = 'submitted[gvs][gvs_schetchik_4]'  #//*[@id="edit-submitted-gvs-gvs-schetchik-4"]
prochie_pokazaniya_obshchee = 'submitted[prochie_pokazaniya][obshchee]'  #//*[@id="edit-submitted-prochie-pokazaniya-obshchee"]


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

def num2month(num):
    months = {
        '1': "январь",
        '2': "февраль",
        '3': "март",
        '4': "апрель",
        '5': "май",
        '6': "июнь",
        '7': "июль",
        '8': "август",
        '9': "сентябрь",
        '10': "октябрь",
        '11': "ноябрь",
        '12': "декабрь"}
    return months.get(num)

def previos_month():
    cd = datetime.now().date().month
    if cd == 1:
        return str(12)
    else:
        return str(cd - 1)

def cur_month():
    return str(datetime.now().date().month)

def cur_year():
    return str(datetime.now().date().year)

def isodate_month(date):
    return str(datetime.strptime(date, '%Y-%m-%d').month)

def get_conf_dir():
    system = platform.system().lower()
    path = os.path.join(os.path.expanduser("~"), ".config", "profjilcom")
    if system == "windows":
        #windows config in С:\ Users \ [user name] \ AppData \ Local \ [ (Project Name) or (AssemblyCompany) ] \ [name project_cashBuild] \ [AssemblyVersion] \ user.config
        path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "profjilcom")
    return path



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
        # создать базу, если её нет
        ret = query.exec_("""
            CREATE TABLE IF NOT EXISTS {table} (
            {d} DATE NOT NULL,
            {hv} INTEGER NOT NULL,
            {hk} INTEGER NOT NULL,
            {gv} INTEGER NOT NULL,
            {gk} INTEGER NOT NULL,
            {t1} INTEGER NOT NULL,
            {t2} INTEGER NOT NULL,
            {T} INTEGER NOT NULL);""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user)
        )
        if not ret:
            print(query.lastError().text())

        # обеспечим уникальность всей совокупности данных за счёт индекса
        ret = query.exec_("""CREATE UNIQUE INDEX IF NOT EXISTS idx_pokazaniya ON {table}
                        ({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T});""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=user)
                        )
        if not ret:
            print(query.lastError().text())

        return ret

    def _test_data(self, user,
                   values={'HVS_vanna': '0', 'HVS_kuhnya': '8', 'GVS_vanna': '0',
                           'GVS_kuhnya': '5', 'T1': '349', 'T2': '13',
                           'Teplo': '41569', 'Date': '2016-01-25'}):
        query = QSqlQuery(self.db)
        query.prepare("""REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                        VALUES (date(:{d}), :{hv}, :{hk}, :{gv}, :{gk}, :{t1}, :{t2}, :{T});""".format(
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
            self.connect(os.path.join(get_conf_dir(), "prof.db"))

    def _reindex(self):
        query = QSqlQuery(self.db)
        ret = query.exec_('REINDEX idx_pokazaniya;')
        if not ret:
            print('reindex', query.lastError().text())
        return ret

    def save2db(self, user, kwargs, reindex=True):
        query = QSqlQuery(self.db)
        #дублирование записей
        query.prepare("""REPLACE INTO {table}({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T})
                        VALUES (date(:{d}), :{hv}, :{hk}, :{gv}, :{gk}, :{t1}, :{t2}, :{T});""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo,
            table=query.driver().escapeIdentifier(user, QSqlDriver.TableName))
        )

        query.bindValue(':%s' % Date, kwargs[Date])
        query.bindValue(':%s' % HVS_vanna, float(kwargs[HVS_vanna]))
        query.bindValue(':%s' % HVS_kuhnya, float(kwargs[HVS_kuhnya]))
        query.bindValue(':%s' % GVS_vanna, float(kwargs[GVS_vanna]))
        query.bindValue(':%s' % GVS_kuhnya, float(kwargs[GVS_kuhnya]))
        query.bindValue(':%s' % T1, float(kwargs[T1]))
        query.bindValue(':%s' % T2, float(kwargs[T2]))
        query.bindValue(':%s' % Teplo, float(kwargs[Teplo]))

        ret = query.exec_()
        if not ret:
            print(query.lastError().text())

        if reindex:
            self._reindex()

        return ret

    def save_all2db(self, user, args):
        self.db.transaction()
        for kwargs in args:
            self.save2db(user, kwargs, reindex=False)
        self._reindex()
        print('commit all', self.db.commit())

    def get_month_pokaz(self, user, month):
        query = QSqlQuery(self.db)
        s_str = '{}-{:02d}-%'.format(cur_year(), int(month))
        ret = query.exec_("""SELECT {d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T}
                FROM {table} WHERE {d} LIKE '{s_str}' ORDER BY {d} DESC;
                """.format(d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
                           gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, s_str=s_str,
                           table=query.driver().escapeIdentifier(user,
                                                        QSqlDriver.TableName)
                           )
                      )
        if not ret:
            print(query.lastError().text())
            return dict()
        query.first()

        return dict(
            Date=query.value(Date), HVS_vanna=query.value(HVS_vanna),
            HVS_kuhnya=query.value(HVS_kuhnya), GVS_vanna=query.value(GVS_vanna),
            GVS_kuhnya=query.value(GVS_kuhnya), T1=query.value(T1),
            T2=query.value(T2), Teplo=query.value(Teplo)
        )

    def get_last_pokaz(self, user):
        query = QSqlQuery(self.db)

        ret = query.exec_("""SELECT {d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T}
            FROM {table} ORDER BY {d} DESC;
            """.format(d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
                    gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo,
                    table=query.driver().escapeIdentifier(user,
                                                    QSqlDriver.TableName)
                        )
                    )
        if not ret:
            print(query.lastError().text())
            return dict()
        query.first()

        return dict(
            Date=query.value(Date), HVS_vanna=query.value(HVS_vanna),
            HVS_kuhnya=query.value(HVS_kuhnya), GVS_vanna=query.value(GVS_vanna),
            GVS_kuhnya=query.value(GVS_kuhnya), T1=query.value(T1),
            T2=query.value(T2), Teplo=query.value(Teplo)
        )



class Conf:
    config = ConfigParser()
    account = "ACCOUNT"
    COOKS = requests.utils.cookiejar_from_dict({'has_js': '1'})
    username = None
    last_update = datetime.now().date().isoformat()

    def __init__(self):
        self.conf_file = os.path.join(get_conf_dir(), "prof.ini")
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
        lst_upd = d.get("last_update", None)
        if lst_upd is None:
            self.last_update = datetime.now().date()
        else:
            self.last_update = datetime.strptime(lst_upd, '%Y-%m-%d').date()

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
        self.config.set(self.account, 'last_update',
            self.last_update.isoformat())
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
        try:
            r = requests.get(url, headers=headers, cookies=self.cookies)
        except:
            raise
        finally:
            r.close()
        self.response = r.text
        self.cookies.update(r.cookies)

        return r.status_code

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
        r = requests.post(auth_url, form, cookies=self.cookies,
                        headers=headers, allow_redirects=False)

        r.close()
        ret = r.ok

        self.cookies.update(r.cookies)

        if r.status_code == 302:
            print('auth', 302)
            r = requests.get(pokaz_url,
                             cookies=self.cookies, headers=headers)
            r.close()
            ret = r.ok

            if r.status_code == 403:
                raise NotAthorized("Not authorized access")

        self.cookies.update(r.cookies)  # update session cookies

        self.authorized = True
        self.username = user

        self.save()

        self.response = r.text

        return ret

    
    def send_pokazaniya(self, hvs_kuhnya, hvs_vannaya,
                        gvs_kuhnya, gvs_vannaya, t1, t2, teplo):
        #TODO: это костыльно. Подумать как построить правильно дерево сайта

        self.connect(pokaz_url)
        tree = etree.HTML(self.response)

        #with open('./doc.html', 'rb') as f:
        #    data = f.read()
        #    tree = etree.HTML(data)
        #pokaz_url = 'http://200ok-debian.rd.ptsecurity.ru:8000/post'

        xaddr = tree.xpath(
            """//*[@id="edit-submitted-dannye-zhilogo-pomeshcheniya-adres-pomeshcheniya"]"""
            )[0]
        adres = xaddr.get('value', "")

        xnum = tree.xpath(
            """//*[@id="edit-submitted-dannye-zhilogo-pomeshcheniya-nomer-licevogo-scheta"]"""
            )[0]
        nlic = xnum.get('value', "")

        xsid =  tree.xpath('''//*[@id="edit-details-sid"]''')[0]
        sid = xsid.get('value', '')
        
        xpage_num =  tree.xpath('''//*[@id="edit-details-page-num"]''')[0]
        page_num = xpage_num.get('value', '')
        
        xpage_count =  tree.xpath('''//*[@id="edit-details-page-count"]''')[0]
        page_count = xpage_count.get('value', '')
        
        xfinished =  tree.xpath('''//*[@id="edit-details-finished"]''')[0]
        finished = xfinished.get('value', '')
        
        xform_build_id = tree.xpath('''//*[@name="form_build_id"]''')[0]
        form_build_id = xform_build_id.get('value', '')
        
        xform_token =  tree.xpath('''//*[@id="edit-webform-client-form-1-form-token"]''')[0]
        form_token = xform_token.get('value', '')
        
        xform_id =  tree.xpath('''//*[@id="edit-webform-client-form-1"]''')[0]
        form_id = xform_id.get('value', '')

        xop = tree.xpath('''//*[@id="edit-submit"]''')[0]
        op = xop.get('value', '')

        hvs_schetchik_3 = ''  #//*[@id="edit-submitted-hvs-hvs-schetchik-3"]
        hvs_schetchik_4 = ''  #//*[@id="edit-submitted-hvs-schetchik-4"]
        gvs_schetchik_3 = '' #//*[@id="edit-submitted-gvs-gvs-schetchik-3"]
        gvs_schetchik_4 = ''  #//*[@id="edit-submitted-gvs-gvs-schetchik-4"]
        el_pokazaniya_obshchee = ''  #//*[@id="edit-submitted-prochie-pokazaniya-obshchee"]

        multipart_form_data = {
            adres_pomeshcheniya: adres,
            nomer_licevogo_scheta: nlic,
            hvs_hvs_kuhnya: hvs_kuhnya, 
            hvs_hvs_vannaya: hvs_vannaya,
            hvs_hvs_schetchik_3: hvs_schetchik_3,
            hvs_hvs_schetchik_4: hvs_schetchik_4,
            gvs_gvs_kuhnya: gvs_kuhnya,
            gvs_gvs_vannaya: gvs_vannaya,
            gvs_gvs_schetchik_3: gvs_schetchik_3,
            gvs_gvs_schetchik_4: gvs_schetchik_4,
            prochie_pokazaniya_elektroenergiya: t1,
            prochie_pokazaniya_t2_noch: t2,
            prochie_pokazaniya_obshchee: el_pokazaniya_obshchee,
            potreblenie_tepla_schetchik_1: teplo,
            'details[sid]': sid,
            'details[page_num]': page_num,
            'details[page_count]': page_count,
            'details[finished]': finished,
            'form_build_id': form_build_id,
            'form_token': form_token,
            'form_id': form_id,
            "op": op,
                }

        h = headers
        h['Origin'] = 'http://cabinet.profjilkom.ru'
        h['Upgrade-Insecure-Requests'] = '1'
        m = MultipartEncoder(multipart_form_data)
        h['Content-Type'] = m.content_type

        r = requests.post(pokaz_url, data=m, cookies=self.cookies,
                          headers=h, allow_redirects=True)
        r.close()
        print(r.status_code, r.is_redirect, r.headers, r.url)

        if r.status_code == 403:
            raise NotAthorized("Not authorized access")
        if not r.ok:
            raise ConnectionError("Coud not connect to %s. Errcode: %s" % (pokaz_url, r.status_code))
        ret = PokazaniyaDB().save2db(self.username,
                               dict(HVS_vanna=int(hvs_vannaya),
                                    HVS_kuhnya=int(hvs_kuhnya),
                                     GVS_vanna=int(gvs_vannaya),
                                     GVS_kuhnya=int(gvs_kuhnya),
                                     T1=int(t1), T2=int(t2),
                                     Teplo=int(teplo),
                                     Date=str(datetime.now().date().isoformat())
                                    )
                               )
        return ret

    def get_all_pokazaniya(self):
        # TODO: delet tested data
        #return [{'HVS_vanna': 38.0, 'HVS_kuhnya': 82.0, 'GVS_vanna': 48.0, 'GVS_kuhnya': 26.0, 'T1': 2616.0, 'T2': 718.0, 'Teplo': 11718.0, 'Date': '2017-03-26'}, {'HVS_vanna': 35.0, 'HVS_kuhnya': 78.0, 'GVS_vanna': 45.0, 'GVS_kuhnya': 25.0, 'T1': 2483.0, 'T2': 678.0, 'Teplo': 11174.0, 'Date': '2017-02-21'}, {'HVS_vanna': 30.0, 'HVS_kuhnya': 68.0, 'GVS_vanna': 39.0, 'GVS_kuhnya': 22.0, 'T1': 2016.0, 'T2': 578.0, 'Teplo': 9057.0, 'Date': '2016-12-26'}, {'HVS_vanna': 25.0, 'HVS_kuhnya': 64.0, 'GVS_vanna': 36.0, 'GVS_kuhnya': 21.0, 'T1': 1835.0, 'T2': 536.0, 'Teplo': 7999.0, 'Date': '2016-11-23'}, {'HVS_vanna': 22.0, 'HVS_kuhnya': 58.0, 'GVS_vanna': 32.0, 'GVS_kuhnya': 20.0, 'T1': 1603.0, 'T2': 473.0, 'Teplo': 7146.0, 'Date': '2016-10-25'}, {'HVS_vanna': 19.0, 'HVS_kuhnya': 53.0, 'GVS_vanna': 28.0, 'GVS_kuhnya': 18.0, 'T1': 1402.0, 'T2': 409.0, 'Teplo': 6477.0, 'Date': '2016-09-25'}, {'HVS_vanna': 16.0, 'HVS_kuhnya': 46.0, 'GVS_vanna': 24.0, 'GVS_kuhnya': 16.0, 'T1': 1268.0, 'T2': 335.0, 'Teplo': 6477.0, 'Date': '2016-08-23'}, {'HVS_vanna': 12.0, 'HVS_kuhnya': 39.0, 'GVS_vanna': 21.0, 'GVS_kuhnya': 15.0, 'T1': 1155.0, 'T2': 267.0, 'Teplo': 6477.0, 'Date': '2016-07-24'}, {'HVS_vanna': 9.0, 'HVS_kuhnya': 33.0, 'GVS_vanna': 21.0, 'GVS_kuhnya': 15.0, 'T1': 1045.0, 'T2': 219.0, 'Teplo': 6477.0, 'Date': '2016-06-23'}, {'HVS_vanna': 7.0, 'HVS_kuhnya': 28.0, 'GVS_vanna': 17.0, 'GVS_kuhnya': 13.0, 'T1': 943.0, 'T2': 171.0, 'Teplo': 6477.0, 'Date': '2016-05-24'}, {'HVS_vanna': 5.0, 'HVS_kuhnya': 24.0, 'GVS_vanna': 13.0, 'GVS_kuhnya': 11.0, 'T1': 854.0, 'T2': 137.0, 'Teplo': 6450.0, 'Date': '2016-04-23'}, {'HVS_vanna': 2.0, 'HVS_kuhnya': 18.0, 'GVS_vanna': 7.0, 'GVS_kuhnya': 8.0, 'T1': 696.0, 'T2': 83.0, 'Teplo': 5889.0, 'Date': '2016-03-23'}, {'HVS_vanna': 1.0, 'HVS_kuhnya': 13.0, 'GVS_vanna': 2.0, 'GVS_kuhnya': 6.0, 'T1': 526.0, 'T2': 28.0, 'Teplo': 5062.0, 'Date': '2016-02-20'}, {'HVS_vanna': 0.0, 'HVS_kuhnya': 8.0, 'GVS_vanna': 0.0, 'GVS_kuhnya': 5.0, 'T1': 349.0, 'T2': 13.0, 'Teplo': 41569.0, 'Date': '2016-01-25'}]
        # get main page
        r = requests.get(archive_url,
                         cookies=self.cookies, headers=headers)
        r.close()
        tree = etree.HTML(r.text)
        line = 1
        tmp = list()
        # ищем только цифры (с десятичной запятой или точкой)
        m = compile(r'\d+[,.]{0,1}\d*')

        '''
        tree = etree.HTML(html)
        for block in tree.xpath("//div[@class='product']"):
            img = block.xpath("//img/@src")[0]
            name = block.xpath("//tr[@class='name']")[0].text
            id = block.xpath("//tr[@class='id']")[0].text
        '''
        # good parse HTML https://habrahabr.ru/post/220125/

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
            # очень костыльно и криво сделано
            # нужно: что есть такой xpath; проверять, что найдены цифры

            # на сайте в показаниях отделяются тысячи с помощью ","
            hvs_kuhnya = int(m.match(p.xpath('//*[@id="edit-submitted-hvs-hvs-kuhnya"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            hvs_vannaya = int(m.match(p.xpath('//*[@id="edit-submitted-hvs-hvs-vannaya"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            gvs_kuhnya = int(m.match(p.xpath('//*[@id="edit-submitted-gvs-gvs-kuhnya"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            gvs_vannaya = int(m.match(p.xpath('//*[@id="edit-submitted-gvs-gvs-vannaya"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            t1 = int(m.match(p.xpath('//*[@id="edit-submitted-prochie-pokazaniya-elektroenergiya"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            t2 = int(m.match(p.xpath('//*[@id="edit-submitted-prochie-pokazaniya-t2-noch"]')[0].xpath('text()')[0]).group(0).replace(',', ''))
            teplo = int(m.match(p.xpath('//*[@id="edit-submitted-potreblenie-tepla-schetchik-1"]')[0].xpath('text()')[0]).group(0).replace(',', ''))

            tmp.append(dict(HVS_vanna=hvs_vannaya, HVS_kuhnya=hvs_kuhnya,
                            GVS_vanna=gvs_vannaya, GVS_kuhnya=gvs_kuhnya,
                            T1=t1, T2=t2, Teplo=teplo,
                            Date=str(datetime.strptime(date.replace(" ", ""),
                                        '%m/%d/%Y-%H:%M').date().isoformat()))
                       )
            line += 1

        print(tmp)

        self.last_update = datetime.now().date()
        self.save()

        return tmp
