# -*- coding: utf-8 -*-
"""Wish List (favori liste) sayfası - ADIM 7, 8, 9, 10."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage, WAIT_TIMEOUT


class WishListPage(BasePage):
    # ACCOUNT_LINK, BasePage'ten miras alınır (ortak üst-navigasyon locator'ı).
    DIRECT_URL = "https://www.amazon.com/hz/wishlist/ls"

    ITEM_PRESENT = (By.CSS_SELECTOR, "[id^='itemName_'], .g-item-sortable")
    ITEM_TITLES = (By.CSS_SELECTOR, "[id^='itemName_'], .g-item-sortable h2, .g-title a")
    ITEM_ROWS = (By.CSS_SELECTOR, "li.g-item-sortable, [id^='item_']")

    # Güncel Amazon Wish List DOM'unda silme kontrolü:
    #   <span id="delete-button-XXX"><input name="submit.deleteItem" type="submit" ...></span>
    DELETE_BUTTONS = [
        (By.CSS_SELECTOR, "input[name='submit.deleteItem']"),
        (By.CSS_SELECTOR, "[data-csa-c-action*='itemDelete']"),
        (By.CSS_SELECTOR, "span[id^='delete-button-'] input[type='submit']"),
        (By.CSS_SELECTOR, "[data-action='reg-item-delete']"),
        (By.CSS_SELECTOR, "[id^='itemDeleteButton_']"),
        (By.XPATH, ".//a[contains(., 'Delete')]"),
        (By.XPATH, ".//button[contains(., 'Delete')]"),
    ]

    def open_from_nav(self):
        """ADIM 7: üstteki 'Account & Lists' üzerine gelip (hover) liste flyout'undan
        Wish List'e gider; olmazsa doğrudan wishlist sayfasına gider."""
        clicked = False
        try:
            account = self.wait_visible(*self.ACCOUNT_LINK)
            self.scroll_into_view(account)
            ActionChains(self.driver).move_to_element(account).perform()
            time.sleep(2)
            clicked = self.click_first([
                (By.CSS_SELECTOR, "#nav-flyout-wl-items a[href*='/hz/wishlist']"),
                (By.XPATH, "//a[contains(@href,'/hz/wishlist')]"),
            ])
        except Exception:
            clicked = False

        if not clicked:
            self.driver.get(self.DIRECT_URL)

        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            lambda d: "/hz/wishlist" in d.current_url
        )
        time.sleep(2)

        # Öğeler görünmüyorsa ve birden fazla liste kartı varsa ilk listeye gir.
        if not self.driver.find_elements(*self.ITEM_PRESENT):
            cards = [e for e in self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/hz/wishlist/ls/']") if e.is_displayed()]
            if cards:
                self.safe_click(cards[0])
                time.sleep(2)
        return self

    # ------------------------------------------------------------------ #
    def item_titles(self):
        els = self.driver.find_elements(*self.ITEM_TITLES)
        return [e.text.strip() for e in els if e.text.strip()]

    @staticmethod
    def _key(name, n=4):
        """Ürün adının ilk n kelimesini karşılaştırma anahtarı olarak alır."""
        return " ".join(name.split()[:n]).lower()

    def assert_contains(self, product_name):
        """ADIM 8: eklenen ürün listede olmalı."""
        self.wait_visible(*self.ITEM_PRESENT)
        key = self._key(product_name)
        titles = self.item_titles()
        assert any(key in t.lower() for t in titles), (
            f"Eklenen ürün Wish List'te bulunamadı!\n"
            f"Aranan: {key!r}\nListedekiler: {titles}"
        )
        return self

    def delete(self, product_name):
        """ADIM 9: ürünü listeden siler."""
        key = self._key(product_name)
        target = None
        for it in self.driver.find_elements(*self.ITEM_ROWS):
            if key in it.text.lower():
                target = it
                break
        assert target is not None, "Silinecek ürün satırı bulunamadı."

        self.scroll_into_view(target)
        time.sleep(1)

        del_btn = self.find_first(self.DELETE_BUTTONS, root=target)
        assert del_btn is not None, "'Delete' butonu bulunamadı."

        self.safe_click(del_btn)
        time.sleep(3)  # 'reg-item-delete' anında siler; DOM güncellensin
        return self

    def assert_absent(self, product_name):
        """ADIM 10: ürün artık listede OLMAMALI."""
        key = self._key(product_name)
        time.sleep(2)
        titles = self.item_titles()
        assert not any(key in t.lower() for t in titles), (
            f"Ürün hâlâ Wish List'te görünüyor! Silme başarısız.\n"
            f"Listedekiler: {titles}"
        )
        return self
