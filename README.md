# ino2ubi

**Версия:** 1.4

Скрипт для конвертации Arduino скетчей (.ino) в пользовательские блоки (.ubi) для программы FLProg. Позволяет автоматически создавать переиспользуемые блоки из Arduino кода с поддержкой входных/выходных параметров, переменных и пользовательских функций.

## Описание

- **Парсинг Arduino скетчей** с автоматическим определением:
  - Глобальных переменных (int, float, bool, String и др.)
  - Пользовательских функций (кроме setup/loop)
  - Директив `#include` и `#define`
  - Объектов классов (например, SoftwareSerial)

- **Настройка ролей переменных:**
  - `variable` — внутренняя переменная блока
  - `input` — входной параметр (отображается слева на блоке)
  - `output` — выходной параметр (отображается справа на блоке)
  - `parameter` — настраиваемый параметр блока

- **Генерация XML** в формате SIXX для FLProg
- **GUI** на PyQt5
- **CLI** для автоматизации

## Использование

### GUI режим

```bash
python arduino_to_flprog_GLOBAL_COMPLETE.py
```

1. Загрузите .ino файл или вставьте код Arduino
2. Нажмите «Парсить код» для анализа
3. Настройте переменные (двойной клик для редактирования):
   - Выберите роль (variable/input/output/parameter)
   - Установите псевдоним (имя в блоке FLProg)
   - Задайте значение по умолчанию
4. Настройте название и описание блока
5. Нажмите «Сгенерировать .ubi блок»
6. Сохраните файл .ubi

### CLI режим

```bash
python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino
python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -o myblock.ubi
python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -n "MyBlock" -d "Описание блока"
```

**Параметры:** `-i` (input), `-o` (output), `-n` (name), `-d` (description)

## Пример Arduino кода

```cpp
// Описание блока (автоматически используется как описание)
int sensorValue = 0;  // in — входной параметр
int outputValue = 0;  // out — выходной параметр
int threshold = 100;  // par — настраиваемый параметр

void setup() {
  Serial.begin(9600);
}

void loop() {
  sensorValue = analogRead(A0);
  if (sensorValue > threshold) {
    outputValue = 1;
  } else {
    outputValue = 0;
  }
}
```

## Примечания

- Комментарии в начале скетча (`//` или `/* */`) автоматически используются как описание блока
- Роли переменных определяются по комментариям: `//in`, `//out`, `//par`
- Функции setup() и loop() автоматически извлекаются в соответствующие секции блока
- Пользовательские функции добавляются в секцию functionCodePart
- Директивы `#include` и `#define` сохраняются в declareCodePart
- Объекты классов (например SoftwareSerial) сохраняются как дополнительные декларации и не отображаются в таблице переменных

## Иконка

Положите файл `icon.ico` в папку со скриптом — он будет использоваться как иконка окна и как иконка exe при сборке через PyInstaller. Формат: .ico (рекомендуется 32×32 и 256×256).

## Требования

- Python 3.10+
- PyQt5 (`pip install PyQt5`)

## Структура проекта

| Файл | Назначение |
|------|------------|
| `arduino_to_flprog_GLOBAL_COMPLETE.py` | Точка входа (GUI/CLI) |
| `constants.py` | Константы, маппинг типов |
| `parser.py` | Парсинг Arduino кода |
| `generator.py` | Генерация SIXX XML для FLProg |
| `gui.py` | Графический интерфейс PyQt5 |
| `README.md` | Документация и справка |
| `CHANGELOG.md` | История изменений |
| `commit_utf8.bat` | Скрипт для коммитов с русским текстом (UTF-8) |

## Сборка EXE

```bash
pyinstaller arduino_to_flprog_GLOBAL_COMPLETE.spec
```

## История изменений (Changelog)

### v1.3
- **Модульная структура:** код разделён на `arduino_to_flprog_GLOBAL_COMPLETE.py` (точка входа), `gui.py`, `generator.py`, `parser.py`, `constants.py`
- **Справка в GUI:** меню «Справка» (F1), окно «О программе»; текст справки загружается из `README.md`
- **Разметка:** вкладки «Переменные» и «Функции» занимают 75% высоты правой панели
- **Иконка:** поддержка `icon.ico` для окна и exe; fallback на стандартную иконку Qt при отсутствии файла
- **Исправление падения:** диалог «Загрузить .ino» использует безопасную начальную папку (никогда system32); при запуске exe cwd может быть system32 — теперь используется домашняя папка пользователя
- **Сборка exe:** spec-файл с иконкой, README.md в bundle, exe `ino2ubi_v1.3.exe`

### v1.2
- Начальная версия с GUI и CLI

### v1.0
- Первая версия конвертера Arduino → FLProg

---

## Коммиты с русским текстом (UTF-8)

Чтобы сообщения коммитов корректно отображались на GitHub:

1. **Рекомендуемый способ:** создайте файл `msg.txt` в UTF-8 с текстом коммита и выполните:
   ```bash
   git add -A
   git commit -F msg.txt
   git push
   ```
   Или используйте скрипт `commit_utf8.bat` (Windows).

2. **Настройка Git** (опционально, один раз):
   ```bash
   git config i18n.commitEncoding utf-8
   git config i18n.logOutputEncoding utf-8
   ```
