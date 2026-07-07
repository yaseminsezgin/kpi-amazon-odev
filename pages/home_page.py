# -*- coding: utf-8 -*-
"""Anasayfa nesnesi (ADIM 1 ve ADIM 3'ün arama kutusu)."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage, WAIT_TIMEOUT
from pages.search_results_page import SearchResultsPage


class HomePage(BasePage):
    URL = "https://www.amazon.com"

    NAV_LOGO = (By.ID, "nav-logo-sprites")
    SEARCH_BOX = (By.ID, "twotabsearchtextbox")
    SEARCH_BUTTON = (By.ID, "nav-search-submit-button")

    def open(self):
        self.driver.get(self.URL)
        self.dismiss_popups()
        return self

    def assert_loaded(self):
        """ADIM 1 doğrulamaları: başlık, logo ve arama kutusu."""
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(EC.title_contains("Amazon"))
        assert "amazon" in self.driver.title.lower(), \
            f"Anasayfa başlığı beklenenden farklı: {self.driver.title}"
        logo = self.wait_visible(*self.NAV_LOGO)
        assert logo.is_displayed(), "Amazon logosu görünmüyor - anasayfa açılmadı."
        assert self.driver.find_elements(*self.SEARCH_BOX), \
            "Arama kutusu bulunamadı - anasayfa tam yüklenmedi."
        return self

    def search(self, term):
        """ADIM 3: arama kutusuna terimi yazıp arar. SearchResultsPage döndürür."""
        box = self.wait_visible(*self.SEARCH_BOX)
        box.clear()
        box.send_keys(term)
        self.safe_click(self.driver.find_element(*self.SEARCH_BUTTON))
        return SearchResultsPage(self.driver)
