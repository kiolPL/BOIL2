# Solver problemu transportowego

Prosty program do liczenia problemow transportowych. Aplikacja wyznacza plan dostaw
metoda wierzcholka polnocno-zachodniego, pokazuje kolejne kroki na grafach i
pozwala blokowac trasy, ktore nie moga byc uzyte.

Jest tez tryb posrednika. W tym wariancie podaje sie koszt zakupu u dostawcy,
cene sprzedazy u odbiorcy oraz koszt transportu na trasie dostawca -> odbiorca.
Program wybiera plan o najwiekszym zysku i pozwala wymusic pelny popyt wybranego
odbiorcy.

## Co jest w srodku

- backend w Pythonie, bez instalowania dodatkowych paczek,
- edycja dostawcow, odbiorcow, podazy i popytu,
- koszty transportu oraz opcjonalne liczenie przychodu i zysku,
- blokowanie tras w zwyklym problemie transportowym,
- blokowanie tras dostawca-odbiorca w trybie posrednika,
- wymuszenie pelnego popytu wybranego odbiorcy w trybie posrednika,
- automatyczne bilansowanie przez dostawce albo odbiorce fikcyjnego,
- tabela wyniku koncowego oraz graf dla kazdej iteracji.

## Zrzuty ekranu

Widok z wlaczonym zyskiem:

![Widok z wlaczonym zyskiem](screenshots/transport-profit-enabled.png)

Widok po wylaczeniu liczenia zysku:

![Widok bez liczenia zysku](screenshots/transport-profit-disabled.png)

Tryb posrednika:

![Tryb posrednika](screenshots/intermediary-profit.png)

## Uruchomienie

```powershell
python .\backend\server.py --port 8000
```

Jesli Windows nie znajduje polecenia `python`, mozna uzyc launchera:

```powershell
py .\backend\server.py --port 8000
```

Po starcie serwera wejdz w przegladarce na:

```text
http://127.0.0.1:8000
```

## Testy

```powershell
python -m unittest discover -s tests -p "test*.py" -v
```

W srodowisku, w ktorym `python` nie jest w PATH, trzeba podmienic polecenie na
dostepna sciezke do Pythona albo uzyc `py`.
