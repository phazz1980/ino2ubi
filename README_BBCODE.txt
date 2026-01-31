[center][size=150][b]ino2ubi[/b][/size][/center]

[b]Версия:[/b] 1.3

[url=https://github.com/YOUR_USER/YOUR_REPO/releases/latest]Скачать exe (ArduinoToFLProg.exe)[/url]

Скрипт для конвертации Arduino скетчей (.ino) в пользовательские блоки (.ubi) для программы FLProg. Позволяет автоматически создавать переиспользуемые блоки из Arduino кода с поддержкой входных/выходных параметров, переменных и пользовательских функций.

[size=120][b]Описание[/b][/size]

[list]
[*][b]Парсинг Arduino скетчей[/b] с автоматическим определением:
[list]
[*]Глобальных переменных (int, float, bool, String и др.)
[*]Пользовательских функций (кроме setup/loop)
[*]Директив [code]#include[/code] и [code]#define[/code]
[*]Объектов классов (например, SoftwareSerial)
[/list]
[*][b]Настройка ролей переменных:[/b]
[list]
[*][code]variable[/code] — внутренняя переменная блока
[*][code]input[/code] — входной параметр (отображается слева на блоке)
[*][code]output[/code] — выходной параметр (отображается справа на блоке)
[*][code]parameter[/code] — настраиваемый параметр блока
[/list]
[*][b]Генерация XML[/b] в формате SIXX для FLProg
[*][b]GUI[/b] на PyQt5
[*][b]CLI[/b] для автоматизации
[/list]

[size=120][b]Использование[/b][/size]

[size=110][b]GUI режим[/b][/size]

[code]python arduino_to_flprog_GLOBAL_COMPLETE.py[/code]

[list=1]
[*]Загрузите .ino файл или вставьте код Arduino
[*]Нажмите «Парсить код» для анализа
[*]Настройте переменные (двойной клик для редактирования):
[list]
[*]Выберите роль (variable/input/output/parameter)
[*]Установите псевдоним (имя в блоке FLProg)
[*]Задайте значение по умолчанию
[/list]
[*]Настройте название и описание блока
[*]Нажмите «Сгенерировать .ubi блок»
[*]Сохраните файл .ubi
[/list]

[size=110][b]CLI режим[/b][/size]

[code]python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino
python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -o myblock.ubi
python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -n "MyBlock" -d "Описание блока"[/code]

[b]Параметры:[/b] [code]-i[/code] (input), [code]-o[/code] (output), [code]-n[/code] (name), [code]-d[/code] (description)

[size=120][b]Пример Arduino кода[/b][/size]

[code=cpp]// Описание блока (автоматически используется как описание)
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
}[/code]

[size=120][b]Примечания[/b][/size]

[list]
[*]Комментарии в начале скетча ([code]//[/code] или [code]/* */[/code]) автоматически используются как описание блока
[*]Роли переменных определяются по комментариям: [code]//in[/code], [code]//out[/code], [code]//par[/code]
[*]Функции setup() и loop() автоматически извлекаются в соответствующие секции блока
[*]Пользовательские функции добавляются в секцию functionCodePart
[*]Директивы [code]#include[/code] и [code]#define[/code] сохраняются в declareCodePart
[*]Объекты классов (например SoftwareSerial) сохраняются как дополнительные декларации и не отображаются в таблице переменных
[/list]

[size=120][b]Иконка[/b][/size]

Положите файл [code]icon.ico[/code] в папку со скриптом — он будет использоваться как иконка окна и как иконка exe при сборке через PyInstaller. Формат: .ico (рекомендуется 32×32 и 256×256).

[size=120][b]Требования[/b][/size]

[list]
[*]Python 3.10+
[*]PyQt5 ([code]pip install PyQt5[/code])
[/list]

[size=120][b]Структура проекта[/b][/size]

[code]arduino_to_flprog_GLOBAL_COMPLETE.py — Точка входа (GUI/CLI)
constants.py                 — Константы, маппинг типов
parser.py                    — Парсинг Arduino кода
generator.py                 — Генерация SIXX XML для FLProg
gui.py                       — Графический интерфейс PyQt5
README.md                    — Документация и справка
commit_utf8.bat              — Скрипт для коммитов с русским текстом (UTF-8)[/code]

[size=120][b]История изменений (Changelog)[/b][/size]

[b]v1.3[/b]
[list]
[*]Модульная структура: [code]arduino_to_flprog_GLOBAL_COMPLETE.py[/code], [code]gui.py[/code], [code]generator.py[/code], [code]parser.py[/code], [code]constants.py[/code]
[*]Справка в GUI: меню «Справка» (F1), окно «О программе»; текст из [code]README.md[/code]
[*]Вкладки «Переменные» и «Функции» — 75% высоты правой панели
[*]Иконка: [code]icon.ico[/code] для окна и exe; fallback на иконку Qt
[*]Исправление падения при открытии .ino: безопасная начальная папка (не system32)
[*]Exe: [code]ino2ubi_v1.3.exe[/code]
[/list]

[b]v1.2[/b] — Начальная версия с GUI и CLI
[b]v1.0[/b] — Первая версия конвертера

[size=120][b]Сборка EXE[/b][/size]

[code]pyinstaller arduino_to_flprog_GLOBAL_COMPLETE.spec[/code]

[size=120][b]Коммиты с русским текстом (UTF-8)[/b][/size]

Чтобы сообщения коммитов корректно отображались на GitHub:

[list=1]
[*][b]Рекомендуемый способ:[/b] создайте файл [code]msg.txt[/code] в UTF-8 с текстом коммита и выполните:
[code]git add -A
git commit -F msg.txt
git push[/code]
Или используйте скрипт [code]commit_utf8.bat[/code] (Windows).

[*][b]Настройка Git[/b] (опционально, один раз):
[code]git config i18n.commitEncoding utf-8
git config i18n.logOutputEncoding utf-8[/code]
[/list]
