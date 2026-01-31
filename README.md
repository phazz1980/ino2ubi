# ino2ubi

**Версия:** 1.3

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

## Сборка EXE

```bash
pyinstaller arduino_to_flprog_GLOBAL_COMPLETE.spec
```
