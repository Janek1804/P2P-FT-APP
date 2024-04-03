1. Czym charakteryzuje się programowanie asynchroniczne?
    - [ ] Czasochłonne zadania takie jak odczyt pliku blokują wątek 
    - [X] Utrudniona w ustaleniu kolejność wykonywania zadań
    - [ ] Wymaga wykorzystania wielu wątków
    - [X] Sprawdza się przy obsłudze operacji I/O

2. W jaki sposób możemy uruchomić funkcję asynchroniczną za pomocą asyncio?
    - [ ] Za pomocą mechanizmu promise
    - [X] Za pomocą funkcji run
    - [X] Za pomocą słowa kluczowego await
    - [ ] Wywołać jak zwykłą funkcję

3. Jaki będzie rezultat działania następującego kodu?
   async def test(a):
       print(a)
   async def main():
       await asyncio.create_task(test(1))
       await asyncio.sleep(1)
       await asyncio.create_task(test(2))
       await asyncio.create_task(test(3))
       await asyncio.sleep(1)
       await asyncio.create_task(test(4))
    
    - [X] 1 2 3 4
    - [ ] 1 3 2 4
    - [ ] 1 4 3 2
    - [ ] 1 2 4 3
    - [ ] Wystąpi błąd
5. W jaki sposób można nawiązać połączenie TCP używając asyncio?
    - [ ] za pomocą start_client
    - [X] za pomocą open_connection
    - [ ] za pomocą fetch
    - [ ] asyncio na to nie pozwala

6. W jaki sposób możemy asynchronicznie odczytać plik?
    - [ ] za pomocą asyncio.aread
    - [X] za pomocą aiofiles.open i metody read
    - [X] za pomocą aiofiles.open i metody readlines
    - [ ] za pomocą obiektu asyncio.StreamReader
