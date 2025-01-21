# Projekt zaliczeniowy - Zaawansowane Wzorce Projektowe i Architektoniczne

## Opis projektu
Projekt składa się z trzech elementów:
- backend — warstwa odpowiedzialna za logikę biznesową, komunikację z bazą danych
oraz odpowiadanie na zapytania HTTP frontend'u. Do implementacji został użyty framework
FastApi.

- frontend — warstwa odpowiedzialna za interakcję z użytkownikiem, zrealizowana jako
aplikacja wiersza poleceń (cmd).

- baza danych — warstwa przechowująca dane aplikacji, zrealizowana przy użyciu SQL.

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

### 4. Table Data Gateway (częściowo)
Operacje związane z szukaniem wierszy i ich dodawaniem są zaimplementowane w klasach
reprezentujących tabele bazy danych. Za modyfikowanie i usuwanie odpowiedzialne są
klasy implementujące wzorzec Row Data Gateway (Watch i Log).

### 5. Server Session State
Po zalogowaniu tworzony jest token, za pomocą którego użytkownik identyfikuje się
serwerowi do chwili wylogowania lub przeterminowania sesji. Token jest przechowywany
w bazie danych, a przeterminowane informacje usuwane w regularnych interwałach czasu
przez specjalny daemon.

### 6. Remote Facade
Wzorzec ten jest używany do uproszczenia interfejsu komunikacji między frontendem a backendem.
Frontend komunikuje się z backendem za pomocą uproszczonych metod, które ukrywają złożoność
operacji backendowych.

### 7. Transaction Script
Wzorzec ten jest używany do implementacji logiki biznesowej w postaci skryptów transakcyjnych,
które wykonują operacje na danych w sposób sekwencyjny.

### 8. Data Transfer Object
Wzorzec ten jest używany do przesyłania danych między warstwami aplikacji. Obiekty DTO
(Data Transfer Object) są używane do przenoszenia danych między frontendem a backendem,
minimalizując liczbę wywołań sieciowych.
