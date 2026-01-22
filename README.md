# SpeedTestCountry
# SpeedTest Country (Speedtest BUTTER)

CLI‑утилита на Python для проверки **скорости скачивания** (Mbps / MB/s) с тестовых серверов в разных странах.  
Есть режим одного региона, режим **`all`** (по очереди прогоняет все регионы) и режим **`custom`** (тест по своему URL).

## Запуск

Требуется Python 3.x и зависимости: `requests`, `rich`.

Из корня проекта:

```bash
python "source/SpeedTest Sergey0066.py"
```

## Режимы

- **Меню**: запуск без параметров (выбор региона/`all`/`custom`).
- **Один регион**:

```bash
python "source/SpeedTest Sergey0066.py" --region ru
```

- **Все регионы (`all`)**: тестирует каждый регион фиксированное время и выводит итоговую таблицу:

```bash
python "source/SpeedTest Sergey0066.py" --region all
```

- **Свой URL (`custom`)**:

```bash
python "source/SpeedTest Sergey0066.py" --region custom --url "https://example.com/file.bin"
```

## Полезные параметры

- **`--threads N`**: количество потоков скачивания (по умолчанию `8`).
- **`--region`**: код региона (или `all/custom`).
- **`--url`**: URL файла для режима `custom`.

## Сборка в EXE с иконкой (Windows)

Установка PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
```

Сборка одного файла `.exe` с иконкой:

```powershell
pyinstaller --onefile --icon "source/icon.ico" "source/SpeedTest Sergey0066.py"
```

Готовый файл появится в `dist\` (по умолчанию).

