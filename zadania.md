## Zadanie 1
Używając modułów asyncio i aiofiles zaimplementuj metodę readAndSend(path:str,dstaddr:str,dstport:int)-> None, 
która asynchronicznie przeczyta i prześle na podany w drugim parametrze adres i port z trzeciego parametru oraz metodę receive(port:int)->str, która zwróci otrzymaną wiadomość.
## Zadanie 2
Napisz funkcję createpieces(n), która asynchronicznie podzieli plik na n równych fragmentów pod względem rozmiaru w pamięci i zapisze je w osobnych plikach nazwanych piece{numer fragmentu}
## Zadanie 3
Używając wcześniej napisanych funkcji napisz program, który wyśle podany plik na adres loopback, odbierze i zapisze w pliku "odebrane", a następnie porównując hashe SHA256 danego pliku i odebranego sprawdzi poprawność przesłanych danych    