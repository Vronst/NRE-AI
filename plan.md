# Miasto

- startuje z szansa 20% na jednen kontrakt do innego miasta, stolica ma 1-3
- szansa na kontrakt miedzy miastami wynosi 1% chyba ze miasto ma fabryke wyczerpanego surowca w innym miescie, wtedy szansa wynosi 20%
- szansa na fabryke to 40% przy miescie (o ile lokacja pozwala), 'big' miasto bd mialo gwarantowana fabryke i 20% szansy na 2

## Struktura miasta

`python 
json = {
  cities: [
    {
        "name": "Eldorado"
        "size": "big",  
        "factory": ["mine", "20%for other if big"],
        "fee": 100
        "number of connections": "6",
        "commodieties": {
          "metal": {"quantity": 100, "price": 200, "regular price": 150, "regular_quantity": 100},
          "gems": {"quantity": 75, "price": 250, "regular price": 300, "regular_quantity": 100},
          "food": {"quantity": 50, "price": 50, "regular price": 45, "regular_quantity": 100},
          "fuel": {"quantity": 50, "price": 100, "regular price": 80, "regular_quantity": 100},
          "relics": {"quantity": 1, "price": 1250, "regular price": 1300, "regular_quantity": 100},
          "special": null,
         },
        "missions": 2,
        "mission_title": ["Agata mysli nad tym prawda?", "Oby Adam sie nie mylil"],
        "connecitons": [
          "Romania", "Kraina Czapl", ...,
          ],
        "contracts": ["Romania"]
         },
         ]
}
`


# Surowce -> Fabryki 
- metal -> Wysypisko
- krysztaly -> Kopalnia
- jedzenie -> Farma
- benzyna -> Cmentarz
- itemy z kampani -> Null
- relikty przeszlosci -> Pole bitwy

# Surowce -> zmiany
- miasto kupuje -> zasob przy nastepnym refreshu zwieksza sie pomiedzy 25%-50% losowo
- miasto sprzedaje -> zasob przy nastepnym refreshu zmniejsza sie o 10%-50%
- kontrakt -> zasob przy nastepnym refreshu nie moze spasc ponizej standardu + 10%
- cena zmienia sie 5%-10% przy refreshu (plus dodatkowa zmiana od ilosci zasobu)```md

# Mechanika handlu

Ilosc zasobu (tj maksymalna ilosc stuk) zalezec bedzie od wielkosci miasta. Duze miasta beda mialy 5x wiecej surowcow w porownaniu do malych miast.
Kazde miasto zelznie od polozenia bd moglo miec fabryke surowca (moze nie miec zadnej)

Ilosci zasobu bd zalezaly takze od graczy i botow oraz tranzakcji miedzy miejskich. 
Tranzakcje te bd okreslaly jakie miasto handluje z jakim i ktore surowce sa wymieniane.
Na podstawie tych tranzakcji oraz misji pocztowych gracz bd mogl wykonywac malo platne zlecenia z miasta do miasta.
Tranzakcje nie musza byc jawne dla graczy nie wypelniajacych ich (tj. gracz weznie zadanie, to dopiero wtedy wie jaki surowiec bd
transportowany, co daje mu mozliwosc ustalenia iz miasto docelowe napenwno bd mialo przynajmniej standardowa ilosc tego surowca)

## Sprzedaz:
*Niemalze wyczerpane zasoby* - 200\*-300%
*Mala ilosc zasobu* - 150\*-200%
*Standardowa ilosc zasobu* - 90\*-100%
*Duza ilosc zasobow* -  75\*-80%

## Skup:
*Niemalze wyczerpane zasoby* - 80\*-90% (80 jesli miasto posiada fabryke surowca)
*Mala ilosc zasobu* - 60\*-75% ceny 
*Standardowa ilosc zasobow* - 30\*-50% ceny zasobu
*Duza ilosc Zasobu* - 0\*-25% ceny

\* ( jesli miasto posiada fabryke surowca)


# Drzewko decyzyjne AI

Tekst poniżej opisuje drzewko decyzyjne i logikę działania agenta AI w grze.

## Cele AI

1.  **Maksymalizacja Zysku:** Głównym celem AI jest zgromadzenie jak największej ilości pieniędzy.
2.  **Unikanie Bankructwa:** AI musi zarządzać swoimi finansami, aby nie zbankrutować.
3.  **Logiczny Handel:** Decyzje AI opierają się na analizie rynków w poszczególnych miastach w celu znalezienia opłacalnych szlaków handlowych.

## Struktura Tury AI

Każda tura AI składa się z poniższych kroków.

### 1. Faza Analizy

*   **Zbierz informacje:** AI analizuje aktualny stan wszystkich miast (ceny, ilości towarów, fabryki) oraz swój własny stan (gotówka, posiadane towary, obecna lokalizacja).
*   **Oceń obecne miasto:**
    *   **Sprzedaż:** Jeśli AI posiada towary, których cena w obecnym mieście jest wyższa niż cena, po której je zakupiło (lub średnia cena rynkowa), AI je sprzedaje.
    *   **Zakup:** Jeśli w obecnym mieście są dostępne tanie towary (cena niższa od średniej lub regularnej ceny), zwłaszcza te produkowane w lokalnych fabrykach, AI rozważa ich zakup.

### 2. Faza Decyzji o Podróży

*   **Analiza połączeń:** AI sprawdza listę miast, do których może się udać ze swojej obecnej lokalizacji.
*   **Kalkulacja potencjalnego zysku:** Dla każdego dostępnego miasta docelowego, AI szacuje potencjalny zysk z podróży:
    ```
    Potencjalny Zysk = (Cena Sprzedaży w Mieście B - Cena Zakupu w Mieście A) * Ilość Towaru - Opłata za Wjazd do Miasta B
    ```
*   **Wybór celu:** AI wybiera jako cel podróży miasto, które oferuje najwyższy potencjalny zysk. Jeśli żaden szlak handlowy nie jest opłacalny, AI może zdecydować się pozostać w obecnym mieście lub udać się do losowego miasta w poszukiwaniu nowych okazji.

### 3. Faza Akcji

*   **Podróż:** AI przemieszcza się do wybranego miasta i uiszcza opłatę za wjazd.
*   **Transakcje:** AI wykonuje zaplanowane operacje kupna i sprzedaży w nowym mieście.
*   **Aktualizacja danych:** Wszystkie działania AI (zmiana lokalizacji, transakcje) są zapisywane poprzez modyfikację sekcji `after` w pliku JSON.

## Logika Unikania Bankructwa

*   **Kontrola budżetu:** Przed każdą operacją wymagającą wydatków (np. zakup towaru, opłata za wjazd), AI sprawdza, czy posiada wystarczającą ilość gotówki.
*   **Rezerwa finansowa:** AI stara się utrzymywać pewien poziom gotówki jako rezerwę, aby uniknąć sytuacji, w której nie stać go na opłaty.
*   **Tryb awaryjny:** W przypadku niskiego stanu gotówki, priorytetem staje się szybka sprzedaż posiadanych towarów, nawet jeśli zysk będzie minimalny.