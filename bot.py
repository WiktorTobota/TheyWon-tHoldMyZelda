"""Automatyczne ponawianie ustalenia terminu istniejącego zamówienia."""

import argparse
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


ROOT = Path(__file__).resolve().parent
RETRY_MESSAGE = re.compile(
    r"nie\s+byliśmy w stanie zarezerwować wybranego przez\s+Ciebie terminu dostawy",
    re.IGNORECASE,
)


def control(page, name):
    """Obsługa przycisków, linków i starszych kontrolek HTML."""
    pattern = re.compile(r"^\s*" + re.escape(name) + r"\s*$", re.IGNORECASE)
    return (
        page.get_by_role("button", name=pattern)
        .or_(page.get_by_role("link", name=pattern))
        .or_(page.get_by_text(pattern))
        .filter(visible=True)
        .first
    )


def attempt(page, order_url):
    page.goto(order_url, wait_until="domcontentloaded")
    control(page, "USTAL TERMIN").click()
    submit = control(page, "ZAMAWIAM Z OBOWIĄZKIEM ZAPŁATY")
    submit.wait_for(state="visible")

    # Nie wybieramy samodzielnie innego dnia ani płatnego transportu.
    selected_dates = page.locator('input[type="radio"][name="day"]:checked:enabled')
    if selected_dates.count() != 1:
        raise RuntimeError("Brak domyślnie zaznaczonego terminu. Wybierz termin ręcznie.")

    # Po wysłaniu ponawiamy wyłącznie po jednoznacznym błędzie rezerwacji.
    submit.click()
    try:
        page.get_by_text(RETRY_MESSAGE).wait_for(state="visible", timeout=30000)
    except PlaywrightTimeoutError as error:
        pending_message = page.get_by_text(re.compile(
            r"Skompletowaliśmy\s+Twoje\s+Zamówienie\.\s+Ustal\s+termin\s+dostawy\.",
            re.IGNORECASE,
        ))
        if control(page, "USTAL TERMIN").is_visible() and pending_message.is_visible():
            print("Strona wróciła do zamówienia, które nadal wymaga ustalenia terminu.", flush=True)
            return
        raise RuntimeError(
            "Nie wykryto znanego błędu rezerwacji. Termin mógł zostać ustalony; "
            "sprawdź zamówienie ręcznie. Automat zatrzymany."
        ) from error
    control(page, "OK").click()


def save_screenshot(page):
    output = ROOT / "wyniki"
    output.mkdir(exist_ok=True)
    path = output / f"stop-{datetime.now():%Y%m%d-%H%M%S-%f}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"Zrzut ekranu: {path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Adres strony RTV z istniejącym zamówieniem")
    parser.add_argument("--przerwa", type=int, default=60, help="Sekundy po błędzie (domyślnie 60)")
    parser.add_argument("--okno", action="store_true", help="Pozostaw widoczną przeglądarkę")
    parser.add_argument("--przegladarka", choices=["chromium", "firefox"], default="chromium")
    args = parser.parse_args()
    if args.przerwa < 1:
        parser.error("Przerwa musi wynosić co najmniej sekundę.")

    profile = ROOT / (".profil-bota" if args.przegladarka == "chromium" else ".profil-bota-firefox")
    with sync_playwright() as playwright:
        browser_type = getattr(playwright, args.przegladarka)
        context = browser_type.launch_persistent_context(
            str(profile), headless=False, viewport={"width": 1920, "height": 1080}
        )
        try:
            page = context.pages[0]
            page.goto(args.url, wait_until="domcontentloaded")
            print("Zaloguj się i otwórz szczegóły JEDNEGO zamówienia z przyciskiem USTAL TERMIN.")
            input("Wróć do terminala i naciśnij Enter, aby rozpocząć automatyczne zamawianie terminu: ")
            order_url = page.url
            if not args.okno:
                context.close()
                context = browser_type.launch_persistent_context(
                    str(profile), headless=True, viewport={"width": 1920, "height": 1080}
                )
                page = context.pages[0]
            page.set_default_timeout(30000)
            number = 0
            while True:
                number += 1
                print(f"[{datetime.now():%H:%M:%S}] Próba {number}", flush=True)
                attempt(page, order_url)
                print(f"Termin nadal nieustalony. Następna próba za {args.przerwa} s.", flush=True)
                time.sleep(args.przerwa)
        except KeyboardInterrupt:
            print("Zatrzymano przez Ctrl+C.")
        except Exception as error:
            print(f"STOP: {error}", flush=True)
            save_screenshot(page)
        finally:
            context.close()


if __name__ == "__main__":
    main()
