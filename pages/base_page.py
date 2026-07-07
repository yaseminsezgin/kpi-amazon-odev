# -*- coding: utf-8 -*-
"""POM - Temel sayfa sınıfı ve ortak yardımcılar.

Tüm sayfa nesneleri BasePage'ten türer. Locator/eylem tekrarını önlemek için
bekleme, güvenli tıklama, popover kapatma gibi ortak davranışlar burada toplanır.
"""
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
)

WAIT_TIMEOUT = 20   # normal elementler için bekleme (sn)
MANUAL_WAIT = 90    # OTP / captcha'yı elle çözmek için verilen süre (sn)


def build_driver():
    """Chrome driver'ı bot-tespitini azaltan ayarlarla kurar.
    Selenium 4.6+ 'Selenium Manager' chromedriver'ı otomatik indirir."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    driver.implicitly_wait(3)
    return driver


class BasePage:
    """Tüm sayfa nesnelerinin ortak atası."""

    # Üst navigasyondaki 'Account & Lists' linki — birden çok sayfa kullanır.
    ACCOUNT_LINK = (By.ID, "nav-link-accountList")

    def __init__(self, driver):
        self.driver = driver

    # ----------------------------- Beklemeler ----------------------------- #
    def wait_visible(self, by, selector, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )

    def wait_clickable(self, by, selector, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )

    def find_first_visible(self, candidates, timeout=WAIT_TIMEOUT):
        """(By, selector) adaylarından ilk GÖRÜNÜR olanı bekleyip döndürür.
        Amazon farklı hesap/bölge/deney gruplarında farklı id'ler kullanır."""
        def _locate(d):
            for by, sel in candidates:
                for el in d.find_elements(by, sel):
                    if el.is_displayed():
                        return el
            return False
        return WebDriverWait(self.driver, timeout).until(_locate)

    def find_first(self, candidates, root=None):
        """Adaylardan ilk EŞLEŞEN (By, selector) öğeyi döndürür. root verilirse o
        öğenin ALTINDA, verilmezse tüm sayfada arar. Bulunamazsa None döner.
        (Görünürlük filtresi uygulamaz; kart/satır içi ilk eşleşmeyi bulmak için.)"""
        scope = root if root is not None else self.driver
        for by, sel in candidates:
            found = scope.find_elements(by, sel)
            if found:
                return found[0]
        return None

    # ----------------------------- Eylemler ------------------------------- #
    def click_first(self, candidates):
        """Adaylardan ilk GÖRÜNÜR öğeyi tıklar. Tıklarsa True, hiçbiri yoksa False."""
        for by, sel in candidates:
            els = [e for e in self.driver.find_elements(by, sel) if e.is_displayed()]
            if els:
                self.safe_click(els[0])
                return True
        return False

    def safe_click(self, element):
        """Normal click engellenirse JS ile tıkla."""
        try:
            element.click()
        except (ElementClickInterceptedException, Exception):
            self.driver.execute_script("arguments[0].click();", element)

    def scroll_into_view(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element
        )

    def dismiss_popups(self):
        """Teslimat adresi / 'Continue shopping' gibi araya giren popup'ları kapatır."""
        for by, sel in [
            (By.CSS_SELECTOR, "input[data-action-type='DISMISS']"),
            (By.CSS_SELECTOR, "button[data-action='a-popover-close']"),
            (By.XPATH, "//button[normalize-space()='Dismiss']"),
            (By.XPATH, "//button[contains(text(),'Continue shopping')]"),
        ]:
            try:
                el = self.driver.find_element(by, sel)
                if el.is_displayed():
                    self.safe_click(el)
                    time.sleep(1)
            except NoSuchElementException:
                pass

    # ----------------------------- Yardımcı ------------------------------- #
    @property
    def current_url(self):
        return self.driver.current_url
