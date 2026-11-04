# Wake the f*ck up, samuraju. Mamy korporację do pokonania.

Gra kupiona. Termin dostępny. Korporacyjny system ma jednak inne plany.

„Prosimy spróbować ponownie za chwilę”.

Ja, tak samo jak mój idol, nie negocjuję.

Zamiast kolejnej rozmowy z konsultantem powstał mały skrypt w Pythonie.
Korporacja poprosiła o ponawianie prób. Potraktowałem to dosłownie.

**Misja: odzyskać gierkę.**

`USTAL TERMIN` → `ZAMAWIAM Z OBOWIĄZKIEM ZAPŁATY` → `OK` → 60 sekund → powtórka.

Python + Playwright. Bez LLM, bez wielkiej architektury. Osobny profil Firefoksa,
ręczne logowanie, potem zminimalizowane okno i automat na warcie.

Korporacja może mi odmówić raz, drugi, nawet setny.

Ja mam ograniczoną cierpliwość. Pętla nie.

**Termin ustalony. Tę bitwę wygrałem.**

## Instalacja (Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Jeśli Chromium zgłosi brak bibliotek systemowych, zainstaluj zależności
zgodnie z komunikatem Playwrighta dla swojej dystrybucji.

## Uruchomienie

```bash
python bot.py 'WKLEJ_ADRES_STRONY_ZAMOWIENIA'
```

1. Zaloguj się w otwartym oknie. Otwórz szczegóły jednego istniejącego
   zamówienia, tak jak na pierwszym zrzucie (przycisk „USTAL TERMIN”).
2. Wróć do terminala i naciśnij Enter. To uruchamia również automatyczne
   kliknięcia „ZAMAWIAM Z OBOWIĄZKIEM ZAPŁATY”.
3. Okno zamknie się, a bot będzie pracował w tle: „USTAL TERMIN” →
   „ZAMAWIAM Z OBOWIĄZKIEM ZAPŁATY” → przy znanym błędzie „OK” →
   60 sekund przerwy → ponowne otwarcie szczegółów zamówienia.

Bot pozostawia domyślnie zaznaczony dzień. Gdy nie ma zaznaczonej opcji,
zatrzymuje się. Nie wyszukuje innego terminu.

Po odpowiedzi innej niż wskazany błąd rezerwacji (także po możliwym sukcesie,
wylogowaniu lub zmianie strony) zatrzymuje się i zapisuje ekran w `wyniki/`.
Ponawia także po powrocie do szczegółów, jeśli jednocześnie widzi przycisk
„USTAL TERMIN” i komunikat „Skompletowaliśmy Twoje Zamówienie. Ustal termin dostawy.”.
Nie rozpoznaje pozytywnego potwierdzenia sukcesu — sprawdź je ręcznie.
Przyciski wyszukuje po napisach, nie po współrzędnych ekranu.

Zatrzymanie: **Ctrl+C**. Podgląd działania: `--okno`.
Inna przerwa: `--przerwa 90`.

Alternatywnie Firefox Playwrighta, z zachowaniem tego samego okna po zalogowaniu:

```bash
python -m playwright install firefox
python bot.py 'WKLEJ_ADRES_STRONY_ZAMOWIENIA' --przegladarka firefox --okno
```

Okno można zminimalizować. Ten tryb nie przełącza przeglądarki na pracę bez okna
po zalogowaniu. Używa osobnego profilu `.profil-bota-firefox/`.

Implementacja powstała na podstawie zrzutów, a kontrolkę wybranego dnia
dopasowano podczas sprawdzania działania na stronie RTV.
Jeśli witryna używa innych napisów, ramek lub niestandardowego wyboru terminu,
selektory w `bot.py` mogą wymagać dopasowania.

*opis na początku przygotowany osobiście, reszta readme i kod, codex