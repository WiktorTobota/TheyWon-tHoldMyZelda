"""Lokalny test przepływu — bez połączenia z RTV i bez zamówień."""

import unittest

from playwright.sync_api import sync_playwright

from bot import attempt


class BotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def prepare(self, checked=True, retry=True):
        checked_attribute = "checked" if checked else ""
        message = (
            "Z przyczyn technicznych nie byliśmy w stanie zarezerwować wybranego przez "
            "Ciebie terminu dostawy. Prosimy spróbować ponownie za chwilę."
            if retry else "Termin potwierdzony"
        )
        html = f"""
        <meta charset="utf-8">
        <a href="#" onclick="document.querySelector('#dates').hidden=false">USTAL TERMIN</a>
        <div id="dates" hidden>
          <label><input type="radio" name="day" style="display:none" {checked_attribute}><i>5</i></label>
          <button onclick="document.querySelector('#result').hidden=false; window.sent=true">
            <span>ZAMAWIAM Z OBOWIĄZKIEM ZAPŁATY</span>
          </button>
        </div>
        <div id="result" hidden>
          <p>{message}</p>
          <button onclick="document.querySelector('#result').hidden=true; window.closedError=true">OK</button>
        </div>
        """
        self.page.route("https://test.invalid/**", lambda route: route.fulfill(
            body=html, content_type="text/html; charset=utf-8"
        ))

    def test_known_error_is_dismissed(self):
        self.prepare()
        attempt(self.page, "https://test.invalid/order")
        self.assertTrue(self.page.evaluate("window.sent && window.closedError"))

    def test_missing_date_does_not_submit(self):
        self.prepare(checked=False)
        with self.assertRaisesRegex(RuntimeError, "Brak domyślnie"):
            attempt(self.page, "https://test.invalid/order")
        self.assertIsNone(self.page.evaluate("window.sent"))

    def test_other_response_stops_without_clicking_ok(self):
        self.prepare(retry=False)
        with self.assertRaisesRegex(RuntimeError, "Termin mógł zostać ustalony"):
            attempt(self.page, "https://test.invalid/order")
        self.assertTrue(self.page.evaluate("window.sent"))
        self.assertIsNone(self.page.evaluate("window.closedError"))

    def test_return_to_pending_order_allows_retry(self):
        self.prepare(retry=False)
        self.page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                document.querySelector('#dates button').onclick = () => {
                    window.sent = true;
                    document.querySelector('#dates').hidden = true;
                    const message = document.createElement('p');
                    message.textContent = 'Skompletowaliśmy Twoje Zamówienie. Ustal termin dostawy.';
                    document.body.appendChild(message);
                };
            });
        """)
        attempt(self.page, "https://test.invalid/order")
        self.assertTrue(self.page.evaluate("window.sent"))
        self.assertIsNone(self.page.evaluate("window.closedError"))


if __name__ == "__main__":
    unittest.main()
