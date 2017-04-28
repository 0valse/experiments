#!/usr/bin/env python

from PyQt5.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery, QSqlDriver, QSqlIndex
from PyQt5.QtCore import Qt


class DBFail(Exception):
    pass


#example db woarking https://github.com/md2/pyhomelib/blob/master/pyhomelib/db.py
#https://github.com/Freeseer/freeseer

class MainDatabase(QSqlDatabase):
	def __init__(self, dbname, *args, **kwargs):
		super(MainDatabase, self).__init__(args, kwargs)
		self.addDatabase('QSQLITE')
        self.setDatabaseName(dbname)
        self.connect_db()

	def connect_db(self):
        if not self.db.open():
            raise DBFail("Cann`t connect to db")

    def __del__(self):
        if self.isOpen():
            self.close()
        super(MainDatabase, self).__del__()

    def drop_table(self):
    	query = QSqlQuery()
    	ret = query.exec_("""DROP TABLE IF NOT EXISTS {};
    			""".format(
    				query.driver().escapeIdentifier(self.databaseName(),
    											QSqlDriver.TableName)
    				)
    	)
    	if not ret:
            print(query.lastError().text())
        return ret

    def create_table(self):
        query = QSqlQuery()
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
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo, table=self.databaseName())
        )
        if not ret:
            print(query.lastError().text())

        # обеспечим уникальность всей совокупности данных за счёт индекса
        ret = query.exec_("""CREATE UNIQUE INDEX IF NOT EXISTS idx_pokazaniya ON {table}
                        ({d}, {hv}, {hk}, {gv}, {gk}, {t1}, {t2}, {T});""".format(
            d=Date, hv=HVS_vanna, hk=HVS_kuhnya, gv=GVS_vanna,
            gk=GVS_kuhnya, t1=T1, t2=T2, T=Teplo,
            table=query.driver().escapeIdentifier(self.databaseName(),
            									QSqlDriver.TableName)
            )
        )
        if not ret:
            print(query.lastError().text())

        return ret



class ProfJilComModel():
	def __init__(self, parent, db, table):
		self.db = MainDatabase()
		self.table = table

		super(ProfJilComModel, self).__init__(parent, db)

		self.connect()

        self.setTable(table)

        self.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.setHeaderData(0, Qt.Horizontal, "Дата")
        self.setHeaderData(1, Qt.Horizontal, 'ХВС Кухня, м3')
        self.setHeaderData(2, Qt.Horizontal, 'ХВС Ванная, м3')
        self.setHeaderData(3, Qt.Horizontal, 'ГВС Кухня, м3')
        self.setHeaderData(4, Qt.Horizontal, 'ГВС Ванная, м3')
        self.setHeaderData(5, Qt.Horizontal, "Электричество День, КВт")
        self.setHeaderData(6, Qt.Horizontal, "Электричество Ночь, КВт")
        self.setHeaderData(7, Qt.Horizontal, "Отопление, КВт")

    

     def save2db(self, user, kwargs, reindex=True):
     	'''
     	Здесь показано, как вставить строку и заполнить ее:
     model.insertRows(row, 1);
     model.setData(model.index(row, 0), 1013);
     model.setData(model.index(row, 1), "Peter Gordon");
     model.setData(model.index(row, 2), 68500);
     model.submitAll();
     	'''
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
    
	def del_row(self, num):
		'''Пример удаления пяти следующих друг за другом строк:
     	model.removeRow(5);
     	model.submitAll();'''
     	self.removeRow(num)
     	self.submitAll()


    def _reindex(self):
        query = QSqlQuery(self.db)
        ret = query.exec_('REINDEX idx_pokazaniya;')
        if not ret:
            print('reindex', query.lastError().text())
        return ret

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
