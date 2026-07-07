# -*- coding: utf-8 -*-
"""Ürün detay sayfası - ADIM 6'nın 'Add to List' akışı."""
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage


class ProductPage(BasePage):
    TITLE = (By.ID, "productTitle")
    ADD_BUTTON = (By.ID, "add-to-wishlist-button-submit")

    def get_title(self):
        """Detay sayfasındaki gerçek ürün başlığı (doğrulama için güvenilir)."""
        try:
            return self.wait_visible(*self.TITLE).text.strip()
        except TimeoutException:
            return ""

    def add_to_list(self):
        """'Add to List' butonuna basar ve açılan pencereyi tamamlar."""
        btn = self.wait_clickable(*self.ADD_BUTTON)
        self.safe_click(btn)
        assert self.complete_add_to_list(), \
            "Ürün listeye eklenemedi ('Add to List' penceresi tamamlanamadı)."

    def complete_add_to_list(self):
        """'Add to List' sonrası oluşan durumu tamamlar/doğrular. Üç durum:
          (1) BAŞARI onay paneli (huc-atwl): mevcut varsayılan liste varsa ana
              butona basınca ürün doğrudan eklenir → başarı.
          (2) Liste SEÇME menüsü: mevcut listelerden ilkine tıkla.
          (3) Yeni liste OLUŞTURMA formu (hiç liste yoksa): 'create-list-submit'
              hem listeyi oluşturur hem ürünü ekler (varsayılan ad 'Shopping List').
        Başarılıysa True döner."""
        for _ in range(8):
            time.sleep(1)
            # (1) Başarı onay paneli ya da inline başarı mesajı
            if any(e.is_displayed() for e in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "#huc-atwl-inner, #huc-list-link, #huc-atwl-header-section")):
                return True
            succ = self.driver.find_elements(By.ID, "atwl-inline-sucess-msg")
            if succ and succ[0].is_displayed() and (succ[0].text or "").strip():
                return True
            # (2) Mevcut liste seçme öğeleri
            for by, sel in [
                (By.CSS_SELECTOR, "[data-wl-list-id]"),
                (By.CSS_SELECTOR, "#atwl-list-item-0"),
            ]:
                items = [e for e in self.driver.find_elements(by, sel)
                         if e.is_displayed()]
                if items:
                    self.safe_click(items[0])
                    time.sleep(2)
                    return True
            # (3) Yeni liste oluşturma formu (listesi olmayan hesap)
            for by, sel in [
                (By.CSS_SELECTOR, "[data-action='create-list-submit']"),
                (By.ID, "lists-createlist-createAndAddAsin"),
                (By.CSS_SELECTOR, "#create-list-form input[type='submit']"),
            ]:
                subs = [e for e in self.driver.find_elements(by, sel)
                        if e.is_displayed()]
                if subs:
                    names = [e for e in self.driver.find_elements(By.ID, "list-name")
                             if e.is_displayed()]
                    if names and not (names[0].get_attribute("value") or "").strip():
                        names[0].send_keys("Shopping List")
                    self.safe_click(subs[0])
                    time.sleep(3)
                    return True
        return False
