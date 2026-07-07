# -*- coding: utf-8 -*-
"""
Amazon.com UI Otomasyon Ödevi - Python + Selenium
==================================================

Adımlar:
 1. www.amazon.com açılır ve anasayfa açıldığı assertion ile doğrulanır.
 2. Login ekranı açılır ve bir kullanıcı ile login olunur (OTP gelirse beklenir).
 3. Search alanına 'samsung' yazılıp ara butonuna tıklanır.
 4. Samsung için sonuç bulunduğu doğrulanır.
 5. 2. sayfaya tıklanır ve 2. sayfanın gösterimde olduğu doğrulanır.
 6. Üstten 3. ürünün 'Add to List' butonuna tıklanır.
 7. Üstteki 'Lists' linkinden Wish List seçilir.
 8. İzlemeye alınan ürünün listede bulunduğu doğrulanır.
 9. Ürünün yanındaki 'Delete' butonuna basılıp favorilerden çıkarılır.
10. Ürünün artık favorilerde olmadığı doğrulanır.

Çalıştırma:
    pip install selenium
    # Kullanıcı bilgilerini ortam değişkeni olarak vermek en güvenlisidir:
    export AMAZON_EMAIL="mail@ornek.com"
    export AMAZON_PASSWORD="parola"
    python3 amazon_test.py

Notlar:
 - Selenium 4.6+ ile gelen "Selenium Manager" chromedriver'ı otomatik indirir,
   ayrıca bir driver kurmaya gerek yoktur.
 - Amazon güçlü bir bot koruması kullanır. Captcha / OTP çıkarsa script
   MANUAL_WAIT süresi kadar bekler; bu süre içinde ekrandan captcha/OTP'yi
   elle çözebilirsiniz.
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)

# --------------------------------------------------------------------------- #
# Ayarlar
# --------------------------------------------------------------------------- #
EMAIL = os.getenv("AMAZON_EMAIL", "")        # ör: export AMAZON_EMAIL="..."
PASSWORD = os.getenv("AMAZON_PASSWORD", "")  # ör: export AMAZON_PASSWORD="..."

WAIT_TIMEOUT = 20          # normal elementler için bekleme (sn)
MANUAL_WAIT = 90           # OTP / captcha'yı elle çözmek için verilen süre (sn)
SEARCH_TERM = "samsung"


# --------------------------------------------------------------------------- #
# Yardımcı fonksiyonlar
# --------------------------------------------------------------------------- #
def build_driver():
    """Chrome driver'ı bot-tespitini azaltan ayarlarla kurar."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Gerçek bir kullanıcıya benzemesi için user-agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    # navigator.webdriver bayrağını gizle
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    driver.implicitly_wait(3)
    return driver


def wait_visible(driver, by, selector, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, selector))
    )


def wait_clickable(driver, by, selector, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, selector))
    )


def safe_click(driver, element):
    """Normal click engellenirse JS ile tıkla."""
    try:
        element.click()
    except (ElementClickInterceptedException, Exception):
        driver.execute_script("arguments[0].click();", element)


def find_first_visible(driver, candidates, timeout=WAIT_TIMEOUT):
    """Verilen (By, selector) adaylarından ilk GÖRÜNÜR olanı bekleyip döndürür.
    Amazon farklı hesap/bölge/deney gruplarında farklı id'ler kullandığı için
    birden çok olası seçiciyi sırayla dener."""
    def _locate(d):
        for by, sel in candidates:
            for el in d.find_elements(by, sel):
                if el.is_displayed():
                    return el
        return False
    return WebDriverWait(driver, timeout).until(_locate)


def skip_account_fixup(driver):
    """Giriş sonrası çıkan 'Add a mobile number / Keep hackers out'
    (accountfixup) ara sayfasını 'Not now' linkine basarak atlar.
    Sayfa her zaman çıkmaz; çıkmazsa sessizce geçer."""
    for by, sel in [
        (By.ID, "ap-account-fixup-phone-skip-link"),
        (By.XPATH, "//a[normalize-space()='Not now']"),
        (By.XPATH, "//input[@aria-labelledby='ap-account-fixup-phone-skip-link']"),
        (By.LINK_TEXT, "Not now"),
    ]:
        els = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
        if els:
            print("   -> 'Add a mobile number' ara sayfası atlanıyor ('Not now').")
            safe_click(driver, els[0])
            time.sleep(2)
            return True
    return False


def dismiss_popups(driver):
    """Teslimat adresi / 'Continue shopping' gibi araya giren popup'ları kapatır."""
    for by, sel in [
        (By.CSS_SELECTOR, "input[data-action-type='DISMISS']"),
        (By.CSS_SELECTOR, "button[data-action='a-popover-close']"),
        (By.XPATH, "//button[normalize-space()='Dismiss']"),
        (By.XPATH, "//button[contains(text(),'Continue shopping')]"),
    ]:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                safe_click(driver, el)
                time.sleep(1)
        except NoSuchElementException:
            pass


# --------------------------------------------------------------------------- #
# ADIM 1 — Anasayfayı aç ve doğrula
# --------------------------------------------------------------------------- #
def step1_open_home(driver):
    print("ADIM 1: Anasayfa açılıyor...")
    driver.get("https://www.amazon.com")
    dismiss_popups(driver)

    # ASSERTION 1a: Sayfa başlığında 'Amazon' geçiyor mu?
    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.title_contains("Amazon"))
    assert "amazon" in driver.title.lower(), \
        f"Anasayfa başlığı beklenenden farklı: {driver.title}"

    # ASSERTION 1b: Amazon logosu (anasayfa navigasyonu) görünür mü?
    logo = wait_visible(driver, By.ID, "nav-logo-sprites")
    assert logo.is_displayed(), "Amazon logosu görünmüyor - anasayfa açılmadı."

    # ASSERTION 1c: Arama kutusu var mı? (anasayfanın yüklendiğinin kanıtı)
    assert driver.find_elements(By.ID, "twotabsearchtextbox"), \
        "Arama kutusu bulunamadı - anasayfa tam yüklenmedi."

    print("   -> Anasayfa başarıyla açıldı ve doğrulandı.")


# --------------------------------------------------------------------------- #
# ADIM 2 — Login
# --------------------------------------------------------------------------- #
def step2_login(driver):
    print("ADIM 2: Login yapılıyor...")
    if not EMAIL or not PASSWORD:
        raise RuntimeError(
            "AMAZON_EMAIL ve AMAZON_PASSWORD ortam değişkenlerini ayarlayın."
        )

    # Üst sağdaki 'Hello, sign in / Account & Lists' linkine tıkla
    account = wait_clickable(driver, By.ID, "nav-link-accountList")
    safe_click(driver, account)

    # E-posta gir → Continue
    # Amazon'un YENİ birleşik giriş ekranında alan id'si 'ap_email' değil
    # 'ap_email_login' olabiliyor; eski akışta ise 'ap_email'. İkisini de dene.
    email_input = find_first_visible(driver, [
        (By.ID, "ap_email"),
        (By.ID, "ap_email_login"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.NAME, "email"),
    ])
    email_input.clear()
    email_input.send_keys(EMAIL)
    # Continue butonu: id bazen 'continue', bazen 'continue-announce';
    # yeni sayfada submit input'u olabilir. Hiçbiri yoksa Enter'a bas.
    cont = None
    for by, sel in [
        (By.ID, "continue"),
        (By.ID, "continue-announce"),
        (By.CSS_SELECTOR, "input#continue"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ]:
        found = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
        if found:
            cont = found[0]
            break
    if cont is not None:
        safe_click(driver, cont)
    else:
        email_input.send_keys(Keys.RETURN)

    # Parola gir → Sign-In
    pwd_input = find_first_visible(driver, [
        (By.ID, "ap_password"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.NAME, "password"),
    ])
    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)
    submit = None
    for by, sel in [
        (By.ID, "signInSubmit"),
        (By.CSS_SELECTOR, "input#signInSubmit"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ]:
        found = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
        if found:
            submit = found[0]
            break
    if submit is not None:
        safe_click(driver, submit)
    else:
        pwd_input.send_keys(Keys.RETURN)

    # Giriş sonrası 'Add a mobile number' (accountfixup) ara sayfası çıkabilir;
    # varsa 'Not now' ile atla. Yüklenmesi için kısa bekleyip birkaç kez dene.
    for _ in range(3):
        time.sleep(2)
        if skip_account_fixup(driver):
            break
        if "accountfixup" not in driver.current_url.lower():
            break

    # OTP / captcha çıkabilir → kullanıcı elle çözene kadar bekle.
    # Login başarılı olunca Amazon anasayfaya döner ve URL artık '/ap/...'
    # (signin, accountfixup, mfa vb.) yolu İÇERMEZ.
    # DİKKAT: Giriş sonrası URL 'amazon.com/?ref_=nav_signin' olabilir; bu yüzden
    # düz 'signin' araması yanıltır ('nav_signin' içerir). '/ap/' yolunu kontrol et.
    print(f"   -> OTP/captcha çıkarsa {MANUAL_WAIT} sn içinde elle giriniz...")
    try:
        WebDriverWait(driver, MANUAL_WAIT).until(
            lambda d: "/ap/" not in d.current_url.lower()
            and d.find_elements(By.ID, "nav-link-accountList")
        )
    except TimeoutException:
        pass
    # Ara sayfa geç çıkarsa bir kez daha atlamayı dene.
    skip_account_fixup(driver)

    # ASSERTION 2: Login sonrası hesap alanı 'sign in' yerine kullanıcı adını
    # göstermeli (yani artık 'Hello, sign in' yazmamalı).
    greeting = wait_visible(driver, By.ID, "nav-link-accountList").text.lower()
    assert "sign in" not in greeting, \
        f"Login başarısız görünüyor, hesap alanı hâlâ: '{greeting}'"
    print(f"   -> Login başarılı. Hesap alanı: '{greeting.strip()}'")


# --------------------------------------------------------------------------- #
# ADIM 3 — 'samsung' araması
# --------------------------------------------------------------------------- #
def step3_search(driver):
    print(f"ADIM 3: '{SEARCH_TERM}' aranıyor...")
    box = wait_visible(driver, By.ID, "twotabsearchtextbox")
    box.clear()
    box.send_keys(SEARCH_TERM)
    # Ara butonu
    safe_click(driver, driver.find_element(By.ID, "nav-search-submit-button"))
    print("   -> Arama gönderildi.")


# --------------------------------------------------------------------------- #
# ADIM 4 — Sonuç bulunduğunu doğrula
# --------------------------------------------------------------------------- #
def step4_verify_results(driver):
    print("ADIM 4: Arama sonuçları doğrulanıyor...")

    # Sonuç kartlarının yüklenmesini bekle
    wait_visible(driver, By.CSS_SELECTOR, "div.s-main-slot")
    results = driver.find_elements(
        By.CSS_SELECTOR, "div[data-component-type='s-search-result']"
    )

    # ASSERTION 4a: En az bir sonuç kartı gelmiş olmalı
    assert len(results) > 0, "'samsung' için hiç sonuç bulunamadı!"

    # ASSERTION 4b: Sonuç bilgi çubuğu / URL 'samsung' içeriyor olmalı
    assert "samsung" in driver.current_url.lower() or \
        "samsung" in driver.title.lower(), \
        "Sonuç sayfası 'samsung' aramasına ait görünmüyor."

    print(f"   -> {len(results)} adet sonuç bulundu, 'samsung' sonuçları doğrulandı.")


# --------------------------------------------------------------------------- #
# ADIM 5 — 2. sayfaya git ve doğrula
# --------------------------------------------------------------------------- #
def step5_go_page2(driver):
    print("ADIM 5: 2. sayfaya geçiliyor...")

    # Sayfalama en altta, önce oraya kaydır
    page2 = wait_clickable(
        driver, By.CSS_SELECTOR, "a.s-pagination-item[aria-label='Go to page 2']"
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", page2)
    time.sleep(1)
    safe_click(driver, page2)

    # 2. sayfanın yüklenmesini bekle: seçili sayfa göstergesi '2' olmalı
    selected = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "span.s-pagination-selected")
        )
    )

    # ASSERTION 5a: Aktif (seçili) sayfa numarası '2' olmalı
    assert selected.text.strip() == "2", \
        f"Aktif sayfa 2 değil, görünen: '{selected.text.strip()}'"

    # ASSERTION 5b: URL 'page=2' içermeli
    assert "page=2" in driver.current_url, \
        f"URL 2. sayfayı göstermiyor: {driver.current_url}"

    print("   -> 2. sayfa açıldı ve aktif sayfanın '2' olduğu doğrulandı.")


# --------------------------------------------------------------------------- #
# ADIM 6 — 3. ürünün 'Add to List' butonuna tıkla
# --------------------------------------------------------------------------- #
def _complete_add_to_list(driver):
    """'Add to List' butonuna basıldıktan sonra oluşan durumu tamamlar/doğrular.
    Üç olası durum:
      (1) BAŞARI onayı paneli (huc-atwl): mevcut varsayılan liste varsa ana butona
          basınca ürün doğrudan eklenir ve 'Shopping List' bağlantılı onay paneli
          çıkar → başarı.
      (2) Liste SEÇME menüsü: mevcut listelerden ilkine tıkla.
      (3) Yeni liste OLUŞTURMA formu (hiç liste yoksa): 'create-list-submit' hem
          listeyi oluşturur hem ürünü ekler; liste adı varsayılan 'Shopping List'.
    Başarılıysa True döner."""
    for _ in range(8):
        time.sleep(1)
        # (1) Başarı onay paneli (huc-atwl) ya da inline başarı mesajı
        if any(e.is_displayed() for e in driver.find_elements(
                By.CSS_SELECTOR, "#huc-atwl-inner, #huc-list-link, #huc-atwl-header-section")):
            return True
        succ = driver.find_elements(By.ID, "atwl-inline-sucess-msg")
        if succ and succ[0].is_displayed() and (succ[0].text or "").strip():
            return True
        # (2) Mevcut liste seçme öğeleri
        for by, sel in [
            (By.CSS_SELECTOR, "[data-wl-list-id]"),
            (By.CSS_SELECTOR, "#atwl-list-item-0"),
        ]:
            items = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
            if items:
                safe_click(driver, items[0])
                time.sleep(2)
                return True
        # (3) Yeni liste oluşturma formu (listesi olmayan hesap)
        for by, sel in [
            (By.CSS_SELECTOR, "[data-action='create-list-submit']"),
            (By.ID, "lists-createlist-createAndAddAsin"),
            (By.CSS_SELECTOR, "#create-list-form input[type='submit']"),
        ]:
            subs = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
            if subs:
                names = [e for e in driver.find_elements(By.ID, "list-name")
                         if e.is_displayed()]
                if names and not (names[0].get_attribute("value") or "").strip():
                    names[0].send_keys("Shopping List")
                safe_click(driver, subs[0])
                time.sleep(3)
                return True
    return False


def step6_add_third_to_list(driver):
    print("ADIM 6: 3. ürün favori listesine ekleniyor...")

    results = driver.find_elements(
        By.CSS_SELECTOR, "div[data-component-type='s-search-result']"
    )
    assert len(results) >= 3, "Sayfada en az 3 ürün yok!"
    third = results[2]  # üstten 3. ürün (0-index)

    # Ürün adını sakla (Adım 8 ve 10'da doğrulamak için)
    try:
        product_name = third.find_element(By.CSS_SELECTOR, "h2").text.strip()
    except NoSuchElementException:
        product_name = third.find_element(
            By.CSS_SELECTOR, "[data-cy='title-recipe']"
        ).text.strip()
    print(f"   -> 3. ürün: {product_name!r}")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", third)
    time.sleep(1)

    # Kart üzerindeki 'Add to List' butonunu bul.
    # Amazon layout'una göre 'Add to List' bir <a>/<button>/<input> olabilir;
    # metne göre esnek arıyoruz.
    add_btn = None
    for by, sel in [
        (By.XPATH, ".//a[contains(., 'Add to List')]"),
        (By.XPATH, ".//button[contains(., 'Add to List')]"),
        (By.XPATH, ".//input[@aria-label='Add to List' or @value='Add to List']"),
        (By.CSS_SELECTOR, "[id^='add-to-wishlist']"),
    ]:
        found = third.find_elements(by, sel)
        if found:
            add_btn = found[0]
            break

    if add_btn is None:
        # Bazı layout'larda 'Add to List' kartta görünmez; ürün detayına girip
        # detay sayfasındaki wishlist butonu kullanılır.
        print("   -> Kartta 'Add to List' yok, ürün detayına giriliyor...")
        link = third.find_element(By.CSS_SELECTOR, "h2 a, a.a-link-normal")
        safe_click(driver, link)
        # Detay sayfasından GERÇEK ürün başlığını al (doğrulama için daha güvenilir).
        try:
            product_name = wait_visible(driver, By.ID, "productTitle").text.strip()
        except TimeoutException:
            pass
        add_btn = wait_clickable(driver, By.ID, "add-to-wishlist-button-submit")

    print(f"   -> Eklenecek ürün: {product_name!r}")
    safe_click(driver, add_btn)

    # 'Add to List' popover'ını tamamla (yeni liste oluştur ya da mevcut listeye ekle).
    assert _complete_add_to_list(driver), \
        "Ürün listeye eklenemedi ('Add to List' penceresi tamamlanamadı)."

    print("   -> Ürün favori listesine eklendi.")
    return product_name


# --------------------------------------------------------------------------- #
# ADIM 7 — 'Lists' linkinden Wish List'i aç
# --------------------------------------------------------------------------- #
def step7_open_wishlist(driver):
    print("ADIM 7: 'Lists' menüsünden Wish List açılıyor...")

    # Üstteki 'Account & Lists' ÜZERİNE GELİNCE (hover) liste flyout'u açılır.
    clicked = False
    try:
        account = wait_visible(driver, By.ID, "nav-link-accountList")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", account)
        ActionChains(driver).move_to_element(account).perform()
        time.sleep(2)
        for by, sel in [
            (By.CSS_SELECTOR, "#nav-flyout-wl-items a[href*='/hz/wishlist']"),
            (By.XPATH, "//a[contains(@href,'/hz/wishlist')]"),
        ]:
            els = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
            if els:
                safe_click(driver, els[0])
                clicked = True
                break
    except Exception:
        pass

    # Flyout'tan gidilemediyse doğrudan wishlist sayfasına git (yedek yol).
    if not clicked:
        driver.get("https://www.amazon.com/hz/wishlist/ls")

    # Wish List sayfasının açıldığını bekle
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        lambda d: "/hz/wishlist" in d.current_url
    )
    time.sleep(2)

    # Öğeler görünmüyorsa ve birden fazla liste kartı varsa, ilk listeye tıkla.
    if not driver.find_elements(By.CSS_SELECTOR, "[id^='itemName_'], .g-item-sortable"):
        cards = [e for e in driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/hz/wishlist/ls/']") if e.is_displayed()]
        if cards:
            safe_click(driver, cards[0])
            time.sleep(2)
    print("   -> Wish List sayfası açıldı.")


# --------------------------------------------------------------------------- #
# ADIM 8 — Ürünün listede olduğunu doğrula
# --------------------------------------------------------------------------- #
def _wishlist_item_titles(driver):
    """Wish List sayfasındaki tüm ürün başlıklarını döndürür."""
    els = driver.find_elements(
        By.CSS_SELECTOR, "[id^='itemName_'], .g-item-sortable h2, .g-title a"
    )
    return [e.text.strip() for e in els if e.text.strip()]


def _key_tokens(name, n=4):
    """Ürün adının ilk n kelimesini karşılaştırma anahtarı olarak alır."""
    return " ".join(name.split()[:n]).lower()

def step8_verify_in_wishlist(driver, product_name):
    print("ADIM 8: Ürünün listede olduğu doğrulanıyor...")
    wait_visible(driver, By.CSS_SELECTOR, "[id^='itemName_'], .g-item-sortable")
    titles = _wishlist_item_titles(driver)
    key = _key_tokens(product_name)

    # ASSERTION 8: Eklenen ürün Wish List'te bulunmalı
    assert any(key in t.lower() for t in titles), (
        f"Eklenen ürün Wish List'te bulunamadı!\n"
        f"Aranan: {key!r}\nListedekiler: {titles}"
    )
    print("   -> Ürünün Wish List'te olduğu doğrulandı.")


# --------------------------------------------------------------------------- #
# ADIM 9 — Ürünü listeden sil
# --------------------------------------------------------------------------- #
def step9_delete_item(driver, product_name):
    print("ADIM 9: Ürün listeden siliniyor...")
    key = _key_tokens(product_name)

    # Ürün satırını (li) bul
    items = driver.find_elements(By.CSS_SELECTOR, "li.g-item-sortable, [id^='item_']")
    target = None
    for it in items:
        if key in it.text.lower():
            target = it
            break
    assert target is not None, "Silinecek ürün satırı bulunamadı."

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
    time.sleep(1)

    # Delete butonu (güncel Amazon Wish List DOM'u):
    #   <span id="delete-button-XXX"> <input name="submit.deleteItem" type="submit"
    #        data-csa-c-action="...itemDelete" aria-labelledby="delete-button-XXX-announce">
    # Yani gerçek kontrol 'submit.deleteItem' input'u; eski 'itemDeleteButton_' /
    # value='Delete' selektörleri artık yok.
    del_btn = None
    for by, sel in [
        (By.CSS_SELECTOR, "input[name='submit.deleteItem']"),
        (By.CSS_SELECTOR, "[data-csa-c-action*='itemDelete']"),
        (By.CSS_SELECTOR, "span[id^='delete-button-'] input[type='submit']"),
        (By.CSS_SELECTOR, "[data-action='reg-item-delete']"),
        (By.CSS_SELECTOR, "[id^='itemDeleteButton_']"),
        (By.XPATH, ".//a[contains(., 'Delete')]"),
        (By.XPATH, ".//button[contains(., 'Delete')]"),
    ]:
        found = target.find_elements(by, sel)
        if found:
            del_btn = found[0]
            break
    assert del_btn is not None, "'Delete' butonu bulunamadı."

    safe_click(driver, del_btn)
    time.sleep(3)  # 'reg-item-delete' anında siler; DOM'un güncellenmesini bekle
    print("   -> 'Delete' butonuna basıldı.")


# --------------------------------------------------------------------------- #
# ADIM 10 — Ürünün listeden çıktığını doğrula
# --------------------------------------------------------------------------- #
def step10_verify_deleted(driver, product_name):
    print("ADIM 10: Ürünün listeden çıktığı doğrulanıyor...")
    key = _key_tokens(product_name)
    time.sleep(2)  # DOM'un güncellenmesi için kısa bekleme

    # Silme sonrası 'öğe kaldırıldı' mesajı ya da boş liste görünebilir.
    titles = _wishlist_item_titles(driver)

    # ASSERTION 10: Ürün artık listede OLMAMALI
    assert not any(key in t.lower() for t in titles), (
        f"Ürün hâlâ Wish List'te görünüyor! Silme başarısız.\n"
        f"Listedekiler: {titles}"
    )
    print("   -> Ürünün favorilerden çıkarıldığı doğrulandı.")


# --------------------------------------------------------------------------- #
# Ana akış
# --------------------------------------------------------------------------- #
def _step_shot(driver, n):
    """STEP_MODE=1 iken her adımın ekran görüntüsünü diag/step_N.png olarak kaydeder."""
    if os.getenv("STEP_MODE") != "1":
        return
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"step_{n:02d}.png")
    try:
        driver.save_screenshot(path)
        print(f"   [STEP_MODE] Ekran görüntüsü: {path}  (URL: {driver.current_url})")
    except Exception as e:
        print(f"   [STEP_MODE] görüntü alınamadı: {type(e).__name__}: {e}")


def main():
    driver = build_driver()
    try:
        step1_open_home(driver);                        _step_shot(driver, 1)
        step2_login(driver);                            _step_shot(driver, 2)
        step3_search(driver);                           _step_shot(driver, 3)
        step4_verify_results(driver);                   _step_shot(driver, 4)
        step5_go_page2(driver);                         _step_shot(driver, 5)
        product_name = step6_add_third_to_list(driver); _step_shot(driver, 6)
        step7_open_wishlist(driver);                    _step_shot(driver, 7)
        step8_verify_in_wishlist(driver, product_name); _step_shot(driver, 8)
        step9_delete_item(driver, product_name);        _step_shot(driver, 9)
        step10_verify_deleted(driver, product_name);    _step_shot(driver, 10)
        print("\n*** TÜM ADIMLAR BAŞARIYLA TAMAMLANDI ***")
    except AssertionError as e:
        print(f"\n!!! ASSERTION HATASI: {e}")
        _dump_diagnostics(driver)
        raise
    except Exception as e:
        print(f"\n!!! HATA: {type(e).__name__}: {e}")
        _dump_diagnostics(driver)
        raise
    finally:
        # İncelemek için biraz bekleyip tarayıcıyı kapat.
        # Tanılama modunda tarayıcıyı açık bırakmak için KEEP_OPEN=1 verin.
        if os.getenv("KEEP_OPEN") == "1":
            print("   -> KEEP_OPEN=1: tarayıcı açık bırakılıyor (kapatmak için Enter)...")
            try:
                input()
            except EOFError:
                time.sleep(120)
        time.sleep(5)
        driver.quit()


def _dump_diagnostics(driver):
    """Hata anında sayfayı incelemek için ekran görüntüsü + kaynak + URL kaydeder."""
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag")
    os.makedirs(outdir, exist_ok=True)
    try:
        print(f"\n--- TANILAMA ---")
        print(f"   URL   : {driver.current_url}")
        print(f"   TITLE : {driver.title}")
        png = os.path.join(outdir, "failure.png")
        driver.save_screenshot(png)
        print(f"   Ekran görüntüsü: {png}")
        html = os.path.join(outdir, "failure.html")
        with open(html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"   Sayfa kaynağı  : {html}")
    except Exception as e:
        print(f"   (tanılama toplanamadı: {type(e).__name__}: {e})")


if __name__ == "__main__":
    main()
