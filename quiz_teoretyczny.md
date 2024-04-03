1. Czym charakteryzuje się programowanie asynchroniczne?
    - [ ] Czasochłonne zadania takie jak odczyt pliku blokują wątek 
    - [X] Utrudniona w ustaleniu kolejność wykonywania zadań
    - [ ] Wymaga wykorzystania wielu wątków
    - [X] Sprawdza się przy obsłudze operacji I/O

2. W jaki sposób możemy uruchomić funkcję asynchroniczną za pomocą asyncio?
    - [ ] Za pomocą mechanizmu promise
    - [X] Za pomocą metody run
    - [X] Za pomocą słowa kluczowego await
    - [ ] Wywołać jak zwykłą funkcję

3. Jaki będzie rezultat działania następującego kodu?
    async def main():
        await asyncio.create_task(so)
        await asyncio.sleep(1)
        await asyncio.create_task(
    
    - 

4. W jaki sposób można nawiązać połączenie TCP używając asyncio?
    - [ ] za pomocą start_client
    - [X] za pomocą open_connection
    - [ ] za pomocą fetch
    - [ ] asyncio na to nie pozwala

5. W jaki sposób możemy asynchronicznie odczytać plik?
    - [ ] za pomocą asyncio.aread
    - [ ] za pomocą aiofiles.open i metody read
    - [ ] za pomocą aiofiles.open i metody readlines
    - [ ] za pomocą obiektu asyncio.StreamReader
