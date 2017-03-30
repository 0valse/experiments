import requests
from re import search
from configparser import ConfigParser
import os

url = 'http://cabinet.profjilkom.ru/'

captcha_img = r'<img\ssrc="(/image_captcha/\d+/\d+)"\s(.+)'
captcha_sid = r'<input\stype="hidden"\sname="captcha_sid"\sid="edit-captcha-sid"\svalue="(.+)"'
captcha_token = r'<input\stype="hidden"\sname="captcha_token"\sid="edit-captcha-token"\svalue="(.+)"'
form_id_value = r'<input type="hidden"\sname="form_build_id"\sid=".+"\svalue="(.+)"'
form_id = r'<input\stype="hidden"\sname="form_build_id"\sid="(.+)"\svalue=".+"'

hvs_hvs_kuhnya = 'submitted[hvs][hvs_kuhnya]'
hvs_hvs_vannaya = 'submitted[hvs][hvs_vannaya]'
gvs_gvs_kuhnya = 'submitted[gvs][gvs_kuhnya]'
gvs_gvs_vannaya = 'submitted[gvs][gvs_vannaya]'
prochie_pokazaniya_elektroenergiya = 'submitted[prochie_pokazaniya][elektroenergiya]'
prochie_pokazaniya_t2_noch = 'submitted[prochie_pokazaniya][t2_noch]'
potreblenie_tepla_schetchik_1 = 'submitted[potreblenie_tepla][schetchik_1]'

headers = {'User-agent': 'Mozilla/5.0', 
            'Accept-Encoding': ', '.join(('gzip', 'deflate')),
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'Referer': 'http://cabinet.profjilkom.ru/node/1'}


class Conf:
    c = ConfigParser()
    section = "COOKIES"

    def __init__(self):
        if os.environ.get('HOME', None) is not None:
            self.conf_file = os.path.join(os.path.expanduser("~"),
                                          ".config", "prof.ini")
        if os.path.isfile(self.conf_file):
            self.c.read_file(self.conf_file)
            self.c.set(self.section, 'has_js', '1')
        if not self.c.has_section(self.section):
            self.c.add_section(self.section)


    def get_cookies(self):
        cook = dict()
        for v, k in self.c.items(self.section):
            cook[v] = k
        return requests.cookies.cookiejar_from_dict(cook)

    def set_cookie(self, cookies):
        assert type(cookies, (requests.cookies.RequestsCookieJar, dict)), "cookie must have a cookie type"
        [self.c.set(self.section, k, v) for v, k in cookies.items()]

    def _update(self):
        with open(self.conf_file, 'w') as f:
            self.c.write(f)

class NotAthorized(ConnectionError):
    pass

class Profjilcom:
    conf = Conf()

    def __init__(self):
        self.response = None
        self.form_id = None
        self.form_value = None
        self.captcha_sid = None
        self.captcha_token = None
        self.captcha_img = None

        self.authorized = False
        self.cookies = self.conf.get_cookies()

        self._connect()

    def _connect(self):
        resp = requests.get(url, headers=headers, cookies=self.cookies)
        resp.close()
        if resp.status_code == 403:
            raise NotAthorized("Not authorized access")
        if not resp.ok:
            raise ConnectionError("Coud not connect to %s. Code: %s" % (url, resp.status_code))
        self.response = resp.content.decode()
        self._form()  # form sets

    def _form(self):
        sf_id = search(form_id, self.response)
        if not sf_id:
            raise ConnectionError("No sf_id find")
        self.form_id = sf_id.group(1)
        
        sf_id_val = search(form_id_value, self.response)
        if not sf_id_val:
            raise ConnectionError("No sf_id_val find")
        self.form_value = sf_id_val.group(1)
        
        ca_sid =  search(captcha_sid, self.response)
        if not ca_sid:
            raise ConnectionError("No ca_sid find")
        self.captcha_sid = ca_sid.group(1)
        
        ca_tok = search(captcha_token, self.response)
        if not ca_tok:
            raise ConnectionError("No ca_tok find")
        self.captcha_token = ca_tok.group(1)
        
        return True
    
    def get_capcha_img(self):
        s = search(captcha_img, self.response)
        if not s:
            raise ConnectionError("No capcha img url find")
        capcha_url = url + s.group(1)
        r = requests.get(capcha_url, headers=headers)
        r.close()
        if not r.ok:
            raise ConnectionError("Coud not connect to %s" % url)
        self.captcha_img = r.content

    
    def logout(self):
        #form = {
        #    "op": '%D0%9E%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D0%B8%D1%82%D1%8C',  # отправить
        #        }
        #r = requests.post('http://cabinet.profjilkom.ru/node/1',
                        # form, cookies=self.cookies, headers=headers,
        #                  allow_redirects=False)
        #r.close()
        #if not r.ok:
        #    raise Exception("Coud not connect to %s. Errcode: %s" % (url, r.status_code))
        #return r.status_code
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
        r = requests.post(url+'/node/1?destination=node%2F1', form,
                          cookies=self.cookies, headers=headers, allow_redirects=False)
        r.close()
        self.cookies.update(r.cookies)

        if r.status_code == 302:
            r = requests.get('http://cabinet.profjilkom.ru/node/1',
                             cookies=self.cookies, headers=headers)
            r.close()
            if r.status_code == 402:
                raise NotAthorized("Not authorized access")

        self.authorized = True
        self.conf.set_cookie(self.cookies)

    
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
        r = requests.post('http://cabinet.profjilkom.ru/node/1', form, cookies=self.cookies,
                          headers=headers, allow_redirects=False)
        r.close()
        if r.status_code == 403:
            raise NotAthorized("Not authorized access")
        if not r.ok:
            raise ConnectionError("Coud not connect to %s. Errcode: %s" % (url, r.status_code))
        return r.status_code, r
