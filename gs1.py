import configparser
import datetime
import logging
import os
import random
import shutil
import subprocess
import threading
import time
import timeit
from logging import handlers

import chromedriver_autoinstaller as ca
import requests
import urllib3
from PyQt5.QtCore import QThread, QWaitCondition, QMutex, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
from requests.adapters import HTTPAdapter
from selenium.common import exceptions
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class WaitReadyState:
    def __call__(self, driver):
        state = driver.execute_script("return document.readyState")
        return True if state == "complete" else False


class WaitSaGameLoad:
    def __call__(self, driver):
        try:
            state = driver.execute_script("return window.user.appUsername")
            return True if state != "" else False
        except exceptions.JavascriptException:
            return False


class WaitMultiBetTable:
    def __init__(self, min_size):
        self.min = min_size

    def __call__(self, driver):
        try:
            state = driver.execute_script(
                f"return GameLayerManager.Instance.sceneLayer."
                f"$children[0].tableList.$children[{self.min}]._host.records"
            )
            return True if isinstance(state, list) else False
        except exceptions.JavascriptException:
            return False


class WaitBetHost:
    def __call__(self, driver):
        try:
            state = driver.execute_script("return window.user._hosts.length")
            return True if int(state) > 0 else False
        except exceptions.JavascriptException:
            return False
        except ValueError:
            return False


class GS(QMainWindow):
    _CONF_DB_KEY = "DB"
    _CONF_SITE_KEY = "SITE"
    _CONF_SERVICE_KEY = "SERVICE"
    _DEFAULT_CONF_DB = ["db_host", "db_port", "db_user", "db_pwd", "db_name"]
    _DEFAULT_CONF_SITE = ["site_url", "site_id_selector", "site_pwd_selector", "sagame_id", "site_id", "site_pwd","site_game_selector"]
    _DEFAULT_CONF_SERVICE = ['default_timeout', "default_delay", "scan_speed", "table_min_size"]

    def __init__(self, parent, setting_path):
        super().__init__(parent)
        self.parent = parent
        self._url, self._id, self._id2, self._pw = '', '', '', ''
        self._config = configparser.ConfigParser()
        self._config.read(setting_path, encoding="utf8")
        self._check_config()
        self.clicktime = time.time()

        self._site_conf = self._config[GS._CONF_SITE_KEY]
        self._service_conf = self._config[GS._CONF_SERVICE_KEY]

        self._default_delay = int(self._service_conf["default_delay"])
        self._default_timeout = int(self._service_conf["default_timeout"])

        if os.path.isdir("./emp"):
            os.chdir("./emp")
            for i in os.listdir():
                try:
                    shutil.rmtree(i)  # ?????? / ???????????? ??????
                except Exception as ex:
                    # print(ex)
                    pass

            os.chdir("../")

        option = Options()
        option.add_argument("disable-gpu")  # ?????? ?????? x
        option.add_argument("lang=ko_KR")  # ?????? ???????????? ??????

        option.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.3163.100 Safari/537.36')  # user-agent ?????? ??????
        option.add_argument(f"--user-data-dir={os.getcwd()}\emp")

        # chrome_ver = ca.get_chrome_version().split('.')[0]
        path = ca.install()
        self.driver = webdriver.WebDriver(path, chrome_options=option)

        urllib3.PoolManager(maxsize=100)
        # adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        # session = requests.Session()
        # session.mount('http://', adapter)
        # session.mount('https://', adapter)
        self.driver.set_window_size(1300, 950)
        self.driver.implicitly_wait(self._default_timeout)

        self.last_update = 0.0
        self.cntnum, self.delaycnt, self.beforelimit, self.logtime, self.changez = 0, 0, 0, 0, 0
        self.nobetcnt, self.overcnt = [], []
        self.lock, self.onestart, self.beforelimitfirst = False, True, True

        formatter = logging.Formatter('%(asctime)s %(message)s')
        # self.logger6 = ??????, ?????? ?????? ?????????
        fh2 = handlers.TimedRotatingFileHandler(filename='infodata/6infoAttack.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh2.setFormatter(formatter)
        fh2.suffix = '%m-%d.txt'
        fh2.setLevel(logging.INFO)
        self.logger6 = logging.getLogger("my6")
        self.logger6.setLevel(logging.INFO)
        self.logger6.addHandler(fh2)
        self.logger6.propagate = False
        self.logger6.info("===================start====================")

        # self.logger6 = ??????, ?????? ?????? ?????????2
        fh5 = handlers.TimedRotatingFileHandler(filename='infodata/7infoAttack2.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh5.setFormatter(formatter)
        fh5.setLevel(logging.INFO)
        self.logger7 = logging.getLogger("my8")
        self.logger7.setLevel(logging.INFO)
        self.logger7.addHandler(fh5)
        self.logger7.propagate = False
        self.logger7.info("==================================start====================================")

        # # self.logger8 = ????????????
        fh4 = handlers.TimedRotatingFileHandler(filename='infodata/8timeCheck.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh4.setFormatter(formatter)
        fh4.setLevel(logging.INFO)
        self.logger8 = logging.getLogger("my7")
        self.logger8.setLevel(logging.INFO)
        self.logger8.addHandler(fh4)
        self.logger8.propagate = False
        self.logger8.info("==================================start====================================")

        # # self.logger9 = ????????????
        fh6 = handlers.TimedRotatingFileHandler(filename='infodata/9otherheck.txt', when='midnight', interval=1,
                                                encoding='utf-8')
        fh6.setFormatter(formatter)
        fh6.setLevel(logging.INFO)
        self.logger9 = logging.getLogger("my9")
        self.logger9.setLevel(logging.INFO)
        self.logger9.addHandler(fh6)
        self.logger9.propagate = False
        self.logger9.info("==================================start====================================")


        # self.requestManager = _RequestManager()
        # self.requestManager.start()
        # self.requestManager.threadEvent.connect(self.request_task)

    def _tr_request_task(self, task):
        pass

    def _login(self):
        print(self._url)
        if 'COIN' in self._url:
            self.driver.get("https://www.38qqs.com/")
            self._login_55qwe()
        elif '007' in self._url:
            self.driver.get("http://vvip8888.com")
            self._login_vvip()
        elif 'THEON' in self._url:
            self.driver.get("http://www.vkvk11.com")
            self._login_vkvk()

    def _idchk(self):
        WebDriverWait(self.driver, self._default_timeout).until(WaitReadyState())
        WebDriverWait(self.driver, self._default_timeout).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, self._site_conf["site_id_selector"]))
        )

        # id_input = self.driver.find_element_by_css_selector(self._site_conf["site_id_selector"])
        self.driver.find_element(By.CSS_SELECTOR, self._site_conf["site_id_selector"]).send_keys(self._id)
        time.sleep(random.uniform(0.5, 1.0))
        # pwd_input = self.driver.find_element_by_css_selector(self._site_conf["site_pwd_selector"])
        pwd_input = self.driver.find_element(By.CSS_SELECTOR, self._site_conf["site_pwd_selector"])
        pwd_input.send_keys(self._pw)
        time.sleep(random.uniform(0.5, 1.0))
        pwd_input.send_keys(Keys.ENTER)

        WebDriverWait(self.driver, self._default_timeout).until(WaitReadyState())

    def _page_pass(self):

        # ##################### ????????? - ?????? ?????? ???????????? ??? ?????? ????????? ???
        # try:
        #     t1 = self.driver.find_elements_by_tag_name('input')
        #     for i in t1:
        #         i.click()
        # except:
        #     print(i)
        #     pass
        # time.sleep(random.uniform(0.5, 1.0))

        # self.driver.find_element_by_css_selector('#sagame').click()     # ???????????? ?????????

        # ???????????? ?????????
        if 'COIN' in self._url:
            # self.driver.find_elements_by_css_selector('.snip1554')[2].click()
            self.driver.find_elements(By.CSS_SELECTOR, '.snip1554')[2].click()
        elif '007' in self._url:
            self.driver.find_elements(By.CSS_SELECTOR, '.btn.gamestart')[5].find_element(By.CSS_SELECTOR, "i").click()
        elif 'THEON' in self._url:
            self.driver.find_elements(By.CSS_SELECTOR, '.card_org')[1].click()

        window_handle = self.driver.window_handles.copy()
        time.sleep(random.uniform(1.0, 2.0))
        WebDriverWait(self.driver, self._default_timeout).until(ec.new_window_is_opened(window_handle))

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def _login_55qwe(self):
        # SITE_ID = 881zhwoddl
        # SITE_PWD = rk660024
        self._idchk()

        if self.driver.find_elements(By.CSS_SELECTOR, "#main_pop_notice_new11"):
            try:
                self.driver.find_element(By.XPATH, u'//input[@name="nomore"]').click()
            except:
                pass
        time.sleep(random.uniform(0.5, 1.0))

        self._page_pass()

    def _login_vvip(self):
        # SITE_ID = aaaa5588
        # SITE_PWD = Qydrkdy7823

        self._idchk()

        # ##################### ????????? - X ?????? ????????? ???????????? ???.
        try:
            t = self.driver.find_elements(By.CSS_SELECTOR, "#warning2021-close")
            for i in t:
                i.click()
        except:
            print(i)
            pass
        time.sleep(random.uniform(0.5, 1.0))

        self._page_pass()

    def _login_vkvk(self):
        # SITE_ID = skflskfl
        # SITE_PWD = Qjrrkdy2589

        WebDriverWait(self.driver, self._default_timeout).until(WaitReadyState())

        # ##################### ????????? - ?????? ?????? ???????????? ??? ?????? ????????? ???
        # try:
        #     t1 = self.driver.find_elements_by_tag_name('input')
        #     for i in t1:
        #         i.click()
        # except:
        #     print(i)
        #     pass
        # time.sleep(random.uniform(0.5, 1.0))
        time.sleep(random.uniform(0.5, 1.0))
        self.driver.execute_script("document.getElementsByName('fp')[0].setAttribute('type','text')")
        time.sleep(random.uniform(0.5, 1.0))
        self.driver.execute_script("document.getElementsByName('fp')[1].setAttribute('type','text')")
        time.sleep(random.uniform(0.5, 1.0))

        WebDriverWait(self.driver, self._default_timeout).until(
            ec.element_to_be_clickable((By.LINK_TEXT, 'LOGIN'))
        )

        self.driver.find_elements(By.CSS_SELECTOR, self._site_conf["site_id_selector"])[1].send_keys(self._id)
        time.sleep(random.uniform(0.5, 1.0))
        self.driver.find_elements(By.CSS_SELECTOR, self._site_conf["site_pwd_selector"])[1].send_keys(self._pw)
        time.sleep(random.uniform(0.5, 1.0))

        try:
            self.driver.find_element(By.CSS_SELECTOR, "input.close1").click()
            # self.driver.find_element_by_css_selector("input.close2").click()
        except:
            pass

        self.driver.find_element(By.LINK_TEXT, 'LOGIN').click()

        WebDriverWait(self.driver, self._default_timeout).until(WaitReadyState())

        self._page_pass()

    def _wait_sa_load(self):
        WebDriverWait(self.driver, self._default_timeout).until(WaitSaGameLoad())
        time.sleep(self._default_delay)

    def _switch_multi_bet(self):
        WebDriverWait(self.driver, self._default_timeout).until(WaitBetHost())
        self.driver.execute_script("GameLayerManager.Instance.showMultiBet()")
        time.sleep(self._default_delay)
        self.driver.execute_script(
            "GameLayerManager.Instance.sceneLayer.$children[0]."
            "ChangePanel({currentTarget: GameLayerManager.Instance.sceneLayer.$children[0].tabList.getChildAt(1)})"
        )

    def _wait_multi_bet(self):
        WebDriverWait(self.driver, self._default_timeout).until(WaitMultiBetTable(self._service_conf["table_min_size"]))
        self.parent.notStart = False
        time.sleep(5)

    def bet(self, table: int, money: int, position: int):
        pass

    def set_chip_group(self, coin_index_list: tuple):
        if len(coin_index_list) != 5:
            raise Exception("??? 5?????? ?????? ??????????????????.")
        self.driver.execute_async_script(
            """var done = arguments[0];
            (async () => {
            var i = new ChipSettingPanel(GameLayerManager.Instance.sceneLayer.$children[0]);
            var n = ChipSettingPanel.getNumOfRow(user.customeChips(GameType.BACCARAT).length, 5);
            var s = 144 + 60 * (n - 1) + 76;
            i.setPanelHeight(s);
            i.scene = "multibacc";
            GameLayerManager.Instance.upperLayer.addChild(i);
            await new Promise(resolve => setTimeout(resolve, 500));
            for (let chip of GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children) {
                if (chip.selected) {
                    GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: chip})
                }
            }

            GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children[%s]});
            GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children[%s]});
            GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children[%s]});
            GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children[%s]});
            GameLayerManager.Instance.upperLayer.$children[0].selectChip({currentTarget: GameLayerManager.Instance.upperLayer.$children[0].$children[3].$children[0].$children[2].$children[0].$children[%s]});

            await new Promise(resolve => setTimeout(resolve, 500));
            GameLayerManager.Instance.upperLayer.$children[0].doSetChip()
            await new Promise(resolve => setTimeout(resolve, 500));
            done()
            })();""" % coin_index_list)

    def set_chip(self, index: int):
        self.driver.execute_script("""(() => {
        GameLayerManager.Instance.sceneLayer.$children[0].selectedChip = GameLayerManager.Instance.sceneLayer.$children[0].chipList.$children[%s]
        GameLayerManager.Instance.sceneLayer.$children[0].chipList.$children.forEach(x => x.isSelected(false))
        SceneGame.curChipIdx = 0
        GameLayerManager.Instance.sceneLayer.$children[0].selectedChip.isSelected(true)
        GlobalData.currentChips = GameLayerManager.Instance.sceneLayer.$children[0].currentChipArray[Number(GameLayerManager.Instance.sceneLayer.$children[0].selectedChip.data)]
        })();""" % index)

    # before code
    def change_limit(self, index: int):
        self.driver.execute_script("""(() => {
        GameLayerManager.Instance.sceneLayer.$children[0].selectedChip = GameLayerManager.Instance.sceneLayer.$children[0].chipList.$children[%s]
        GameLayerManager.Instance.sceneLayer.$children[0].chipList.$children.forEach(x => x.isSelected(false))
        SceneGame.curChipIdx = 0
        GameLayerManager.Instance.sceneLayer.$children[0].selectedChip.isSelected(true)
        GlobalData.currentChips = GameLayerManager.Instance.sceneLayer.$children[0].currentChipArray[Number(GameLayerManager.Instance.sceneLayer.$children[0].selectedChip.data)]
        })();""" % index)

    # currect code
    def change_bet_limit(self, limit_index: int):
        self.driver.execute_script(
            """GameLayerManager.Instance.sceneLayer.$children[0].multiBetLimit.changeBetLimit.ChangeLimit({currentTarget:GameLayerManager.Instance.sceneLayer.$children[0].multiBetLimit.changeBetLimit.btnChangeArray[%s], target: GameLayerManager.Instance.sceneLayer.$children[0].multiBetLimit.changeBetLimit.btnChangeArray[%s].textLabel})""" % (
            limit_index, limit_index))

    def set_money(self, table: int, position: int):
        self.driver.execute_script("""GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children[%s].doBet(
        {currentTarget: 
        GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children[%s].$children[10].$children[15].$children[%s]
        })""" % (table, table, position))

    def video_reload_interval(self, interval_time_hour: int):
        self.driver.execute_script(f"setInterval(() => {{ user.prefs.switchLiveStream = !user.prefs.switchLiveStream; setTimeout(() => {{ user.prefs.switchLiveStream = !user.prefs.switchLiveStream; }}, 4000); }}, 1000 * 60 * 60 * {interval_time_hour})")

    def enablebet(self, table_index):
        return self.driver.execute_script(
            f"return GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children[{table_index}].$children[10].$children[15].$children[0].$touchEnabled"
        )

    def betting(self, table: int, position: str, money: int, game: str, ctmoney: int, len1: int):
        self.delaycnt += 1
        start = timeit.default_timer()
        num = [0.06, 0.15] if self.logtime < 0.3 else [0.04, 0.08]
        if len1 < 4 and self.onestart:
            self.parent.change = self.change(num)
            self.logger8.info(f"-- check0 : [%.1f??? self.betting : {table}" % (timeit.default_timer() - start))
            start = timeit.default_timer()
            self.onestart = False

        # num = [0.05, 0.1] if self.delaycnt >= 2 else [0.04, 0.07] if self.delaycnt >= 4 else [0.05, 0.15]
        """
        ?????? ??????
        :param table: ????????? ?????? ex) 831, 832
        :param position: P: ????????????, T: ??????, B: ??????, PP: ??????????????????, BP: ????????????, L: ????????????
        :param money: ??????
        :param game: ??????, ??????
        :return: ????????? True ????????? False or Exception
        """
        table_index = self.driver.execute_script(
        f"return GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children.findIndex(x => x._host._hostID == {table})")
        if table_index < 0:
            self.logger9.info("???????????? ??????")
            raise Exception("???????????? ?????? ??? ????????????.")

        time.sleep(random.uniform(num[0], num[1]))
        self.logger8.info(f"-- check1 : [%.1f??? table : {table}" % (timeit.default_timer() - start))
        self.logtime = timeit.default_timer() - start
        start = timeit.default_timer()
        self.logger6.info(f"?????? ????????? ??????: {table_index + 1}")

        if table_index < 12:
            self.driver.execute_script("scrollBy(0,-600);")
        else:
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

        time.sleep(random.uniform(num[0], num[1]))
        self.logger8.info("-- check2 : [%.1f???" % (timeit.default_timer() - start))
        start = timeit.default_timer()

        re = True
        ovnum = 7
        errtxt = "?????? ?????? ?????? ??????????????????."
        cnt = 0
        if self.nobetcnt:  # ?????? ????????? ????????? ??????
            w, c = [i for i, v in enumerate(self.nobetcnt) if table == v['ta']], \
                   [v['cnt'] for i, v in enumerate(self.nobetcnt) if table == v['ta']]
            where, cnt = w[0] if w else 0, c[0] if c else 0

            self.logger7.info(f'[{table}, {cnt}, {where} : table, cnt, where')
            if ovnum < cnt:  # 7??? ?????? ???????????? 12??? ????????? ????????? ?????? ??????
                if self.overcnt:
                    w1 = [k for k, w in enumerate(self.overcnt) if table == w['ta']]
                    where1 = w1[0] if w1 else -1
                    if where1 == -1:
                        self.logger6.info(f"{errtxt} 12 ??? ?????? ??????-1")
                        self.logger7.info(f"[{table} {errtxt} 12 ??? ?????? ??????-1 ")
                        self.overcnt.append({'ta': table, 'time': datetime.datetime.now()})
                        re = False
                    else:
                        # 12??? ??????
                        if self.overcnt[where1]['time'] + datetime.timedelta(seconds=12) < datetime.datetime.now():
                            if self.enablebet(table_index):  # ????????? ???????????? ??????
                                time.sleep(random.uniform(num[0], num[1]))
                                if not self.check_available_bet(table_index):  # ????????? ??????????????? ?????? ?????? ??????
                                    self.logger6.info(f"{errtxt} 12 ??? ?????? ??????2")
                                    self.logger7.info(f"[{table} {errtxt} 12 ??? ?????? ??????2")
                                    self.overcnt[where1]['time'] = datetime.datetime.now()
                                    re = False
                                else:   # ????????? ?????? ????????? ???????????? ??????
                                    self.logger6.info(f"?????? ?????? ???????????? ??????")
                                    self.logger7.info(f"[{table} ?????? ?????? ???????????? ??????")
                                    del self.overcnt[where1]
                                    del self.nobetcnt[where]
                            else:
                                self.logger6.info(f"{errtxt} 12 ??? ?????? ??????2")
                                self.logger7.info(f"[{table} {errtxt} 12 ??? ?????? ??????2")
                                self.overcnt[where1]['time'] = datetime.datetime.now()
                                re = False
                        else:   # 12??? ??????
                            self.logger6.info(f"{errtxt} 12 ??? ??????")
                            self.logger7.info(f"[{table} {errtxt} 12 ??? ??????")
                            re = False
                else:   # ????????? ???????????? ????????? 12??? ??????
                    self.logger6.info(f"{errtxt} 12 ??? ?????? ??????1")
                    self.logger7.info(f"[{table} {errtxt} 12 ??? ?????? ??????1")
                    self.overcnt.append({'ta': table, 'time': datetime.datetime.now()})
                    re = False

            else:  # 10??? ????????????
                if self.enablebet(table_index):  # ????????? ???????????? ??????
                    time.sleep(random.uniform(num[0], num[1]))
                    if not self.check_available_bet(table_index):   # ????????? ?????? ?????????
                        if cnt == 0:
                            self.logger6.info(f"{errtxt} ??????")
                            self.logger7.info(f"[{table} {errtxt} ??????")
                            self.nobetcnt.append({'ta': table, 'cnt': 1})
                        else:
                            self.nobetcnt[where]['cnt'] = cnt + 1
                            self.logger6.info(f"{errtxt} cnt : {cnt}")
                            self.logger7.info(f"[{table} {errtxt} cnt : {cnt}")
                        re = False
                    else:   # ????????? ?????? ????????? ???????????? ??????
                        if cnt != 0:
                            del self.nobetcnt[where]
                            self.logger6.info(f"?????? ?????? ???????????? ??????")
                            self.logger7.info(f"[{table} ?????? ?????? ???????????? ??????")
                else:   # ????????? ???????????? ?????????
                    if cnt == 0:
                        self.logger6.info(f"{errtxt} ??????")
                        self.logger7.info(f"[{table} {errtxt} ??????")
                        self.nobetcnt.append({'ta': table, 'cnt': 1})
                    else:
                        self.nobetcnt[where]['cnt'] = cnt + 1
                        self.logger6.info(f"{errtxt} cnt : {cnt}")
                        self.logger7.info(f"[{table} {errtxt} cnt : {cnt}")
                    re = False
        else:  # ?????? ?????? ??? ?????? ???????????? ??????
            if self.enablebet(table_index):  # ????????? ???????????? ??????
                time.sleep(random.uniform(num[0], num[1]))
                if not self.check_available_bet(table_index):   # ????????? ?????? ?????????
                    self.logger6.info(f"{errtxt} ??????")
                    self.logger7.info(f"[{table} {errtxt} ?????? ?????? ?????? ??????")
                    self.nobetcnt.append({'ta': table, 'cnt': 1})
                    re = False
            else:   # ????????? ???????????? ?????????
                self.logger6.info(f"{errtxt} ??????")
                self.logger7.info(f"[{table} {errtxt} ?????? ?????? ?????? ??????")
                self.nobetcnt.append({'ta': table, 'cnt': 1})
                re = False

        # print(f'?????????????????? : {tablebet}')

        time.sleep(random.uniform(num[0], num[1]))
        self.logger8.info(f"-- check3 : [%.1f???, cntover : {cnt}" % (timeit.default_timer() - start)) if ovnum < cnt \
            else self.logger8.info("-- check3 : [%.1f???" % (timeit.default_timer() - start))
        if not re: return re

        value = money
        n = 4 if money > 5000000 else 3 if money > 2000000 else 2 if money > 350000 else 1 if money > 50000 else 0

        if n != self.beforelimit:
            self.change_bet_limit(n)
            self.beforelimit = n
            self.logger9.info(f"{table} change betting limit num {n}")
            time.sleep(random.uniform(0.5, 1))

        if money > self.changez:    money = self.changez - self.changez % 1000
        if money < 1000:
            print("????????? ????????? ????????????.")
            time.sleep(1)
            return True

        start = timeit.default_timer()
        if self.check_already_bet(table_index):
            self.logger6.info("?????? ????????? ??????????????????.")
            return False

        time.sleep(random.uniform(num[0], num[1]))
        self.logger8.info("-- check4 : [%.1f???" % (timeit.default_timer() - start))
        start = timeit.default_timer()
        position_dict = {"P": 0, "T": 1, "B": 2, "PP": 3, "BP": 4, "L": 5}

        if position_dict.get(position, None) is None:
            raise Exception("??? ??? ?????? ??????????????????.")

        position_index = position_dict[position]

        self.logger6.info(f"?????? ????????? ??????: {position_index + 1}")

        coins = [1000, 5000, 10000, 100000, 1000000]

        result = {x: 0 for x in coins}

        for coin in reversed(coins):
            coin_count = value // coin
            value -= coin * coin_count
            if value == 100:
                value += coin
                coin_count -= 1
            result[coin] = coin_count

        if value != 0:
            raise Exception("?????? ??? ??? ?????? ???????????????.")

        result = {k: v for k, v in result.items() if v != 0}

        coin_groups = [list(result.keys())[i:i + 5] for i in range(0, len(result.keys()), 5)]
        self.logger8.info("-- check5 : [%.1f???" % (timeit.default_timer() - start))
        start = timeit.default_timer()

        for coin_group in coin_groups:
            for coin in coins:
                if coin not in coin_group:
                    if len(coin_group) != 5:
                        coin_group.append(coin)
                    else:
                        break
            coin_group = sorted(coin_group)

            # self.set_chip_group(tuple((coins.index(x) for x in coin_group if x in coins)))
            for index, coin in enumerate(coin_group):
                if result.get(coin, False):
                    self.set_chip(index)
                    for _ in range(result[coin]):
                        self.set_money(table_index, position_index)

        time.sleep(random.uniform(num[0], num[1]))
        self.logger8.info("-- check6 : [%.1f???" % (timeit.default_timer() - start))
        start = timeit.default_timer()
        data = self.driver.execute_script(
            "try { "
            "GameLayerManager.Instance.upperLayer.$children.filter(x => x.hasOwnProperty('btnConfirm'))[0];"
            "return true "
            "} catch(e) { return false }")
        # m = [0.2, 0.4] if self.delaycnt >= 2 else [0.1, 0.3] if self.delaycnt >= 4 else [0.3, 0.5]
        m = [0.3, 0.5] if self.logtime < 0.3 else [0.15, 0.3]
        time.sleep(random.uniform(m[0], m[1]))
        self.logger8.info("-- check7 : [%.1f???" % (timeit.default_timer() - start))
        start = timeit.default_timer()
        if data:
            if game == 'r' and ctmoney == 0:
                self.logger6.info(f'att ctmomney : {ctmoney}')
                re = self.driver.execute_script(
                    "try { "
                    "GameLayerManager.Instance.upperLayer.$children.filter(x => x.hasOwnProperty('btnConfirm'))[0]._parent.doConfirmBet(); "
                    "GameLayerManager.Instance.upperLayer.$children.filter(x => x.hasOwnProperty('btnConfirm'))[0].doClose();"
                    "return true "
                    "} catch(e) { return false }")
                self.logger8.info("-- check8-1 : [%.1f???" % (timeit.default_timer() - start))
                if self.delaycnt == len1:
                    self.logger8.info(f"-- checkTotal : delaycnt : {self.delaycnt}")
                return re
            else:
                self.logger6.info(f'dont att game : {game}')
                self.logger6.info(f'dont att ctmomney : {ctmoney}')
                # self.driver.find_element_by_xpath("//body").send_keys(Keys.ESCAPE)
                re = self.driver.execute_script(
                    "try { "
                    "GameLayerManager.Instance.upperLayer.$children.filter(x => x.hasOwnProperty('btnConfirm'))[0].doClose();"
                    "return true "
                    "} catch(e) { return false }")
                self.logger8.info("-- check8-2 : [%.1f???" % (timeit.default_timer() - start))
                if self.delaycnt == len1:
                    self.logger8.info(f"-- checkTotal : delaycnt : {self.delaycnt}")
                return re
        return data

    def check_available_bet(self, table: int):
        try:
            cTime = int(self.driver.execute_script(
                f"return GameLayerManager.Instance.sceneLayer.$children[0].tableList.$children[{table}].lblStatus.textLabel.text"))
            if cTime < 2:
                self.logger6.info("?????? ?????? ????????? ?????? ????????????.")
                return False
        except:
            return False
        else:
            return True

    def check_already_bet(self, table: int):
        bet_count = self.driver.execute_script(f"return window.user._hosts[{table}].bets.length")
        return True if bet_count != 0 else False

    def _health_checker(self):
        if (time.time() - self.last_update) > 30:
            raise TimeoutError("?????? ??????")

        self.timer = threading.Timer(5, self._health_checker)
        self.timer.daemon = True
        self.timer.start()

    def click1(self):
        self.driver.execute_script("user.updateBalance();"
                                   "GameLayerManager.Instance.sceneLayer.$children[0].lobbyFooter.btnRefreshBalance.startProcessing(1e3);")
        time.sleep(random.uniform(0.1, 0.15))
        self.driver.execute_script("GameLayerManager.Instance.sceneLayer.$children[0].counter = 0")
        time.sleep(random.uniform(0.1, 0.15))
        return "Click to balance"
        # self.logger7.info('????????? ??????')
        # print('????????? ??????')

    def change(self, num):
        change = self.driver.execute_script(
            "return GameLayerManager.Instance.sceneLayer.$children[0].lobbyFooter.lblBalance.text")
        time.sleep(random.uniform(num[0], num[1]))
        changez = int(change.replace('KRW', '').replace('.00', '').replace(',', ''))
        print(f'?????? :  {changez}')
        self.changez = changez
        return changez

    def setup(self, url, _id, _id2, _pw):
        self._url, self._id, self._id2, self._pw = url, _id, _id2, _pw
        self._login()
        self._wait_sa_load()
        self._switch_multi_bet()
        self._wait_multi_bet()
        # self.parent.sagameNotstart = False
        self.last_update = time.time()
        time.sleep(random.uniform(1, 2))
        self.video_reload_interval(2)
        if self.beforelimitfirst:
            self.change_bet_limit(0)
            self.beforelimitfirst = False
            self.logger9.info(f"first change betting limit num 0")
            time.sleep(random.uniform(0.5, 1))
            self.change([0.2, 0.4])

        # self._health_checker()

    def _check_config(self):
        if set(GS._DEFAULT_CONF_DB) != set((dict(self._config.items(GS._CONF_DB_KEY)).keys())):
            raise Exception("????????? ?????? ????????? ????????????.")
        if '' in dict(self._config.items(GS._CONF_DB_KEY)).values():
            raise Exception("???????????? ????????? ????????????.")

        if set(GS._DEFAULT_CONF_SITE) != set((dict(self._config.items(GS._CONF_SITE_KEY)).keys())):
            raise Exception("????????? ?????? ????????? ????????????.")
        if '' in dict(self._config.items(GS._CONF_SITE_KEY)).values():
            raise Exception("???????????? ????????? ????????????.")

        if set(GS._DEFAULT_CONF_SERVICE) != set((dict(self._config.items(GS._CONF_SERVICE_KEY)).keys())):
            raise Exception("????????? ?????? ????????? ????????????.")
        if '' in dict(self._config.items(GS._CONF_SERVICE_KEY)).values():
            raise Exception("???????????? ????????? ????????????.")

    def _health_checker(self):
        if (time.time() - self.last_update) > 10 * 4:
            self.logger9.info("???????????? ??????")
            raise TimeoutError("?????? ??????")

        self.timer = threading.Timer(5, self._health_checker)
        self.timer.daemon = True
        self.timer.start()

    def release_all(self):
        try:
            self.driver.quit()
        finally:
            print("??? ???????????? ??????")

        try:
            os.system("taskkill /f /im chromedriver.exe /t")
            self.driver.close()
            time.sleep(3)
        finally:
            time1 = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"{time1} : ?????? ???????????? ??????")


# Tr ?????? ?????? ?????????
class _RequestManager(QThread):
    threadEvent = pyqtSignal(dict)

    # taskQueue = []

    def __init__(self, request_delay=200):
        QThread.__init__(self)
        self.request_delay = request_delay
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self._status = True
        self.taskQueue = []

    def __del__(self):
        self.wait()

    def run(self):
        while self._status:
            # e = len(self.taskQueue)
            if self.taskQueue:
                nowtime = datetime.datetime.now()
                num = 0
                self.mutex.lock()
                try:
                    task = self.taskQueue.pop()
                # self.logger1.info(f'{nowtime} : {task}, {len(self.taskQueue)}')
                except Exception as ex:
                    self.logger1.info("????????? ?????? ????????????", ex)
                    num = 1
                self.mutex.unlock()

                if num == 0:
                    self.threadEvent.emit(task)
                # self.msleep(self.request_delay)

    def requestTrTask(self, task):
        self.mutex.lock()
        self.taskQueue.insert(0, task)
        self.mutex.unlock()
        self.msleep(self.request_delay)

