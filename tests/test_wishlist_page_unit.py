# -*- coding: utf-8 -*-
"""WishListPage._key() için tarayıcısız birim testleri.

_key(), ürün adının ilk n kelimesini küçük harfe çevirerek 8/9/10. adımlardaki
(assert_contains / delete / assert_absent) eşleştirme anahtarını üretir. Saf ve
WebDriver'dan bağımsız olduğu için birim test edilir. @staticmethod olduğundan
driver'a gerek yok. Hem pytest ile hem de doğrudan `python3` ile çalışır.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.wishlist_page import WishListPage  # noqa: E402

key = WishListPage._key


def test_ilk_dort_kelime_alinir():
    assert key("Samsung 990 EVO Plus SSD 2TB") == "samsung 990 evo plus"


def test_kucuk_harfe_cevirir():
    assert key("SAMSUNG T9 Portable SSD") == "samsung t9 portable ssd"


def test_dort_kelimeden_kisa_ad_oldugu_gibi_kalir():
    assert key("Samsung") == "samsung"


def test_fazla_bosluklar_normalize_edilir():
    assert key("  Samsung   Type-C   USB   Flash   Drive  ") == "samsung type-c usb flash"


def test_n_parametresi_kelime_sayisini_belirler():
    assert key("bir iki uc dort bes", n=2) == "bir iki"


def test_bos_ad_bos_anahtar_uretir():
    assert key("") == ""


def _run_all():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} test geçti.")
    return failed


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
