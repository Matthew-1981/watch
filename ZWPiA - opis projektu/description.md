# Projekt zaliczeniowy — Zaawansowane Wzorce Projektowe i Architektoniczne

## Opis projektu
Celem projektu jest stworzenie prostej aplikacji do pobierania pomiarów z zegarków
w celu mierzenia ich dokładności względem dokładniejszego zegaru kwarcowego. Na podstawie
pomiarów obliczane są statystyki i interpolacja pomiarów. Aplikacja działa na serwerze i 
umożliwia tworzenie i pracę na wielu kontach. Dostęp do serwera zapewnia aplikacja działająca
w wierszu poleceń, w przyszłości powstanie również wersja z interfejsem graficznym.

Projekt składa się z trzech elementów:
- backend — warstwa odpowiedzialna za logikę biznesową, komunikację z bazą danych
oraz odpowiadanie na zapytania HTTP frontend'u. Do implementacji został użyty framework
FastApi.

- frontend — warstwa odpowiedzialna za interakcję z użytkownikiem, zrealizowana jako
aplikacja wiersza poleceń (cmd).

- baza danych — warstwa przechowująca dane aplikacji, zrealizowana przy użyciu SQL.

## Obsługa
Aby utworzyć konto, należy użyć polecenia `$ watches register` i wypełnić dane użytkownika
oraz serwera:
```shell
$ watches register
Enter configuration information...
host: http://127.0.0.1:27712
username: user
password: ?
```

Aby przełączyć użytkownika lub zmienić serwer można użyć `$ watches config`:
```shell
$ watches config
Enter configuration information...
host: http://127.0.0.1:27712
username: another_user
password: ?
```

Wywołanie `$ watches` otwiera interaktywną aplikację:
```shell
watches
Watch Database CMD Client
host: http://127.0.0.1:27712, user: user
Tissot>
```

Z poziomu aplikacji można między innymi zobaczyć pomiary, dodać nowe, zmieniać grupy
(cykle) pomiarów. Aby zobaczyć wszystkie możliwości, można użyć `$ watches help`.

## Instalacja
Rekomendowana jest instalacja w **Docker** za pomocą **docker-compose**.
Wystarczy wejść do folderu projektu uzupełnić zmienne środowiskowe w `.env` wzorem
`.env.example` i użyć komendy `docker-compose up`. W Dockerze powinny się pojawić dwa
kontenery — jeden z backend, drugi z bazą danych.

Aby zainstalować aplikację wiersza poleceń, należy użyć komend:
`pip3 install ./communincation $$ pip3 install ./cmd`.

## Użyte wzorce projektowe

### 1. Model-View-Presenter
Całość projektu przyjmuje strukturę model (baza danych), view (FastApi backend) oraz
presenter (cmd).

### 2. Active Record
Dostęp do tabeli Users oraz Tokens jest implementowany przez klasy zawierające dane wiersza,
metody update, delete, insert, oraz inne metody dostępu do danych.

### 3. Row Data Gateway
Dostęp do tabeli Watch oraz Log jest implementowany przez klasy zawierające dane wiersza
i metody update, oraz delete.

### 4. Server Session State
Po zalogowaniu tworzony jest token, za pomocą którego użytkownik identyfikuje się
serwerowi do chwili wylogowania lub przeterminowania sesji. Token jest przechowywany
w bazie danych, a przeterminowane informacje usuwane w regularnych interwałach czasu
przez specjalny daemon.

### 5. Remote Facade
Wzorzec ten jest używany do uproszczenia interfejsu komunikacji między frontendem a backendem.
Frontend komunikuje się z backendem za pomocą uproszczonych metod, które ukrywają złożoność
operacji backendowych.

### 6. Transaction Script
Wzorzec ten jest używany do implementacji logiki biznesowej w postaci skryptów transakcyjnych,
które wykonują operacje na danych w sposób sekwencyjny.

### 7. Data Transfer Object
Wzorzec ten jest używany do przesyłania danych między warstwami aplikacji. Obiekty DTO
(Data Transfer Object) są używane do przenoszenia danych między frontendem a backendem,
minimalizując liczbę wywołań sieciowych.
