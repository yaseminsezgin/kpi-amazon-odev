# -*- coding: utf-8 -*-
"""
Amazon.com UI Otomasyon Ödevi - POM (Page Object Model)
=======================================================

10 adım, sayfa nesneleri (pages/) üzerinden çağrılır; locator'lar bu dosyada
DEĞİL, ilgili sayfa sınıflarındadır.

Çalıştırma:
    pip install selenium
    export AMAZON_EMAIL="mail@ornek.com"
    export AMAZON_PASSWORD="parola"
    python3 tests/test_amazon.py
"""
import os
import sys
import time

# Proje kökünü import yoluna ekle (pages paketine erişmek için)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.base_page import build_driver          # noqa: E402
from pages.home_page import HomePage              # noqa: E402
from pages.login_page import LoginPage            # noqa: E402
from pages.wishlist_page import WishListPage      # noqa: E402

EMAIL = os.getenv("AMAZON_EMAIL", "")
PASSWORD = os.getenv("AMAZON_PASSWORD", "")
SEARCH_TERM = "samsung"


def run():
    if not EMAIL or not PASSWORD:
        raise RuntimeError(
            "AMAZON_EMAIL ve AMAZON_PASSWORD ortam değişkenlerini ayarlayın."
        )

    driver = build_driver()
    try:
        # ADIM 1 — Anasayfayı aç ve doğrula
        print("ADIM 1: Anasayfa açılıyor...")
        home = HomePage(driver).open()
        home.assert_loaded()
        print("   -> Anasayfa açıldı ve doğrulandı.")

        # ADIM 2 — Login
        print("ADIM 2: Login yapılıyor...")
        login = LoginPage(driver).open()
        login.login(EMAIL, PASSWORD)
        greeting = login.assert_logged_in()
        print(f"   -> Login başarılı. Hesap alanı: '{greeting.strip()}'")

        # ADIM 3 — 'samsung' araması
        print(f"ADIM 3: '{SEARCH_TERM}' aranıyor...")
        results = home.search(SEARCH_TERM)
        print("   -> Arama gönderildi.")

        # ADIM 4 — Sonuç bulunduğunu doğrula
        print("ADIM 4: Arama sonuçları doğrulanıyor...")
        count = results.assert_has_results(SEARCH_TERM)
        print(f"   -> {count} adet sonuç bulundu, doğrulandı.")

        # ADIM 5 — 2. sayfaya git ve doğrula
        print("ADIM 5: 2. sayfaya geçiliyor...")
        results.go_to_page(2)
        print("   -> 2. sayfa açıldı ve aktif sayfanın '2' olduğu doğrulandı.")

        # ADIM 6 — 3. ürünün 'Add to List' butonuna tıkla
        print("ADIM 6: 3. ürün favori listesine ekleniyor...")
        product_name = results.add_nth_to_list(3)
        print(f"   -> Eklenen ürün: {product_name!r}")

        # ADIM 7 — 'Lists' menüsünden Wish List'i aç
        print("ADIM 7: 'Lists' menüsünden Wish List açılıyor...")
        wishlist = WishListPage(driver).open_from_nav()
        print("   -> Wish List sayfası açıldı.")

        # ADIM 8 — Ürünün listede olduğunu doğrula
        print("ADIM 8: Ürünün listede olduğu doğrulanıyor...")
        wishlist.assert_contains(product_name)
        print("   -> Ürünün Wish List'te olduğu doğrulandı.")

        # ADIM 9 — Ürünü listeden sil
        print("ADIM 9: Ürün listeden siliniyor...")
        wishlist.delete(product_name)
        print("   -> 'Delete' butonuna basıldı.")

        # ADIM 10 — Ürünün listeden çıktığını doğrula
        print("ADIM 10: Ürünün listeden çıktığı doğrulanıyor...")
        wishlist.assert_absent(product_name)
        print("   -> Ürünün favorilerden çıkarıldığı doğrulandı.")

        print("\n*** TÜM ADIMLAR BAŞARIYLA TAMAMLANDI ***")

    except Exception as e:
        print(f"\n!!! HATA: {type(e).__name__}: {e}")
        # Hata anında incelemek için ekran görüntüsü kaydet
        try:
            outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diag")
            os.makedirs(outdir, exist_ok=True)
            path = os.path.join(outdir, "pom_failure.png")
            driver.save_screenshot(path)
            print(f"   Ekran görüntüsü: {os.path.abspath(path)}  (URL: {driver.current_url})")
        except Exception:
            pass
        raise
    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    run()
