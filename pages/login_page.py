# -*- coding: utf-8 -*-
"""Giriş (login) sayfası nesnesi - ADIM 2."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage, MANUAL_WAIT


class LoginPage(BasePage):
    # ACCOUNT_LINK, BasePage'ten miras alınır (ortak üst-navigasyon locator'ı).

    # Amazon'un YENİ birleşik giriş ekranında e-posta alanı 'ap_email' değil
    # 'ap_email_login' olabilir; eski akışta 'ap_email'. Hepsini dene.
    EMAIL_FIELDS = [
        (By.ID, "ap_email"),
        (By.ID, "ap_email_login"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.NAME, "email"),
    ]
    CONTINUE_BUTTONS = [
        (By.ID, "continue"),
        (By.ID, "continue-announce"),
        (By.CSS_SELECTOR, "input#continue"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ]
    PASSWORD_FIELDS = [
        (By.ID, "ap_password"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.NAME, "password"),
    ]
    SUBMIT_BUTTONS = [
        (By.ID, "signInSubmit"),
        (By.CSS_SELECTOR, "input#signInSubmit"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ]
    # Giriş sonrası 'Add a mobile number / Keep hackers out' (accountfixup) atlama
    SKIP_FIXUP = [
        (By.ID, "ap-account-fixup-phone-skip-link"),
        (By.XPATH, "//a[normalize-space()='Not now']"),
        (By.XPATH, "//input[@aria-labelledby='ap-account-fixup-phone-skip-link']"),
        (By.LINK_TEXT, "Not now"),
    ]

    def open(self):
        """Üst sağdaki 'Hello, sign in / Account & Lists' linkine tıklar."""
        self.safe_click(self.wait_clickable(*self.ACCOUNT_LINK))
        return self

    def login(self, email, password):
        # E-posta gir → Continue
        email_input = self.find_first_visible(self.EMAIL_FIELDS)
        email_input.clear()
        email_input.send_keys(email)
        if not self.click_first(self.CONTINUE_BUTTONS):
            email_input.send_keys(Keys.RETURN)

        # Parola gir → Sign-In
        pwd = self.find_first_visible(self.PASSWORD_FIELDS)
        pwd.clear()
        pwd.send_keys(password)
        if not self.click_first(self.SUBMIT_BUTTONS):
            pwd.send_keys(Keys.RETURN)

        # 'Add a mobile number' ara sayfası çıkabilir; varsa 'Not now' ile atla.
        for _ in range(3):
            time.sleep(2)
            if self.skip_account_fixup():
                break
            if "accountfixup" not in self.current_url.lower():
                break

        # Giriş başarılı olunca URL artık '/ap/...' (signin, accountfixup, mfa)
        # yolu İÇERMEZ. DİKKAT: giriş sonrası URL 'amazon.com/?ref_=nav_signin'
        # olabilir; bu yüzden düz 'signin' araması yanıltır → '/ap/' kontrol edilir.
        try:
            WebDriverWait(self.driver, MANUAL_WAIT).until(
                lambda d: "/ap/" not in d.current_url.lower()
                and d.find_elements(*self.ACCOUNT_LINK)
            )
        except TimeoutException:
            pass
        self.skip_account_fixup()  # ara sayfa geç çıkarsa bir kez daha dene
        return self

    def skip_account_fixup(self):
        """'Not now' linki varsa tıklar; tıklarsa True."""
        return self.click_first(self.SKIP_FIXUP)

    def assert_logged_in(self):
        """ADIM 2 doğrulaması: hesap alanı artık 'sign in' göstermemeli."""
        greeting = self.wait_visible(*self.ACCOUNT_LINK).text.lower()
        assert "sign in" not in greeting, \
            f"Login başarısız görünüyor, hesap alanı hâlâ: '{greeting}'"
        return greeting
