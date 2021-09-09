# siu77777 // tu889955
# GameLayerManager.Instance.showMultiBet()
# 멀티배팅 화면 띄우기
# GameLayerManager.Instance.sceneLayer.$children[0]
# .ChangePanel({currentTarget: GameLayerManager.Instance.sceneLayer.$children[0].tabList.getChildAt(1)})
# 게임 종류 선택 0: 모든 1: 바카라 2: 스페셜 3: 라이브
# SceneMultiBet
# GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children[$1]._host.records
# window.user._hosts[0].records 동일
# 테이블 기록 $ <- 테이블 번호
# GameLayerManager.Instance.sceneLayer.$children[0].refreshView()
# 테이블 새로고침
# GameLayerManager.Instance.sceneLayer.$children[0].lobbyFooter.btnRefreshBalance
# GameLayerManager.Instance.sceneLayer.$children[0]
# .lobbyFooter.onBtnTap({currentTarget: GameLayerManager
# .Instance.sceneLayer.$children[0].lobbyFooter.btnRefreshBalance})

# 670 change 값 받아야함!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# 776 change 값 받아야함!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
import configparser
import datetime
import itertools
import logging
import os
import random
import shutil
import threading
import time
import timeit
import ctypes
from logging import handlers

import pymysql.cursors
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QAbstractItemView
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from gs1 import GS

form_class = uic.loadUiType('main.ui')[0]
form_class2 = uic.loadUiType('main1.ui')[0]


class Info(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._url, self._id, self._id2, self._pw = "", "", "", ""

        if os.path.isfile("./info.txt"):
            with open('./info.txt', 'r') as file:
                try:
                    s = file.read().split(',')
                    self.id.setText(s[0])
                    self.id_2.setText(s[1])
                    self.pw.setText(s[2])
                except:
                    pass
        self.run_btn.clicked.connect(self.run_btn_clicked)

    def run_btn_clicked(self):
        _url = self.url.currentText()
        _id = self.id.text()
        _id2 = self.id_2.text()
        _pw = self.pw.text()
        data = f"{_id},{_id2},{_pw}"
        with open('./info.txt', 'w') as file:
            file.write(data)

        widget.setFixedWidth(600)
        widget.setCurrentIndex(widget.currentIndex()+1)
        time.sleep(1)
        # login.hide()
        # window.show()
        # print('change')
        window.run1(_url, _id, _id2, _pw)


class Runner(QMainWindow, form_class2):
    finished = pyqtSignal()
    updateProgress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.disponly = []
        self.setupUi(self)
        self.finished.connect(self.update)
        # self.updateProgress.connect(self.datadisplay())
        self.qtnum, self.change, = 0, 0
        self.totnum = []
        self.notStart = True
        timer1 = QTimer(self)
        timer1.start(1000)
        timer1.timeout.connect(self.disp)
        run_path = os.path.dirname(os.path.abspath(__file__))
        self.gs = GS(self, os.path.join(run_path, "setting.conf"))
        self.thread1 = object

    def closeEvent(self, event):
        self.deleteLater()

    def disp(self):
        if self.disponly and self.totnum:
            self.datadisplay(self.disponly)
        if not self.notStart:
            self.thread1.notstart = False
            self.thread1.change = self.change
        if self.qtnum % 2 == 0:
            # 화면단 필요한 자료
            pass

        self.qtnum += 1

    def update(self):
        # self.datadisplay(data, 1)
        pass

    # 화면 띄우기
    def datadisplay(self, data):
        self.csHistory.setRowCount(len(self.totnum))
        rowPosition = self.csHistory.rowCount()
        try:
            for v in self.totnum:
                # print(f"v['subnum'] : {v['subnum']}, data[0] : {data[0]}")
                if int(v['subnum']) != int(data[0]):
                    continue
                for i in range(0, 11):
                    item = QTableWidgetItem(str(data[i]))
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    if rowPosition % 2 == 1:    item.setBackground(QtGui.QColor(250, 250, 250))
                    self.csHistory.setItem(v['position'], i, item)
        except Exception as ex:
            print(f'err {ex}')

        self.csHistory.resizeColumnToContents(0)
        self.csHistory.resizeRowsToContents()
        self.csHistory.setEditTriggers(QAbstractItemView.NoEditTriggers)  # edit 금지 모드

    def run1(self, _url, _id, _id2, _pw):
        try:
            self.th1 = Thread1(self.gs, _url, _id, _id2, _pw)
            # self.gs.setup(self.url_text, self.id_text, self.id2_text, self.pw_text)
            self.th1.start()

            self.thread1 = Runner2(self, self.gs, _url, _id, _id2, _pw)
            self.thread1.start()

        except Exception as ex:
            print(ex)
            print("타임아웃 에러 만들기")


class Runner2(QThread):

    def __init__(self, parent, gs, _url, _id, _id2, _pw):
        super().__init__(parent)
        self.parent = parent
        self.gs = gs
        # self.setupUi(self)
        self._CONF_DB_KEY = "DB"
        self._CONF_SITE_KEY = "SITE"
        self._CONF_SERVICE_KEY = "SERVICE"
        self._DEFAULT_CONF_DB = ["db_host", "db_port", "db_user", "db_pwd", "db_name"]
        self._DEFAULT_CONF_SITE = ["site_url", "site_id_selector", "site_pwd_selector", "sagame_id", "site_id", "site_pwd", "site_game_selector"]
        self._DEFAULT_CONF_SERVICE = ['default_timeout', "default_delay", "scan_speed", "table_min_size"]

        self._config = configparser.ConfigParser()
        self._config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "setting.conf"), encoding="utf8")
        self._check_config()

        self._db_conf = self._config[self._CONF_DB_KEY]
        self._service_conf = self._config[self._CONF_SERVICE_KEY]

        self._default_delay = int(self._service_conf["default_delay"])
        self._default_timeout = int(self._service_conf["default_timeout"])

        self.conn = pymysql.connect(host=self._config["DB"]["DB_HOST"],
                                    user=self._config["DB"]["DB_USER"],
                                    password=self._config["DB"]["DB_PWD"] if self._config["DB"][
                                                                                 "DB_PWD"] != ";" else None,
                                    db=self._config["DB"]["DB_NAME"],
                                    charset="utf8",
                                    port=int(self._config["DB"]["DB_PORT"]))

        self.cossql = "SELECT DATE_FORMAT(date,'%Y-%m-%d %H:%i:%s') AS date, step, ta, bp, beBP FROM " \
                      "(SELECT date, step, ta, bp, beBP FROM sub01save use index (idx_datename) " \
                      "WHERE date BETWEEN DATE_ADD(now(), INTERVAL -1200 second) AND now() AND " \
                      "name = 'NG') AS dout ORDER BY dout.date DESC"

        self.cossql1 = "SELECT DATE_FORMAT(date,'%Y-%m-%d %H:%i:%s') AS date, step, ta, bp, beBP FROM " \
                       "(SELECT date, step, ta, bp, beBP FROM sub01save use index (idx_datename) " \
                       "WHERE date BETWEEN DATE_ADD(now(), INTERVAL -25 second) AND now() AND " \
                       "name = 'NG') AS dout ORDER BY dout.date DESC"

        self.sqldatasql = "SELECT DATE_FORMAT(date,'%Y-%m-%d %H:%i:%s') AS date, name, step, bp, ta FROM " \
                          "(SELECT date, name, step, bp, ta FROM sub01saveB use index (idx_datename) " \
                          "WHERE date BETWEEN DATE_ADD(now(), INTERVAL -25 second) AND now() AND " \
                          "name = '{}') AS dout "

        self.sqlT = "SELECT host_id AS ta, DATE_FORMAT(CD,'%Y-%m-%d %H:%i:%s') AS CD FROM " \
                    "(SELECT host_id, create_datetime AS CD FROM games1 use index (cd_idx) " \
                    "WHERE create_datetime BETWEEN DATE_ADD(now(), INTERVAL -25 second) AND now()) AS dout "

        self.insertquery = "INSERT INTO sub10%s VALUES(null, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"

        self.attDatasql = "SELECT DATE_FORMAT(date,'%Y-%m-%d %H:%i:%s') AS date, name, step, bp, ta, beBP FROM " \
                          "(SELECT date, name, step, bp, ta, beBP FROM sub01save use index (idx_datename) " \
                          "WHERE date BETWEEN DATE_ADD(now(), INTERVAL -25 second) AND now() AND " \
                          "name = 'NG') AS dout"

        self.attSaveData = 'UPDATE sub10save SET ' \
                           'NG = "%s", OG = "%s", BG = "%s", BB = "%s", YJ = "%s", YK = "%s" ' \
                           'WHERE id = "%s" AND driving = "%s"'

        self.driving = ''
        self.last_update, self.timecash = 0.0, 0.0
        self.from_db, self.table_no = [], []
        self.dbcnt, self.table_noCnt, self.ctrlCnt = 0, 0, 0
        self.cosFirst, self.notstart, self.ctrldata, self.attack, self.delcash = True, True, True, False, True
        self.dbtablesum, self.dt, self.dispdata = [], [], []
        self.change, self.clicktime, self.attno = 0, 0, 0
        self.money0, self.money1, self.money2 = 0, 0, 0
        self.ctrlNG, self.ctrlOG, self.ctrlBG, self.ctrlBB, self.ctrlYJ, self.ctrlYK = [], [], [], [], [], []

        formatter = logging.Formatter('%(asctime)s %(message)s')
        # self.logger1 = 매수 로그 남기기
        fh1 = handlers.TimedRotatingFileHandler(filename='infodata/1infoStart.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh1.setFormatter(formatter)
        fh1.suffix = '%m-%d.txt'
        fh1.setLevel(logging.INFO)
        self.logger1 = logging.getLogger("my1")
        self.logger1.setLevel(logging.INFO)
        self.logger1.addHandler(fh1)
        self.logger1.propagate = False
        self.logger1.info("===================start====================")
        # self.logger2 = 편입, 이탈 로그 남기기
        fh2 = handlers.TimedRotatingFileHandler(filename='infodata/2infoAttack.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh2.setFormatter(formatter)
        fh2.suffix = '%m-%d.txt'
        fh2.setLevel(logging.INFO)
        self.logger2 = logging.getLogger("my2")
        self.logger2.setLevel(logging.INFO)
        self.logger2.addHandler(fh2)
        self.logger2.propagate = False
        self.logger2.info("===================start====================")

        # # self.logger3 = 미체결 취소 로그 남기기
        fh3 = handlers.TimedRotatingFileHandler(filename='infodata/3infoCheck.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh3.setFormatter(formatter)
        fh3.setLevel(logging.INFO)
        self.logger3 = logging.getLogger("my3")
        self.logger3.setLevel(logging.INFO)
        self.logger3.addHandler(fh3)
        self.logger3.propagate = False
        self.logger3.info("==================================start====================================")

        # # self.logger4 = 시간체크
        fh4 = handlers.TimedRotatingFileHandler(filename='infodata/4timeCheck.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh4.setFormatter(formatter)
        fh4.setLevel(logging.INFO)
        self.logger4 = logging.getLogger("my4")
        self.logger4.setLevel(logging.INFO)
        self.logger4.addHandler(fh4)
        self.logger4.propagate = False
        self.logger4.info("==================================start====================================")

        # # self.logger5 = 기타 잡다
        fh5 = handlers.TimedRotatingFileHandler(filename='infodata/5otherCheck.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh5.setFormatter(formatter)
        fh5.setLevel(logging.INFO)
        self.logger5 = logging.getLogger("my5")
        self.logger5.setLevel(logging.INFO)
        self.logger5.addHandler(fh5)
        self.logger5.propagate = False
        self.logger5.info("==================================start====================================")

        self._url, self._id, self._id2, self._pw = _url, _id, _id2, _pw

    def run(self):
        try:
            if self._id:
                while self.notstart:
                    time.sleep(1)
                self.last_update = time.time()
                self._health_checker()
                while 1:
                    self.insert_table()

                    if self.delcash:
                        self.timecash = time.time()
                        self.delcash = False

                    if (time.time() - self.timecash) > 300*5:
                        if os.path.isdir("./emp"):
                            os.chdir("./emp")
                            for i in os.listdir():
                                try:
                                    shutil.rmtree(i)  # 쿠키 / 캐쉬파일 삭제
                                except Exception as ex:
                                    # print(ex)
                                    pass
                            # self.gs.driver.delete_all_cookies()
                            os.chdir("../")
                            self.delcash = True
                            print('delcash')
                            self.logger5.info('delcash')

        except Exception as ex:
            print(ex)

    def find_ddata(self, data, no):
        delnum = []
        for i, v in enumerate(data):
            if v['no'] == no:
                delnum.append(i)
                self.ctrlCnt -= 1
                break
        return reversed(delnum)

    def del_data(self, algo, no):
        if self.attack:
            if algo == "NG" and self.ctrlNG:
                for k in self.find_ddata(self.ctrlNG, no): del self.ctrlNG[k]
            elif algo == "OG" and self.ctrlOG:
                for k in self.find_ddata(self.ctrlOG, no): del self.ctrlOG[k]
            elif algo == "BG" and self.ctrlBG:
                for k in self.find_ddata(self.ctrlBG, no): del self.ctrlBG[k]
            elif algo == "BB" and self.ctrlBB:
                for k in self.find_ddata(self.ctrlBB, no): del self.ctrlBB[k]
            elif algo == "YJ" and self.ctrlYJ:
                for k in self.find_ddata(self.ctrlYJ, no): del self.ctrlYJ[k]
            elif algo == "YK" and self.ctrlYK:
                for k in self.find_ddata(self.ctrlYK, no): del self.ctrlYK[k]

            self.logger1.info(f'cancel attack no : {no}')
            if not self.ctrlNG and not self.ctrlOG and not self.ctrlBG and not self.ctrlBB and \
                    not self.ctrlYJ and not self.ctrlYK:
                self.attack = False

    def from_dbdata(self):
        _id2 = self._id2
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(f"SELECT * FROM sub10 WHERE start = 't' AND id = '{_id2}'")
            result = cursor.fetchall()
            cursor.execute(f"SELECT * FROM sub10 WHERE start = 'f' AND id = '{_id2}'")
            result1 = cursor.fetchall()

        if result:
            self.logger1.info(f'from_dbdata result')
            for i in result:
                # print(data)
                noData = True
                for z in self.from_db:
                    if z['no'] == i['no']:
                        noData = False
                if noData:
                    print(f'start : {i}')
                    self.parent.totnum.append({'subnum': i['subnum'], 'position': self.dbcnt})
                    self.dbcnt += 1
                    i['readtable'] = 't'
                    self.cosFirst = True
                    # cursor.execute(f"UPDATE sub10 SET readtable = 't' WHERE no = '{str(i['no'])}'")
                    self.from_db.append(i)
                    self.logger1.info(f'from_db : {self.from_db}')
                    with self.conn.cursor(pymysql.cursors.DictCursor) as cursor1:
                        cursor1.execute("SELECT ta FROM sub01save use index (idx_date) "
                                        "WHERE date BETWEEN DATE_ADD(now(), INTERVAL -60 minute) AND now() GROUP BY ta")
                        table_no_org = cursor1.fetchall()
                    table = {}
                    for k, v in enumerate(i['tableno']):
                        if i['tableno'][k] == 't':
                            try:
                                n = k + 1
                                table[str(n)] = table_no_org[k]['ta']
                                table[str(n) + 'date'] = 'f'
                                table[str(n) + 'tf'] = 'f'
                                table[str(n) + 'beBP'] = 'f'
                                table[str(n) + 'chBP'] = 'f'
                                self.table_noCnt += 1
                            except:
                                pass
                    self.table_no.append(table)
                    self.logger1.info(f'table_no : {self.table_no}')
                    self.ctrldata = True

        if result1:
            self.logger1.info(f'from_dbdata result1')
            for i in result1:
                inData = False
                # inData = [True for z in self.from_db if z['no'] == i['no']]
                for z in self.from_db:
                    if z['no'] == i['no']:
                        inData = True

                if inData:
                    delnum = i['no']
                    print(f'스톱 : {i["no"]}')
                    index = [j for j, v in enumerate(self.from_db) if int(delnum) == self.from_db[j]['no']][0]
                    self.logger1.info(f'remove data : {delnum}')
                    self.del_data(self.from_db[index]['sub1001'], self.from_db[index]['no'])
                    del self.from_db[index]
                    ta = self.table_no[index]
                    for n, val3 in enumerate(ta):
                        if n % 5 == 0:
                            self.table_noCnt -= 1
                    del self.table_no[index]
                    self.dbcnt -= 1
                    self.logger1.info(f'남은 from_db : {self.from_db}')
                    for dei, dev in self.parent.totnum:
                        if dev['subnum'] == i['subnum']:
                            del self.parent.totnum[dei]

        self.conn.commit()
        # if not result and not result1:
        #     print("result 음슴")

    def chktable(self):
        self.logger1.info(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, {str(self.table_no)}')
        # print(self.from_db)

    def checkover_step(self):
        self.logger1.info('checkover_step1')
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor2:
            if self.cosFirst:
                cursor2.execute(self.cossql)
                self.cosFirst = False
            else:
                cursor2.execute(self.cossql1)
            result2 = cursor2.fetchall()
            self.logger2.info(f'cos result : {result2}')
        for i, val in enumerate(self.from_db):
            pass1 = True
            ta = self.table_no[i]
            for n, val3 in enumerate(ta):
                if n % 5 == 0:
                    tname = ta[str(val3)]
                    d = val3 + 'tf'
                    ttf = ta[d]
                elif n % 5 == 2 and ttf != 'f' and ttf != 't':
                    aftertime = 0 if val['sub1004'] == '' else int(val['sub1004'])
                    tpass = False
                    # 시간 비교함수 활용
                    if val['sub1003'] == 'c' and datetime.datetime.strptime(ttf, "%Y-%m-%d %H:%M:%S") + \
                            datetime.timedelta(minutes=aftertime) < datetime.datetime.now():
                        tpass = True
                        ctmoney = 0
                    elif val['sub1003'] == 's':
                        tpass = True
                        ctmoney = int(aftertime) * 1000
                    if tpass:
                        print(f'--timepass {tname}')
                        self.table_no[i][val3] = 't'
                        p, b = val['sub1015'], val['sub1016']
                        if p and b:
                            bp = p + b
                        elif p:
                            bp = p
                        elif b:
                            bp = b
                        # 1,7,8,9,10,11,12, amoset
                        ctrl = {"no": val["no"], "lnum": val["subnum"], "ta": tname, "readTime1": "", "readTime2": "", "attack": "f",
                                "attNo": 0, "attTime": "", "attBP": "", "TieTime": "",
                                "acstart": "f", "beBP": "", "autoctl": "f", "cruse": "f", "ng1": "f",
                                "sncnt": 0, "rccnt": 0, "step": 0,
                                "amoset": 0, "attmoney": 0, "resultmoney": 0,
                                "ctmoney": ctmoney, "cresultmoney": 0, "cttopP": 0, "cttopN": 0,
                                "wincnt": 0, "losecnt": 0, "totcnt": 0, "lastwl": "", "bp": bp,
                                "sub1001": val["sub1001"], "sub1007": val["sub1007"], "sub1008": val["sub1008"],
                                "sub1009": val["sub1009"], "sub1010": val["sub1010"], "sub1011": val["sub1011"],
                                "sub1012": val["sub1012"], "sub1014": val["sub1014"], "sub1017": val["sub1017"],
                                "sub1018": val["sub1018"], "sub1019": val["sub1019"], "amosetorg": val["amoset"]
                                }
                        self.logger1.info(f'add ctrl : {ctrl}')
                        self.ctrlCnt += 1
                        if val['sub1001'] == "NG":
                            self.ctrlNG.append(ctrl)
                        elif val['sub1001'] == "OG":
                            self.ctrlOG.append(ctrl)
                        elif val['sub1001'] == "BG":
                            self.ctrlBG.append(ctrl)
                        elif val['sub1001'] == "BB":
                            self.ctrlBB.append(ctrl)
                        elif val['sub1001'] == "YJ":
                            self.ctrlYJ.append(ctrl)
                        elif val['sub1001'] == "YK":
                            self.ctrlYK.append(ctrl)
                        self.attack = True
                        # print(self.table_no)

                if n % 5 == 2 and ttf == 'f':
                    pass1 = False

            if pass1: continue
            if result2:
                for k in result2:
                    for n, val3 in enumerate(ta):
                        if ta[str(val3)] == k["ta"]:
                            a, b = val3 + 'date', val3 + 'beBP'
                            if self.table_no[i][a] == 'f':
                                self.table_no[i][a] = k['date']
                                self.table_no[i][b] = k['bp']
                                self.logger1.info(f'add table info : {self.table_no[i]}')
                                # datetime.datetime.strptime(self.table_no[i][a], "%Y-%m-%d %H:%M:%S")
                            elif self.table_no[i][a] < k['date']:
                                c = val3 + 'chBP'
                                if self.table_no[i][c] == 'f':
                                    if self.table_no[i][b] != k["bp"]:
                                        self.table_no[i][a] = k['date']
                                        self.table_no[i][c] = 't'
                                        info = f'--changebp pass table {k["ta"]}'
                                        print(info)
                                        self.logger1.info(info)
                                        self.logger1.info(self.table_no[i])

                                        if int(val["sub1002"]) <= 0:
                                            d = val3 + 'tf'
                                            self.table_no[i][d] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            info2 = f'--step pass {k["ta"]}'
                                            print(info2)
                                            self.logger1.info(info2)
                                            self.logger1.info(self.table_no[i])

                                else:
                                    if int(k["step"]) >= int(val["sub1002"]):
                                        # print(f'넘어간 번호 : {val3}')
                                        d = val3 + 'tf'
                                        # print(f'수정 번호 : {a}')
                                        if self.table_no[i][d] == 'f':
                                            self.table_no[i][d] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            self.logger1.info(f'stepDB {result2}')
                                            info2 = f'--step pass {k["ta"]}'
                                            print(info2)
                                            self.logger1.info(info2)
                                            self.logger1.info(self.table_no[i])
        self.conn.commit()

    def attinfo2(self, ctrldata, result, bp, step):
        if bp == 'P':
            ctrldata['readTime1'] = result['date']
        else:
            ctrldata['readTime2'] = result['date']
        if datetime.datetime.now() < datetime.datetime.strptime(ctrldata['sub1018'], "%Y-%m-%d %H:%M") \
                and float(ctrldata['resultmoney']) < float(ctrldata['sub1014'] * 1000) \
                and self.change < int(ctrldata['sub1019']) * 1000:
            self.logger3.info(f'attack bp : {bp}')
            if ctrldata['sub1001'] == "NG" and result['beBP'] != result['bp'] and bp == result['bp'] and ctrldata[
                'ng1'] == 't' \
                    or ctrldata['sub1001'] == "OG" and result['beBP'] != result['bp'] and bp != result['bp'] and \
                    ctrldata['ng1'] == 't' \
                    or ctrldata['sub1001'] == "NG" and result['beBP'] == result['bp'] and bp == result['bp'] \
                    or ctrldata['sub1001'] == "OG" and result['beBP'] == result['bp'] and bp != result['bp'] \
                    or ctrldata['sub1001'] == "BG" and bp == result['bp'] \
                    or ctrldata['sub1001'] == "BB" and bp != result['bp'] \
                    or ctrldata['sub1001'] == "YJ" and bp != result['bp'] \
                    or ctrldata['sub1001'] == "YK" and bp == result['bp']:
                ctrldata['attack'] = 't'
                ctrldata['attTime'] = result['date']
                ctrldata['attBP'] = bp
                ctrldata['step'] = step
                self.attno = self.attno + 1
                ctrldata['attno'] = self.attno

            if ctrldata['attack'] == 't':
                mon = ctrldata['amosetorg'].split('|')
                mon2 = mon[ctrldata['amoset']].split(',')
                ctrldata['attmoney'] = int(mon2[0]) * 1000
                info = ' simul' if ctrldata['sub1017'] == 's' else ' real '
                if self.driving == '': self.driving = ctrldata['sub1017']
                actxt = ", autoControl : True" if ctrldata['autoctl'] == 't' else ""

                table = next(iter({i for a1 in self.table_no for i, y in a1.items() if y in str(ctrldata['ta'])}))
                di = [ctrldata['lnum'], info, result['date'][-8:], table, ctrldata['sub1001'], step, bp, mon2[0], "", "", "", self.attno]
                self.parent.disponly = di
                self.dispdata.append(di)
                # self.datadisplay(di, 0)

                dataz = f"#####{di[11]}attack #####, ta : {ctrldata['ta']}, Name : {di[4]}, " \
                        f"bp : {di[6]}, aTTmoney : {mon2[0]}, step : {step}{actxt}"
                print(dataz)
                self.logger2.info(dataz)
                self.logger3.info(dataz)

                self._attack(ctrldata, bp)
        else:
            print('$$$$$$$$$$$$$$$$$Game end$$$$$$$$$$$$$$$$$$$$$$$')
            if datetime.datetime.now() > datetime.datetime.strptime(ctrldata['sub1018'], "%Y-%m-%d %H:%M"):
                self.logger3.info(f'now : {datetime.datetime.now()}')
                self.logger3.info(datetime.datetime.strptime(ctrldata['sub1018'], "%Y-%m-%d %H:%M"))
                print('Game DeadLineTime Over')
            elif float(ctrldata['resultmoney']) >= float(ctrldata['sub1014']):
                self.logger3.info(f"resultmoney : {float(ctrldata['resultmoney'])}")
                self.logger3.info(f"setmoney : {float(ctrldata['sub1014'])}")
                print('Game AmountSetting Over')
            elif self.change >= int(ctrldata['sub1019']):
                self.logger3.info(f"limitmoney : {float(ctrldata['sub1019'])}")
                self.logger3.info(f"totalmoney : {self.change}")
                print('Game TotalAmount Over')

    def _attack(self, ctrldata, bp):
        data = {'ta': int(ctrldata['ta']), 'bp': ctrldata['attBP'], 'mon': int(ctrldata['attmoney']),
                'game': ctrldata['sub1017'], 'ctmoney': int(ctrldata['ctmoney'])}

        if not self.dbtablesum:
            self.dbtablesum.append(data)
            # self.delaycnt += 1
        else:
            d = [[i, data['mon']] for i, aa in enumerate(self.dbtablesum) if aa['ta'] == data['ta'] and aa['bp'] == bp]
            if d:
                self.dbtablesum[d[0][0]]['mon'] += d[0][1]
                # self.delaycnt -= 1
                print(
                    f"####!  sum  data  !####, ta : {ctrldata['ta']}, bp : {ctrldata['attBP']}, mon : {self.dbtablesum[d[0][0]]['mon']}")
                self.logger2.info(
                    f"####!  sum  data  !####, ta : {ctrldata['ta']}, bp : {ctrldata['attBP']}, mon : {self.dbtablesum[d[0][0]]['mon']}")
            else:
                self.dbtablesum.insert(0, data)
                # self.delaycnt += 1

    def _autoctrl(self, result, ctrldata):
        step = int(result['step'])
        # attack 이전일때
        attmin = 0 if ctrldata['sub1007'] == '' else int(ctrldata['sub1007'])
        attmax = 1000 if ctrldata['sub1008'] == '' else int(ctrldata['sub1008'])
        attchk = 0 if ctrldata['sub1009'] == '' else int(ctrldata['sub1009'])
        ssnum = 0 if ctrldata['sub1010'] == '' else int(ctrldata['sub1010'])
        atnum = 0 if ctrldata['sub1011'] == '' else int(ctrldata['sub1011'])
        renum = 0 if ctrldata['sub1012'] == '' else int(ctrldata['sub1012'])

        if ctrldata['autoctl'] == 't':  # 오토컨트롤 일때 값 늘이기
            autonum = atnum
            attmin = attmin + autonum
            attmax = attmax + autonum

        if 0 < attchk <= step and ctrldata['autoctl'] == 'f':  # 오토컨트롤 체크
            ctrldata['sncnt'] = ctrldata['sncnt'] + 1
            if 0 < ssnum == ctrldata['sncnt']:  # 오토컨트롤 시작
                ctrldata['autoctl'] = 't'
                ctrldata['sncnt'] = 0
                self.logger3.info(f'오토 컨트롤 시작, ta : {result["ta"]}')
        elif attmax <= step and ctrldata['autoctl'] == 't':  # 리턴갯수 체크
            ctrldata['rccnt'] = ctrldata['rccnt'] + 1
            if 0 < renum == ctrldata['rccnt']:  # 오토컨트롤 종료
                ctrldata['autoctl'] = 'f'
                ctrldata['rccnt'] = 0
                self.logger3.info(f'오토 컨트롤 종료, ta : {result["ta"]}')
        return [step, attmin, attmax]

    def sqldata(self, ctrl, re, re1, re_t):
        if re_t:
            for ctrlData, resultT in itertools.product(ctrl, re_t):
                if ctrlData['attack'] == 't' and int(ctrlData['ta']) == resultT['ta']:
                    for bp in ctrlData['bp']:
                        if ctrlData['readTime1'] != resultT['CD'] and ctrlData['TieTime'] != resultT['CD'] and bp == ctrlData['attBP'] or \
                           ctrlData['readTime2'] != resultT['CD'] and ctrlData['TieTime'] != resultT['CD'] and bp == ctrlData['attBP']:
                            print(f"!!!! Tie !!!! !!rebet!!, ta : {ctrlData['ta']}, Name : {ctrlData['sub1001']}, "
                                  f"bp : {ctrlData['attBP']}, aTTmoney : {ctrlData['attmoney']}")
                            ctrlData['TieTime'] = resultT['CD']
                            self._attack(ctrlData, bp)
        if re:
            for ctrlData, result in itertools.product(ctrl, re):
                if ctrlData['attack'] == 't' and ctrlData['ta'] == result['ta']:
                    for bp in ctrlData['bp']:
                        # 공격 후 결과 값
                        if bp == 'P' and ctrlData['readTime1'] != result['date'] and ctrlData['attBP'] == bp \
                                or bp == 'B' and ctrlData['readTime2'] != result['date'] and ctrlData['attBP'] == bp:

                            mon = ctrlData['amosetorg'].split('|')
                            win, info = 't' if ctrlData['attBP'] == result['bp'] else 'f', \
                                        'win ' if ctrlData['attBP'] == result['bp'] else 'lose'
                            self.logger2.info(f'!!!! result !!!! : {info}, ta : {ctrlData["ta"]}, Name : {ctrlData["sub1001"]}, bp : {bp}, aTTmoney : {ctrlData["attmoney"]}')
                            print(f'!!!! result !!!! : {info}, ta : {ctrlData["ta"]}, Name : {ctrlData["sub1001"]}, bp : {bp}, aTTmoney : {ctrlData["attmoney"]}')
                            ctrlData['attack'] = 'f'
                            ctrlData['attTime'], ctrlData['attBP'], ctrlData['TieTime'], \
                                ctrlData['readTime1'], ctrlData['readTime2'] = '', '', '', '', ''

                            mon2 = mon[ctrlData['amoset']].split(',')
                            if mon2[1] == '': mon2[1] = 0

                            if win == 't':
                                attremoney = int(ctrlData['attmoney']) if result['bp'] == 'P' else int(ctrlData['attmoney']) * 0.95
                                ctrlData['resultmoney'] = ctrlData['resultmoney'] + attremoney

                                if ctrlData['ctmoney'] != 0:
                                    ctrlData['cresultmoney'] = ctrlData['cresultmoney'] + attremoney
                                    if ctrlData['cttopP'] < ctrlData['cresultmoney']: ctrlData['cttopP'] = ctrlData['cresultmoney']

                                if 0 < int(mon2[1]) and ctrlData['cruse'] == 'f':
                                    ctrlData['attmoney'] = int(mon2[0]) * int(mon2[1]) * 1000
                                    ctrlData['cruse'] = 't'
                                elif ctrlData['cruse'] == 't' or 0 >= int(mon2[1]):
                                    ctrlData['amoset'] = int(mon2[2]) - 1
                                    mon3 = mon[ctrlData['amoset']].split(',')
                                    ctrlData['attmoney'] = int(mon3[0]) * 1000
                                    ctrlData['cruse'] = 'f'
                                ctrlData['wincnt'] = ctrlData['wincnt'] + 1
                                ctrlData['lastwl'] = 'win'
                            else:
                                attremoney = int(ctrlData['attmoney'])
                                ctrlData['resultmoney'] = ctrlData['resultmoney'] - attremoney
                                if ctrlData['ctmoney'] != 0:
                                    ctrlData['cresultmoney'] = ctrlData['cresultmoney'] - attremoney
                                    if ctrlData['cttopN'] > ctrlData['cresultmoney']: ctrlData['cttopN'] = ctrlData['cresultmoney']
                                ctrlData['amoset'] = int(mon2[3]) - 1
                                mon3 = mon[ctrlData['amoset']].split(',')
                                ctrlData['attmoney'] = int(mon3[0]) * 1000
                                ctrlData['cruse'] = 'f'
                                ctrlData['losecnt'] = ctrlData['losecnt'] + 1
                                ctrlData['lastwl'] = 'lose'

                            if ctrlData['ctmoney'] > 0 >= ctrlData['ctmoney'] - ctrlData['cttopP'] + ctrlData['cttopN'] or \
                                    ctrlData['ctmoney'] < 0 <= ctrlData['ctmoney'] + ctrlData['cttopP'] - ctrlData['cttopN']:
                                ctrlData['ctmoney'], ctrlData['amoset'] = 0, 0

                            self.money0 = int(self.money0) + int(attremoney) if win == 't' else int(self.money0) - int(attremoney)
                            # self.wlData.append([result['date'].strftime("%Y-%m-%d %H:%M:%S"), ctrlData['ta'], win, self.money0, attremoney, ctrlData['sub1017']])
                            ctrlData['totcnt'] = ctrlData['totcnt'] + 1
                            if ctrlData['sub1017'] == 's':
                                pinfo = f'--{datetime.datetime.now().strftime("%H:%M:%S")}, 시뮬 전체 잔액 : {self.money0}, 테이블 잔액 : {ctrlData["resultmoney"]}, ta : {ctrlData["ta"]}'
                                total = self.money0 / 1000 if self.money0 != 0 else 0
                            else:
                                pinfo = f'--{datetime.datetime.now().strftime("%H:%M:%S")}, 리얼 전체 잔액 : {self.change},  테이블 잔액 : {ctrlData["resultmoney"]}, ta : {ctrlData["ta"]}'
                                total = self.change / 1000 if self.change != 0 else 0
                            print(pinfo)
                            self.logger2.info(pinfo)
                            i = [k for k, v in enumerate(self.dispdata) if v[11] == ctrlData['attno']][0]
                            self.dispdata[i][8] = info
                            self.dispdata[i][9] = str(ctrlData['attmoney'] / 1000)
                            self.dispdata[i][10] = str(total)
                            self.parent.disponly = self.dispdata[i]

                            # self.datadisplay(self.disponly, 1)
                            # self.delaycnt += 0.25

                # re는 ng와 og만 attack check.
                if ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "NG" \
                        or ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "OG":

                    reData = self._autoctrl(result, ctrlData)
                    step = reData[0] + 1
                    attmin, attmax = reData[1], reData[2]

                    # attack check
                    for bp in ctrlData['bp']:
                        if attmin <= 1 and ctrlData['attack'] == 'f' and result['bp'] != result['beBP']:  # 1단계 어택하기
                            if bp == 'P' and ctrlData['readTime1'] != result['date'] or \
                                    bp == 'B' and ctrlData['readTime2'] != result['date']:
                                ctrlData['ng1'] = 't'
                                self.logger3.info(f'resultDataNG1 = {result}')
                                self.logger3.info(f'ctrlDataNG1 = {ctrlData}')
                                self.attinfo2(ctrlData, result, bp, 1)
                        elif attmin <= step <= attmax and ctrlData['attack'] == 'f':  # 나머지 단계어택하기
                            if bp == 'P' and ctrlData['readTime1'] != result['date'] or \
                                    bp == 'B' and ctrlData['readTime2'] != result['date']:
                                self.logger3.info(f'resultDataNG2 = {result}')
                                self.logger3.info(f'ctrlDataNG2 = {ctrlData}')
                                self.attinfo2(ctrlData, result, bp, step)

        if re1:
            for ctrlData, result in itertools.product(ctrl, re1):  # re1의 attack f 모아서 확인
                if ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "BG" \
                        or ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "BB" \
                        or ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "YJ" \
                        or ctrlData['attack'] == 'f' and ctrlData['ta'] == result['ta'] and ctrlData['sub1001'] == "YK":
                    reData = self._autoctrl(result, ctrlData)
                    step = reData[0]
                    attmin, attmax = reData[1], reData[2]

                    # attack check
                    for bp in ctrlData['bp']:
                        if attmin <= step <= attmax and ctrlData['attack'] == 'f':  # 어택하기
                            if bp == 'P' and ctrlData['readTime1'] != result['date'] or \
                                    bp == 'B' and ctrlData['readTime2'] != result['date']:
                                self.logger3.info(f'resultDataOt = {result}')
                                self.logger3.info(f'ctrlDataOt = {ctrlData}')
                                self.attinfo2(ctrlData, result, bp, step)

    def attackdata(self):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(self.attDatasql)
            re = cursor.fetchall()
            re1, re2 = '', ''
            if self.ctrlBG or self.ctrlBB:
                cursor.execute(self.sqldatasql.format('BG'))
                re1 = cursor.fetchall()
            if self.ctrlYJ or self.ctrlYK:
                cursor.execute(self.sqldatasql.format('YJ'))
                re2 = cursor.fetchall()
            cursor.execute(self.sqlT)
            sqlT = cursor.fetchall()
        self.conn.commit()
        if re or sqlT:
            if self.ctrlNG:                self.sqldata(self.ctrlNG, re, "", sqlT)
            if self.ctrlOG:                self.sqldata(self.ctrlOG, re, "", sqlT)
            if re1 or sqlT:
                if self.ctrlBG:            self.sqldata(self.ctrlBG, re, re1, sqlT)
                if self.ctrlBB:            self.sqldata(self.ctrlBB, re, re1, sqlT)
            if re2 or sqlT:
                if self.ctrlYJ:            self.sqldata(self.ctrlYJ, re, re2, sqlT)
                if self.ctrlYK:            self.sqldata(self.ctrlYK, re, re2, sqlT)
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(self.attSaveData %
                               (self.ctrlNG, self.ctrlOG, self.ctrlBG, self.ctrlBB, self.ctrlYJ, self.ctrlYK,
                                self._id2, self.driving))
            self.conn.commit()

    def insert_table(self):
        # 테이블 번호
        # table_no = 831
        # 배팅 데이터
        # bet_list = [["P", 1000]]
        try:
            self.last_update = time.time()
            self.clicktime += 1
            start = timeit.default_timer()
            self.from_dbdata()
            if self.from_db and self.ctrlCnt < self.table_noCnt:    self.checkover_step()
            if self.attack:     self.attackdata()

            # 배팅 가능한 상태인지 체크
            attnum = len(self.dbtablesum)
            if self.dbtablesum:
                start1 = timeit.default_timer()
                for a in range(attnum):
                    # 테이블 번호, 포지션, 금액
                    data = self.dbtablesum.pop()
                    bet_result = self.gs.betting(int(data['ta']), str(data['bp']), int(data['mon']),
                                                 str(data['game']), int(data['ctmoney']), attnum)
                    self.logger2.info(f"배팅 성공 여부: {bet_result}")

                    if not bet_result:
                        self.dt.insert(0, data)
                        self.logger2.info(f"배팅 재시도: {data}")
                if self.dt:
                    l1 = len(self.dt)
                    for k in range(l1):
                        self.dbtablesum.insert(0, self.dt.pop())
                self.gs.delaycnt = 0
                self.gs.onestart = True
                self.gs.logger8.info(f"-- checkTotal : %.1f초" % (timeit.default_timer() - start1))
                self.gs.logger7.info(f"=======================================================================================")
                self.gs.logger8.info(f"=======================================================================================")

            # self.logger4.info(f"betting : [%.2f초, attnum : {attnum}, delaycnt : {self.delaycnt}" % (timeit.default_timer() - start3))

            if timeit.default_timer() - start < 3:
                self.from_dbdata()
                time.sleep(random.uniform(1.0, 1.5))
                self.from_dbdata()
                time.sleep(random.uniform(1.0, 1.5))
            elif timeit.default_timer() - start < 4.5:
                self.from_dbdata()
                time.sleep(random.uniform(1.0, 1.5))

            if self.clicktime % 30 == 0:
                print(self.gs.click1())
                print(f'--{datetime.datetime.now().strftime("%H:%M:%S")}, 잔액 : {self.change}')
                self.clicktime = 0

                # self.gs.driver.get("chrome://settings/clearBrowserData")
                # time.sleep(2)
                # actions = ActionChains(self.driver)
                # actions.send_keys(Keys.TAB * 7 + Keys.ENTER)  # confirm
                # actions.perform()

            self.logger4.info("-- bbtime4 : [%.1f초" % (timeit.default_timer() - start))
            print("-- bbtime4 : [%.1f초" % (timeit.default_timer() - start))

        except Exception as ex:
            print(ex)

    async def cleardata(self):
        pass
        # await self.gs.driver.

    def _check_config(self):
        if set(self._DEFAULT_CONF_DB) != set((dict(self._config.items(self._CONF_DB_KEY)).keys())):
            raise Exception("필요한 설정 항목이 없습니다.")
        if '' in dict(self._config.items(self._CONF_DB_KEY)).values():
            raise Exception("비어있는 설정이 있습니다.")

        if set(self._DEFAULT_CONF_SITE) != set((dict(self._config.items(self._CONF_SITE_KEY)).keys())):
            raise Exception("필요한 설정 항목이 없습니다.")
        if '' in dict(self._config.items(self._CONF_SITE_KEY)).values():
            raise Exception("비어있는 설정이 있습니다.")

        if set(self._DEFAULT_CONF_SERVICE) != set((dict(self._config.items(self._CONF_SERVICE_KEY)).keys())):
            raise Exception("필요한 설정 항목이 없습니다.")
        if '' in dict(self._config.items(self._CONF_SERVICE_KEY)).values():
            raise Exception("비어있는 설정이 있습니다.")

    def _health_checker(self):
        if (time.time() - self.last_update) > 10*4:
            self.logger9.info("텔레그램 전송")
            raise TimeoutError("응답 없음")

        self.timer = threading.Timer(5, self._health_checker)
        self.timer.daemon = True
        self.timer.start()

    def release_all(self):
        try:
            self.conn.close()
        finally:
            print("DB 드라이버 종료")


class Thread1(QThread):
    def __init__(self, _gs, _url, _id, _id2, _pw):
        super().__init__()
        self.gs = _gs
        self.url_text = _url
        self.id_text = _id
        self.id2_text = _id2
        self.pw_text = _pw

    def run(self):
        self.gs.setup(self.url_text, self.id_text, self.id2_text, self.pw_text)


def check_admin():
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    return is_admin


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    import sys

    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    login = Info()
    window = Runner()
    while 1:
        try:
            widget = QtWidgets.QStackedWidget()

            widget.addWidget(login)
            widget.addWidget(window)
            widget.setFixedWidth(490)
            widget.setFixedHeight(275)
            widget.show()

            # login.show()
            # window.show()
            sys.exit(app.exec_())
        except KeyboardInterrupt or SystemError or TimeoutError or SystemExit:
            window.thread1.release_all()
            sys.exit(0)

        finally:
            app = QApplication(sys.argv)
            login = Info()
            window = Runner()
