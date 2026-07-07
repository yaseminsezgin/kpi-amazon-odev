# -*- coding: utf-8 -*-
"""Arama sonuçları sayfası - ADIM 4, 5, 6."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from pages.base_page import BasePage, WAIT_TIMEOUT
from pages.product_page import ProductPage


class SearchResultsPage(BasePage):
    MAIN_SLOT = (By.CSS_SELECTOR, "div.s-main-slot")
    RESULTS = (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    SELECTED_PAGE = (By.CSS_SELECTOR, "span.s-pagination-selected")

    # Kart üzerindeki 'Add to List' adayları
    CARD_ADD_BUTTONS = [
        (By.XPATH, ".//a[contains(., 'Add to List')]"),
        (By.XPATH, ".//button[contains(., 'Add to List')]"),
        (By.XPATH, ".//input[@aria-label='Add to List' or @value='Add to List']"),
        (By.CSS_SELECTOR, "[id^='add-to-wishlist']"),
    ]

    def assert_has_results(self, term):
        """ADIM 4: en az bir sonuç ve sayfa aramaya ait olmalı. Sonuç sayısını döndürür."""
        self.wait_visible(*self.MAIN_SLOT)
        results = self.driver.find_elements(*self.RESULTS)
        assert len(results) > 0, f"'{term}' için hiç sonuç bulunamadı!"
        assert term in self.current_url.lower() or term in self.driver.title.lower(), \
            f"Sonuç sayfası '{term}' aramasına ait görünmüyor."
        return len(results)

    def go_to_page(self, n):
        """ADIM 5: n. sayfaya geçer ve aktif sayfanın n olduğunu doğrular."""
        page = self.wait_clickable(
            By.CSS_SELECTOR, f"a.s-pagination-item[aria-label='Go to page {n}']"
        )
        self.scroll_into_view(page)
        time.sleep(1)
        self.safe_click(page)
        selected = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located(self.SELECTED_PAGE)
        )
        assert selected.text.strip() == str(n), \
            f"Aktif sayfa {n} değil, görünen: '{selected.text.strip()}'"
        assert f"page={n}" in self.current_url, \
            f"URL {n}. sayfayı göstermiyor: {self.current_url}"
        return self

    def results(self):
        return self.driver.find_elements(*self.RESULTS)

    def add_nth_to_list(self, n):
        """ADIM 6: üstten n. ürünü favori listesine ekler. Ürün adını döndürür.

        Kartta 'Add to List' varsa oradan; yoksa ürün detayına girip ekler.
        Detaya girildiğinde daha güvenilir olan gerçek ürün başlığı alınır."""
        results = self.results()
        assert len(results) >= n, f"Sayfada en az {n} ürün yok!"
        item = results[n - 1]

        # Kart adı (detaya girersek gerçek başlıkla güncellenir)
        try:
            product_name = item.find_element(By.CSS_SELECTOR, "h2").text.strip()
        except NoSuchElementException:
            product_name = item.find_element(
                By.CSS_SELECTOR, "[data-cy='title-recipe']"
            ).text.strip()

        self.scroll_into_view(item)
        time.sleep(1)

        # Kart üzerinde 'Add to List' butonu var mı? (kart öğesinin altında ara)
        card_btn = self.find_first(self.CARD_ADD_BUTTONS, root=item)

        product = ProductPage(self.driver)
        if card_btn is not None:
            self.safe_click(card_btn)
            assert product.complete_add_to_list(), \
                "Ürün listeye eklenemedi ('Add to List' penceresi tamamlanamadı)."
        else:
            # Kartta yok → ürün detayına gir, gerçek başlığı al, oradan ekle.
            link = item.find_element(By.CSS_SELECTOR, "h2 a, a.a-link-normal")
            self.safe_click(link)
            product_name = product.get_title() or product_name
            product.add_to_list()

        return product_name
