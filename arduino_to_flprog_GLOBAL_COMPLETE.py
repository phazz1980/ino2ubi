"""
================================================================================
ino2ubi
================================================================================

ОПИСАНИЕ:
---------
Скрипт для конвертации Arduino скетчей (.ino) в пользовательские блоки (.ubi)
для программы FLProg. Позволяет автоматически создавать переиспользуемые
блоки из Arduino кода с поддержкой входных/выходных параметров, переменных
и пользовательских функций.

ВОЗМОЖНОСТИ:
------------
- Парсинг Arduino скетчей с автоматическим определением:
  * Глобальных переменных (int, float, bool, String и др.)
  * Пользовательских функций (кроме setup/loop)
  * Директив #include и #define
  * Объектов классов (например, SoftwareSerial)
  
- Настройка ролей переменных:
  * variable - внутренняя переменная блока
  * input - входной параметр (отображается слева на блоке)
  * output - выходной параметр (отображается справа на блоке)
  * parameter - настраиваемый параметр блока

- Генерация XML файлов в формате SIXX для FLProg
- Графический интерфейс (GUI) на PyQt5
- Командная строка (CLI) для автоматизации

ИСПОЛЬЗОВАНИЕ:
--------------

1. ГРАФИЧЕСКИЙ РЕЖИМ (GUI):
   Запуск без параметров:
   > python arduino_to_flprog_GLOBAL_COMPLETE.py
   
   Шаги:
   - Загрузите .ino файл или вставьте код Arduino
   - Нажмите "Парсить код" для анализа
   - Настройте переменные (двойной клик для редактирования):
     * Выберите роль (variable/input/output/parameter)
     * Установите псевдоним (имя в блоке FLProg)
     * Задайте значение по умолчанию
   - Настройте название и описание блока
   - Нажмите "Сгенерировать .ubi блок"
   - Сохраните файл .ubi

2. КОМАНДНАЯ СТРОКА (CLI):
   Базовое использование:
   > python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino
   
   С указанием выходного файла:
   > python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -o myblock.ubi
   
   С настройкой названия и описания:
   > python arduino_to_flprog_GLOBAL_COMPLETE.py -i sketch.ino -n "MyBlock" -d "Описание блока"
   
   Параметры CLI:
   --input, -i     Путь к Arduino скетчу (.ino)
   --output, -o    Путь для сохранения .ubi (по умолчанию: имя_скетча.ubi)
   --name, -n      Название блока
   --description, -d  Описание блока

ПРИМЕР ARDUINO КОДА:
--------------------
// Описание блока (автоматически используется как описание)
int sensorValue = 0;  // input - входной параметр
int outputValue = 0;  // out - выходной параметр
int threshold = 100;   // par - настраиваемый параметр

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

ПРИМЕЧАНИЯ:
-----------
- Комментарии в начале скетча (// или /* */) автоматически используются
  как описание блока
- Роли переменных определяются по комментариям: //in, //out, //par
- Функции setup() и loop() автоматически извлекаются в соответствующие
  секции блока
- Пользовательские функции добавляются в секцию functionCodePart
- Директивы #include и #define сохраняются в declareCodePart
- Объекты классов (например SoftwareSerial) сохраняются как дополнительные
  декларации и не отображаются в таблице переменных

ИКОНКА:
-------
Положите файл icon.ico в папку со скриптом — он будет использоваться
как иконка окна и как иконка exe при сборке через PyInstaller.
Формат: .ico (рекомендуется 32x32 и 256x256).

ТРЕБОВАНИЯ:
-----------
- Python 3.x
- PyQt5 (pip install PyQt5)

АВТОР:
------
Скрипт для конвертации Arduino кода в блоки FLProg

ВЕРСИЯ:
-------
v1.2

================================================================================
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import re
import uuid
import html
import os
import argparse

# Текст справки для GUI (используется модульный docstring)
GUI_HELP_TEXT = __doc__


class ArduinoToFLProgConverter(QtWidgets.QMainWindow):
    """
    Главный класс приложения для конвертации Arduino кода в блоки FLProg.
    
    Предоставляет графический интерфейс для:
    - Загрузки и редактирования Arduino скетчей
    - Парсинга кода и извлечения переменных, функций, директив
    - Настройки параметров блока (роли переменных, псевдонимы)
    - Генерации XML файлов .ubi в формате SIXX для FLProg
    
    Атрибуты:
        variables (dict): Словарь найденных переменных с их параметрами
        functions (dict): Словарь пользовательских функций
        global_section_raw (str): Исходная глобальная секция кода
        global_includes (list): Список директив #include
        global_defines (dict): Словарь директив #define
        extra_declarations (list): Дополнительные декларации (объекты классов)
        last_save_dir (str): Последняя директория для сохранения файлов
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ino2ubi")
        self.resize(1400, 850)
        # Иконка окна: icon.ico рядом со скриптом или во временной папке exe (PyInstaller)
        self._set_window_icon()
        self.variables = {}
        self.functions = {}
        # Дополнительно храним всё содержимое global_section
        self.global_section_raw = ""
        self.global_includes = []
        self.global_defines = {}
        # Дополнительные декларации (объекты/классы и т.п.), которые не должны попадать в таблицу переменных
        self.extra_declarations = []
        self._safe_home = self._get_safe_home_dir()
        self.last_save_dir = self._safe_home
        self.create_widgets()

    def _get_safe_home_dir(self):
        """Начальная папка для диалогов: никогда не system32 (при запуске exe cwd часто system32)."""
        home = os.path.expanduser("~")
        if not home:
            home = os.environ.get("USERPROFILE", "")
        if not home:
            home = os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")
        home = os.path.abspath(home) if home else ""
        # Не использовать текущую папку, если это system32
        try:
            cwd = os.path.abspath(os.getcwd())
            if "system32" in cwd.lower() or "system64" in cwd.lower():
                pass  # уже подставили home
            elif home and os.path.isdir(home):
                pass
            else:
                home = cwd if os.path.isdir(cwd) else "."
        except Exception:
            home = home or "."
        return home if (home and os.path.isdir(home)) else "."

    def _set_window_icon(self):
        """Устанавливает иконку окна из icon.ico, если файл есть; иначе — стандартная иконка приложения."""
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            # Fallback: иконка приложения Qt (без icon.ico в exe всё равно будет своя иконка окна)
            icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
            if not icon.isNull():
                self.setWindowIcon(icon)

    def create_widgets(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Меню "Справка"
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Справка")
        act_help = QtWidgets.QAction("Справка...", self)
        act_help.setShortcut("F1")
        act_help.triggered.connect(self.show_help)
        help_menu.addAction(act_help)
        act_about = QtWidgets.QAction("О программе", self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        left_layout.addWidget(QtWidgets.QLabel("Arduino Code (вставка: Ctrl+V или правая кнопка мыши -> Вставить):"))

        self.code_input = QtWidgets.QPlainTextEdit()
        self.code_input.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.code_input.customContextMenuRequested.connect(self.show_code_menu)
        left_layout.addWidget(self.code_input)

        code_buttons_layout = QtWidgets.QHBoxLayout()
        btn_load = QtWidgets.QPushButton("Загрузить .ino")
        btn_load.clicked.connect(self.load_arduino_file)
        code_buttons_layout.addWidget(btn_load)

        btn_clear = QtWidgets.QPushButton("Очистить")
        btn_clear.clicked.connect(self.clear_code)
        code_buttons_layout.addWidget(btn_clear)

        btn_parse = QtWidgets.QPushButton("Парсить код")
        btn_parse.clicked.connect(self.parse_code)
        code_buttons_layout.addWidget(btn_parse)

        left_layout.addLayout(code_buttons_layout)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        self.tabs = QtWidgets.QTabWidget()

        var_tab = QtWidgets.QWidget()
        var_layout = QtWidgets.QVBoxLayout(var_tab)
        var_layout.addWidget(QtWidgets.QLabel("Найденные переменные (двойной клик для редактирования):"))

        self.var_tree = QtWidgets.QTreeWidget()
        self.var_tree.setHeaderLabels(["Переменная", "Тип", "Роль", "Псевдоним", "По умолчанию"])
        self.var_tree.setColumnWidth(0, 120)
        self.var_tree.setColumnWidth(1, 100)
        self.var_tree.setColumnWidth(2, 100)
        self.var_tree.setColumnWidth(3, 120)
        self.var_tree.setColumnWidth(4, 100)
        self.var_tree.itemDoubleClicked.connect(self.on_tree_double_click)
        var_layout.addWidget(self.var_tree)

        self.tabs.addTab(var_tab, "Переменные")

        func_tab = QtWidgets.QWidget()
        func_layout = QtWidgets.QVBoxLayout(func_tab)
        func_layout.addWidget(QtWidgets.QLabel("Найденные функции (двойной клик для редактирования):"))

        self.func_tree = QtWidgets.QTreeWidget()
        self.func_tree.setHeaderLabels(["Имя функции", "Возвращает", "Параметры", "Тело функции"])
        self.func_tree.setColumnWidth(0, 120)
        self.func_tree.setColumnWidth(1, 80)
        self.func_tree.setColumnWidth(2, 150)
        self.func_tree.setColumnWidth(3, 300)
        self.func_tree.itemDoubleClicked.connect(self.edit_function)
        func_layout.addWidget(self.func_tree)

        self.tabs.addTab(func_tab, "Функции")

        right_layout.addWidget(self.tabs, 3)

        settings_group = QtWidgets.QGroupBox("Настройки блока")
        settings_layout = QtWidgets.QGridLayout()

        settings_layout.addWidget(QtWidgets.QLabel("Название блока:"), 0, 0)
        self.block_name_entry = QtWidgets.QLineEdit("Custom Block")
        settings_layout.addWidget(self.block_name_entry, 0, 1)

        settings_layout.addWidget(QtWidgets.QLabel("Описание блока:"), 1, 0)
        self.block_description_entry = QtWidgets.QTextEdit()
        self.block_description_entry.setPlainText("Автоматически сгенерированный блок")
        self.block_description_entry.setFixedHeight(80)
        settings_layout.addWidget(self.block_description_entry, 1, 1)

        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group, 1)

        btn_generate = QtWidgets.QPushButton("Сгенерировать .ubi блок")
        btn_generate.clicked.connect(self.generate_block)
        right_layout.addWidget(btn_generate, 0)

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)

    def show_code_menu(self, position):
        menu = QtWidgets.QMenu()
        menu.addAction("Вставить", self.paste_code)
        menu.addAction("Копировать", self.copy_code)
        menu.addAction("Вырезать", self.cut_code)
        menu.addSeparator()
        menu.addAction("Выделить все", self.select_all_code)
        menu.exec_(self.code_input.mapToGlobal(position))

    def paste_code(self):
        clipboard = QtWidgets.QApplication.clipboard()
        self.code_input.insertPlainText(clipboard.text())

    def copy_code(self):
        clipboard = QtWidgets.QApplication.clipboard()
        cursor = self.code_input.textCursor()
        if cursor.hasSelection():
            clipboard.setText(cursor.selectedText())

    def cut_code(self):
        clipboard = QtWidgets.QApplication.clipboard()
        cursor = self.code_input.textCursor()
        if cursor.hasSelection():
            clipboard.setText(cursor.selectedText())
            cursor.removeSelectedText()

    def select_all_code(self):
        self.code_input.selectAll()

    def show_help(self):
        """Открывает диалог со справкой по программе."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Справка — ino2ubi")
        dialog.resize(700, 550)
        layout = QtWidgets.QVBoxLayout(dialog)
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(GUI_HELP_TEXT)
        text.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(text)
        btn_close = QtWidgets.QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec_()

    def show_about(self):
        """Открывает диалог «О программе»."""
        QtWidgets.QMessageBox.about(
            self,
            "О программе",
            "<h3>ino2ubi</h3>"
            "<p>Конвертация Arduino скетчей (.ino) в пользовательские блоки (.ubi) для FLProg.</p>"
            "<p><b>Версия:</b> 1.2</p>"
            "<p><b>Требования:</b> Python 3.x, PyQt5</p>"
            "<p>Справка: меню <b>Справка → Справка...</b> или клавиша <b>F1</b></p>"
        )

    def clear_code(self):
        self.code_input.clear()

    def load_arduino_file(self):
        # Начальная папка — домашняя, не system32 (при запуске exe cwd часто system32)
        start_dir = self.last_save_dir if os.path.isdir(self.last_save_dir) else self._safe_home
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите Arduino файл", start_dir, "Arduino files (*.ino);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.code_input.setPlainText(f.read())
                # Автоматически подставляем имя файла как название блока
                base_name = os.path.splitext(os.path.basename(filename))[0]
                self.block_name_entry.setText(base_name)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", "Не удалось загрузить файл: {}".format(e))

    def extract_function_body(self, code, func_name):
        pattern = r'void\s+{}\s*\(\s*\)\s*\{{'.format(func_name)
        match = re.search(pattern, code)
        if not match:
            return ""
        start_pos = match.end()
        brace_count = 1
        pos = start_pos
        while pos < len(code) and brace_count > 0:
            if code[pos] == '{':
                brace_count += 1
            elif code[pos] == '}':
                brace_count -= 1
            pos += 1
        if brace_count == 0:
            return code[start_pos:pos-1].strip()
        return ""

    def extract_custom_function_body(self, code, start_pos):
        brace_count = 1
        pos = start_pos
        while pos < len(code) and brace_count > 0:
            if code[pos] == '{':
                brace_count += 1
            elif code[pos] == '}':
                brace_count -= 1
            pos += 1
        if brace_count == 0:
            return code[start_pos:pos-1].strip()
        return ""

    def extract_global_section(self, code):
        setup_match = re.search(r'void\s+setup\s*\(', code)
        loop_match = re.search(r'void\s+loop\s*\(', code)
        first_func_pos = len(code)
        if setup_match and setup_match.start() < first_func_pos:
            first_func_pos = setup_match.start()
        if loop_match and loop_match.start() < first_func_pos:
            first_func_pos = loop_match.start()
        return code[:first_func_pos].strip()

    def extract_leading_comment(self, code):
        """Возвращает текст комментария в начале скетча (//... или /* ... */), если он есть."""
        i = 0
        n = len(code)

        # Пропускаем начальные пробелы/переводы строк
        while i < n and code[i].isspace():
            i += 1

        if i >= n:
            return None

        # Многострочный комментарий /* ... */
        if code.startswith("/*", i):
            end = code.find("*/", i + 2)
            if end == -1:
                # Нет закрывающего, берём до конца файла
                comment_body = code[i + 2 :].strip()
            else:
                comment_body = code[i + 2 : end].strip()
            return comment_body or None

        # Последовательность строк //...
        if code.startswith("//", i):
            lines = []
            pos = i
            while pos < n:
                # Конец строки
                line_end = code.find("\n", pos)
                if line_end == -1:
                    line_end = n
                line = code[pos:line_end]
                if line.strip().startswith("//"):
                    # Убираем ведущие // и пробелы
                    clean = re.sub(r'^\s*//\s*', '', line).rstrip()
                    lines.append(clean)
                    pos = line_end + 1
                else:
                    break
            comment_body = "\n".join(lines).strip()
            return comment_body or None

        return None

    def parse_function_params(self, params_str):
        if not params_str or params_str.strip() == '':
            return []
        params = []
        param_list = params_str.split(',')
        for param in param_list:
            param = param.strip()
            if not param:
                continue
            parts = param.split()
            if len(parts) >= 2:
                param_type = parts[0]
                param_name = parts[1]
                params.append({'type': param_type, 'name': param_name})
        return params

    def parse_functions(self, code):
        """ИСПРАВЛЕНО: Парсит все пользовательские функции (не setup и не loop)"""
        func_pattern = r'(void|int|long|bool|boolean|float|double|byte|char|String|uint8_t|int16_t|uint16_t|int32_t|uint32_t)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{'

        matches = list(re.finditer(func_pattern, code))

        for match in matches:
            func_name = match.group(2)

            if func_name in ['setup', 'loop']:
                continue

            return_type = match.group(1).strip()
            params_str = match.group(3).strip()

            body_start = match.end()
            func_body = self.extract_custom_function_body(code, body_start)

            parsed_params = self.parse_function_params(params_str)

            func_pos = match.start()
            setup_match = re.search(r'void\s+setup\s*\(', code)
            loop_match = re.search(r'void\s+loop\s*\(', code)

            if setup_match and func_pos < setup_match.start():
                location = "до setup/loop"
            elif loop_match and func_pos < loop_match.start():
                location = "до setup/loop"
            else:
                location = "после loop"

            self.functions[func_name] = {
                'return_type': return_type,
                'params': params_str,
                'parsed_params': parsed_params,
                'body': func_body,
                'location': location
            }

    def parse_code(self):
        """
        Парсит Arduino код и извлекает все необходимые элементы.
        
        Выполняет следующие действия:
        1. Извлекает комментарий в начале скетча (используется как описание)
        2. Находит все пользовательские функции (кроме setup/loop)
        3. Извлекает глобальную секцию (до setup/loop)
        4. Парсит директивы #include и #define
        5. Находит глобальные переменные и определяет их роли по комментариям
        6. Сохраняет объекты классов как дополнительные декларации
        7. Отображает результаты в таблицах переменных и функций
        
        Роли переменных определяются по комментариям в строке:
        - //in или //input -> input (входной параметр)
        - //out или //output -> output (выходной параметр)
        - //par или //parameter -> parameter (настраиваемый параметр)
        - без комментария -> variable (внутренняя переменная)
        
        Показывает информационное сообщение с количеством найденных элементов.
        """
        code = self.code_input.toPlainText()
        self.var_tree.clear()
        self.variables = {}
        self.func_tree.clear()
        self.functions = {}
        # Сбрасываем данные по глобальной секции
        self.global_section_raw = ""
        self.global_includes = []
        self.global_defines = {}
        self.extra_declarations = []

        # Если в начале скетча есть комментарий — используем его как описание блока
        leading_comment = self.extract_leading_comment(code)
        if leading_comment:
            self.block_description_entry.setPlainText(leading_comment)

        self.parse_functions(code)

        for func_name, func_info in self.functions.items():
            params_display = func_info['params'] if func_info['params'] else "(нет)"
            body_preview = func_info['body'][:50] + "..." if len(func_info['body']) > 50 else func_info['body']
            item = QtWidgets.QTreeWidgetItem([func_name, func_info['return_type'], params_display, body_preview])
            self.func_tree.addTopLevelItem(item)

        global_section = self.extract_global_section(code)
        # Сохраняем исходную глобальную секцию
        self.global_section_raw = global_section

        # Убираем из неё функции, определённые до setup/loop
        for func_name, func_info in self.functions.items():
            if func_info['location'] == "до setup/loop":
                func_pattern = r'(void|int|long|bool|boolean|float|double|byte|char|String)\s+{}\s*\([^)]*\)\s*\{{[^}}]*\}}'.format(func_name)
                global_section = re.sub(func_pattern, '', global_section, flags=re.DOTALL)

        # Парсим директивы #include и #define из оставшейся global_section
        include_pattern = r'^\s*#include[^\n]*$'
        self.global_includes = re.findall(include_pattern, global_section, re.MULTILINE)

        define_pattern = r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$'
        self.global_defines = {
            name: value.strip()
            for (name, value) in re.findall(define_pattern, global_section, re.MULTILINE)
        }

        # Парсим глобальные переменные (любые типы, включая классы, например SoftwareSerial)
        var_pattern = r'\b(?:const\s+)?([A-Za-z_][A-Za-z0-9_:<>]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*([^;]+))?;'
        matches = re.finditer(var_pattern, global_section)

        # Примитивные типы, которые должны отображаться в таблице переменных
        primitive_types = {
            'int', 'long', 'unsigned long', 'bool', 'boolean', 'float', 'double',
            'byte', 'char', 'String', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t'
        }

        for match in matches:
            full_decl = match.group(0).strip()
            var_type = match.group(1).strip()
            var_name = match.group(2)
            var_value = match.group(3).strip() if match.group(3) else None

            # Определяем роль по комментариям в строке: //in, //out, //par
            # Ищем исходную строку global_section, где находится объявление
            line_start = global_section.rfind('\n', 0, match.start()) + 1
            line_end = global_section.find('\n', match.start())
            if line_end == -1:
                line_end = len(global_section)
            line_text = global_section[line_start:line_end]

            role = 'variable'
            if re.search(r'//\s*in\b', line_text):
                role = 'input'
            elif re.search(r'//\s*out\b', line_text):
                role = 'output'
            elif re.search(r'//\s*par\b', line_text):
                role = 'parameter'

            if var_type in primitive_types:
                # Это "обычная" переменная – показываем в таблице и используем как variable/input/output/parameter
                self.variables[var_name] = {
                    'type': var_type,
                    'default': var_value,
                    'role': role,
                    'alias': var_name
                }

                default_display = var_value if var_value else ""
                item = QtWidgets.QTreeWidgetItem([var_name, var_type, role, var_name, default_display])
                self.var_tree.addTopLevelItem(item)
            else:
                # Это объект/класс (например SoftwareSerial) – сохраняем как дополнительную декларацию,
                # но НЕ показываем в таблице переменных
                self.extra_declarations.append(full_decl)

        QtWidgets.QMessageBox.information(
            self,
            "Парсинг",
            "Найдено глобальных переменных: {}\nНайдено функций: {}\nНайдено #include: {}\nНайдено #define: {}".format(
                len(self.variables),
                len(self.functions),
                len(self.global_includes),
                len(self.global_defines),
            ),
        )

    def edit_function(self, item, column):
        func_name = item.text(0)
        func_info = self.functions[func_name]

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Редактировать функцию: {}".format(func_name))
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Имя функции: {}".format(func_name)))
        layout.addWidget(QtWidgets.QLabel("Возвращает: {}".format(func_info['return_type'])))
        layout.addWidget(QtWidgets.QLabel("Параметры: {}".format(func_info['params'])))
        layout.addWidget(QtWidgets.QLabel("Тело функции:"))

        body_text = QtWidgets.QPlainTextEdit()
        body_text.setPlainText(func_info['body'])
        layout.addWidget(body_text)

        def save_function():
            new_body = body_text.toPlainText().strip()
            self.functions[func_name]['body'] = new_body
            body_preview = new_body[:50] + "..." if len(new_body) > 50 else new_body
            item.setText(3, body_preview)
            dialog.accept()

        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.clicked.connect(save_function)
        layout.addWidget(btn_save)

        dialog.setLayout(layout)
        dialog.exec_()

    def on_tree_double_click(self, item, column):
        """ИСПРАВЛЕНО: Открывает полноценный диалог редактирования переменной"""
        var_name = item.text(0)

        if var_name not in self.variables:
            return

        var_info = self.variables[var_name]

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Редактировать переменную: {}".format(var_name))
        dialog.resize(500, 400)

        layout = QtWidgets.QVBoxLayout()

        info_group = QtWidgets.QGroupBox("Информация")
        info_layout = QtWidgets.QFormLayout()

        name_label = QtWidgets.QLabel(var_name)
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Имя переменной:", name_label)

        type_label = QtWidgets.QLabel(var_info['type'])
        type_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Тип данных:", type_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        settings_group = QtWidgets.QGroupBox("Настройки")
        settings_layout = QtWidgets.QFormLayout()

        role_label = QtWidgets.QLabel("Роль в блоке:")
        role_combo = QtWidgets.QComboBox()
        role_combo.addItems(["variable", "input", "output", "parameter"])
        role_combo.setCurrentText(var_info['role'])

        role_combo.setToolTip(
            "variable - внутренняя переменная блока\n"
            "input - входной параметр (получает данные извне)\n"
            "output - выходной параметр (передаёт данные наружу)\n"
            "parameter - настраиваемый параметр блока"
        )
        settings_layout.addRow(role_label, role_combo)

        alias_label = QtWidgets.QLabel("Псевдоним:")
        alias_edit = QtWidgets.QLineEdit(var_info['alias'])
        alias_edit.setPlaceholderText("Введите псевдоним переменной")
        alias_edit.setToolTip("Имя переменной, которое будет использоваться в блоке FLProg")
        settings_layout.addRow(alias_label, alias_edit)

        default_label = QtWidgets.QLabel("Значение по умолчанию:")
        default_edit = QtWidgets.QLineEdit(var_info.get('default', '') or '')
        default_edit.setPlaceholderText("Введите значение по умолчанию")
        default_edit.setToolTip("Начальное значение переменной (для parameter и variable)")
        settings_layout.addRow(default_label, default_edit)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        description_group = QtWidgets.QGroupBox("Описание роли")
        description_layout = QtWidgets.QVBoxLayout()
        description_text = QtWidgets.QTextEdit()
        description_text.setReadOnly(True)
        description_text.setMaximumHeight(100)

        role_descriptions = {
            "variable": "Внутренняя переменная блока.\n"
                        "Используется для хранения промежуточных данных внутри блока.\n"
                        "Не видна извне и не настраивается пользователем.",

            "input": "Входной параметр блока.\n"
                     "Получает значение от других блоков через соединения.\n"
                     "Отображается слева на блоке в виде входного пина.",

            "output": "Выходной параметр блока.\n"
                      "Передаёт вычисленное значение другим блокам.\n"
                      "Отображается справа на блоке в виде выходного пина.",

            "parameter": "Настраиваемый параметр блока.\n"
                         "Пользователь может изменить его значение в свойствах блока.\n"
                         "Имеет значение по умолчанию, которое можно переопределить."
        }

        def update_description():
            current_role = role_combo.currentText()
            description_text.setText(role_descriptions.get(current_role, ""))

        role_combo.currentTextChanged.connect(update_description)
        update_description()

        description_layout.addWidget(description_text)
        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        buttons_layout = QtWidgets.QHBoxLayout()

        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        btn_cancel = QtWidgets.QPushButton("Отмена")
        btn_cancel.setStyleSheet("padding: 5px 15px;")

        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

        def save_changes():
            new_role = role_combo.currentText()
            new_alias = alias_edit.text().strip()
            new_default = default_edit.text().strip()

            if not new_alias:
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Ошибка",
                    "Псевдоним не может быть пустым!"
                )
                return

            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_alias):
                QtWidgets.QMessageBox.warning(
                    dialog,
                    "Ошибка",
                    "Псевдоним должен начинаться с буквы или подчёркивания\n"
                    "и содержать только буквы, цифры и подчёркивания!"
                )
                return

            self.variables[var_name]['role'] = new_role
            self.variables[var_name]['alias'] = new_alias
            self.variables[var_name]['default'] = new_default if new_default else None

            item.setText(2, new_role)
            item.setText(3, new_alias)
            item.setText(4, new_default)

            dialog.accept()

        def cancel_changes():
            dialog.reject()

        btn_save.clicked.connect(save_changes)
        btn_cancel.clicked.connect(cancel_changes)

        dialog.setLayout(layout)
        dialog.exec_()

    def get_type_class_name(self, var_type):
        """ИСПРАВЛЕНО: Добавлены String и uint типы"""
        type_mapping = {
            'int': 'IntegerDataType',
            'long': 'LongDataType',
            'unsigned long': 'LongDataType',
            'bool': 'BooleanDataType',
            'boolean': 'BooleanDataType',
            'float': 'FloatDataType',
            'double': 'FloatDataType',
            'byte': 'ByteDataType',
            'char': 'CharDataType',
            'String': 'StringDataType',
            'uint8_t': 'ByteDataType',
            'int16_t': 'IntegerDataType',
            'uint16_t': 'IntegerDataType',
            'int32_t': 'LongDataType',
            'uint32_t': 'LongDataType'
        }
        return type_mapping.get(var_type, 'IntegerDataType')

    def create_sixx_data_type(self, var_type, type_id, instance_coll_id):
        """Создаёт SIXX тип данных с instanceCollection"""
        type_class = self.get_type_class_name(var_type)
        instance_id = type_id + 1

        xml = '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="type" sixx.type="{} class" sixx.env="Arduino" >\n'.format(type_id, type_class)
        xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="instanceCollection" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(instance_coll_id)
        xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="{}" sixx.env="Arduino" >\n'.format(instance_id, type_class)
        xml += '\t\t\t\t\t\t</sixx.object>\n'
        xml += '\t\t\t\t\t</sixx.object>\n'
        xml += '\t\t\t\t</sixx.object>\n'

        return xml

    def create_ubi_xml_sixx(self, setup_code, loop_code):
        """Создаёт правильный SIXX XML для FLProg"""
        block_name = self.block_name_entry.text()
        block_description = self.block_description_entry.toPlainText().strip() or "Автоматически сгенерированный блок"
        loop_code_encoded = html.escape(loop_code)
        setup_code_encoded = html.escape(setup_code)

        current_id = [0]

        def next_id():
            current_id[0] += 1
            return current_id[0]

        root_id = next_id()
        code_block_id = next_id()
        main_uuid_id = next_id()
        main_uuid = str(uuid.uuid4())
        blocks_coll_id = next_id()
        label_id = next_id()
        inputs_coll_id = next_id()

        instance_coll_id = 15
        comment_str_id = 18

        inputs_xml = ""
        inputs_list = [(var_name, var_info) for var_name, var_info in self.variables.items() if var_info['role'] == 'input']

        id_base = 119328430
        for idx, (var_name, var_info) in enumerate(inputs_list):
            adaptor_id = next_id()
            obj_id = next_id()
            id_source_id = next_id()
            type_id = next_id()
            name_id = next_id()
            uuid_obj_id = next_id()
            input_uuid = str(uuid.uuid4())

            inputs_xml += '\t\t\t<sixx.object sixx.id="{}" sixx.type="InputsOutputsAdaptorForUserBlock" sixx.env="Arduino" >\n'.format(adaptor_id)
            inputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="object" sixx.type="UniversalBlockInputOutput" sixx.env="Arduino" >\n'.format(obj_id)
            inputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="SmallInteger" sixx.env="Core" >{}</sixx.object>\n'.format(id_source_id, id_base + idx * 1000)
            inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="block" sixx.idref="{}" />\n'.format(code_block_id)

            inputs_xml += self.create_sixx_data_type(var_info['type'], type_id, instance_coll_id)

            inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isInput" sixx.type="True" sixx.env="Core" />\n'
            inputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(name_id, var_info["alias"])
            inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isNot" sixx.type="False" sixx.env="Core" />\n'
            inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="nameCash" sixx.idref="{}" />\n'.format(name_id)
            inputs_xml += '\t\t\t\t</sixx.object>\n'
            inputs_xml += '\t\t\t\t<sixx.object sixx.name="comment" sixx.idref="{}" />\n'.format(comment_str_id)
            inputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(uuid_obj_id, input_uuid)
            inputs_xml += '\t\t\t</sixx.object>\n'

        outputs_coll_id = next_id()
        outputs_xml = ""
        outputs_list = [(var_name, var_info) for var_name, var_info in self.variables.items() if var_info['role'] == 'output']

        id_base = 153438280
        for idx, (var_name, var_info) in enumerate(outputs_list):
            adaptor_id = next_id()
            obj_id = next_id()
            id_source_id = next_id()
            type_id = next_id()
            name_id = next_id()
            uuid_obj_id = next_id()
            output_uuid = str(uuid.uuid4())

            outputs_xml += '\t\t\t<sixx.object sixx.id="{}" sixx.type="InputsOutputsAdaptorForUserBlock" sixx.env="Arduino" >\n'.format(adaptor_id)
            outputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="object" sixx.type="UniversalBlockInputOutput" sixx.env="Arduino" >\n'.format(obj_id)
            outputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="SmallInteger" sixx.env="Core" >{}</sixx.object>\n'.format(id_source_id, id_base + idx * 1000)
            outputs_xml += '\t\t\t\t\t<sixx.object sixx.name="block" sixx.idref="{}" />\n'.format(code_block_id)

            outputs_xml += self.create_sixx_data_type(var_info['type'], type_id, instance_coll_id)

            outputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isInput" sixx.type="False" sixx.env="Core" />\n'
            outputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(name_id, var_info["alias"])
            outputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isNot" sixx.type="False" sixx.env="Core" />\n'
            outputs_xml += '\t\t\t\t\t<sixx.object sixx.name="nameCash" sixx.idref="{}" />\n'.format(name_id)
            outputs_xml += '\t\t\t\t</sixx.object>\n'
            outputs_xml += '\t\t\t\t<sixx.object sixx.name="comment" sixx.idref="{}" />\n'.format(comment_str_id)
            outputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(uuid_obj_id, output_uuid)
            outputs_xml += '\t\t\t</sixx.object>\n'

        vars_coll_id = next_id()
        name_str_id = next_id()
        info_id = next_id()
        info_str_id = next_id()
        runs_id = next_id()
        runs_arr_id = next_id()
        runs_val_id = next_id()
        values_arr_id = next_id()

        params_coll_id = next_id()
        params_xml = ""
        params_list = [(var_name, var_info) for var_name, var_info in self.variables.items() if var_info['role'] == 'parameter']

        for var_name, var_info in params_list:
            adaptor_id = next_id()
            param_id = next_id()
            param_name_id = next_id()
            param_type_id = next_id()
            default_val_id = next_id()
            comment_id = next_id()
            uuid_param_id = next_id()
            uuid_adapt_id = next_id()
            param_uuid = str(uuid.uuid4())
            adapt_uuid = str(uuid.uuid4())

            default_val = var_info.get('default', '0') or '0'

            params_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.type="InputsOutputsAdaptorForUserBlock" sixx.env="Arduino" >\n'.format(adaptor_id)
            params_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="object" sixx.type="UserBlockParametr" sixx.env="Arduino" >\n'.format(param_id)
            params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(param_name_id, var_info["alias"])

            params_xml += self.create_sixx_data_type(var_info['type'], param_type_id, instance_coll_id)

            params_xml += '\t\t\t\t\t\t<sixx.object sixx.name="hasDefaultValue" sixx.type="True" sixx.env="Core" />\n'

            try:
                if '.' in default_val:
                    params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="numberDefaultValue" sixx.type="Float" sixx.env="Core" >{}</sixx.object>\n'.format(default_val_id, default_val)
                else:
                    params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="numberDefaultValue" sixx.type="SmallInteger" sixx.env="Core" >{}</sixx.object>\n'.format(default_val_id, default_val)
            except:
                params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="numberDefaultValue" sixx.type="SmallInteger" sixx.env="Core" >0</sixx.object>\n'.format(default_val_id)

            params_xml += '\t\t\t\t\t\t<sixx.object sixx.name="hasUpRange" sixx.type="False" sixx.env="Core" />\n'
            params_xml += '\t\t\t\t\t\t<sixx.object sixx.name="hasDownRange" sixx.type="False" sixx.env="Core" />\n'
            params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="comment" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(comment_id)
            params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(uuid_param_id, param_uuid)
            params_xml += '\t\t\t\t\t</sixx.object>\n'
            params_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(uuid_adapt_id, adapt_uuid)
            params_xml += '\t\t\t\t</sixx.object>\n'

        loop_part_id = next_id()
        loop_code_id = next_id()

        setup_part_id = next_id()
        setup_code_id = next_id()

        declare_part_id = next_id()
        declare_coll_id = next_id()
        declare_xml = ""
        vars_list = [(var_name, var_info) for var_name, var_info in self.variables.items() if var_info['role'] == 'variable']

        # Сначала добавляем директивы #include и #define как сырые строки в declareCodePart
        for inc in self.global_includes:
            decl_id = next_id()
            decl_name_id = next_id()
            decl_last_id = next_id()
            decl_first_id = next_id()

            line = inc.strip()
            declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_name_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_last_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, html.escape(line))
            declare_xml += '\t\t\t\t\t</sixx.object>\n'

        for name, value in self.global_defines.items():
            decl_id = next_id()
            decl_name_id = next_id()
            decl_last_id = next_id()
            decl_first_id = next_id()

            line = "#define {} {}".format(name, value)
            declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_name_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_last_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, html.escape(line))
            declare_xml += '\t\t\t\t\t</sixx.object>\n'

        # Затем добавляем дополнительные декларации объектов/классов (например SoftwareSerial newSerial = ...)
        for line in self.extra_declarations:
            decl_id = next_id()
            decl_name_id = next_id()
            decl_last_id = next_id()
            decl_first_id = next_id()

            declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_name_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" ></sixx.object>\n'.format(decl_last_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, html.escape(line))
            declare_xml += '\t\t\t\t\t</sixx.object>\n'

        # Затем добавляем стандартные объявления переменных
        for var_name, var_info in vars_list:
            decl_id = next_id()
            decl_name_id = next_id()
            decl_last_id = next_id()
            decl_first_id = next_id()

            declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_name_id, var_info["alias"])
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" >;</sixx.object>\n'.format(decl_last_id)
            declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, var_info["type"])
            declare_xml += '\t\t\t\t\t</sixx.object>\n'

        func_part_id = next_id()
        func_coll_id = next_id()
        functions_xml = ""

        for func_name, func_info in self.functions.items():
            func_id = next_id()
            func_body_id = next_id()
            func_proto_id = next_id()
            func_ret_type_id = next_id()
            func_name_id = next_id()
            func_params_coll_id = next_id()

            body_encoded = html.escape(func_info['body'])

            functions_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockFunction" sixx.env="Arduino" >\n'.format(func_id)
            functions_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="functionBody" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_body_id, body_encoded)
            functions_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="parsesFunctionName" sixx.type="CodeUserBlockFunctionName" sixx.env="Arduino" >\n'.format(func_proto_id)
            functions_xml += '\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="declare" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_ret_type_id, func_info["return_type"])
            functions_xml += '\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_name_id, func_name)
            functions_xml += '\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="parametrs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(func_params_coll_id)

            for param in func_info.get('parsed_params', []):
                fparam_id = next_id()
                fparam_type_id = next_id()
                fparam_name_id = next_id()

                functions_xml += '\t\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockFunctionParametr" sixx.env="Arduino" >\n'.format(fparam_id)
                functions_xml += '\t\t\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="declare" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(fparam_type_id, param["type"])
                functions_xml += '\t\t\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(fparam_name_id, param["name"])
                functions_xml += '\t\t\t\t\t\t\t\t</sixx.object>\n'

            functions_xml += '\t\t\t\t\t\t\t</sixx.object>\n'
            functions_xml += '\t\t\t\t\t\t</sixx.object>\n'
            functions_xml += '\t\t\t\t\t</sixx.object>\n'

        libs_id = next_id()

        xml_header = '<?xml version="1.0" encoding="utf-16"?>\n'
        xml_header += '<sixx.object sixx.id="{}" sixx.type="BlocksLibraryElement" sixx.env="Arduino" >\n'.format(root_id)
        xml_header += '\t<sixx.object sixx.id="{}" sixx.name="typeClass" sixx.type="CodeUserBlock" sixx.env="Arduino" >\n'.format(code_block_id)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(main_uuid_id, main_uuid)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="blocks" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(blocks_coll_id)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="label" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(label_id, block_name)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="inputs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(inputs_coll_id)
        xml_header += inputs_xml
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="outputs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(outputs_coll_id)
        xml_header += outputs_xml
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="variables" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(vars_coll_id)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(name_str_id, block_name)
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="info" sixx.type="Text" sixx.env="Core" >\n'.format(info_id)
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="string" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(info_str_id, html.escape(block_description))
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="runs" sixx.type="RunArray" sixx.env="Core" >\n'.format(runs_id)
        xml_header += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="runs" sixx.type="Array" sixx.env="Core" >\n'.format(runs_arr_id)
        xml_header += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="SmallInteger" sixx.env="Core" >50</sixx.object>\n'.format(runs_val_id)
        xml_header += '\t\t\t\t</sixx.object>\n'
        xml_header += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="values" sixx.type="Array" sixx.env="Core" >\n'.format(values_arr_id)
        xml_header += '\t\t\t\t\t<sixx.object sixx.type="UndefinedObject" sixx.env="Core" />\n'
        xml_header += '\t\t\t\t</sixx.object>\n'
        xml_header += '\t\t\t</sixx.object>\n'
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="parametrs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(params_coll_id)
        xml_header += params_xml
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="loopCodePart" sixx.type="CodeUserBlockLoopCodePart" sixx.env="Arduino" >\n'.format(loop_part_id)
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="code" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(loop_code_id, loop_code_encoded)
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="setupCodePart" sixx.type="CodeUserBlockSetupCodePart" sixx.env="Arduino" >\n'.format(setup_part_id)
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="code" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(setup_code_id, setup_code_encoded)
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="declareCodePart" sixx.type="CodeUserBlockDeclareCodePart" sixx.env="Arduino" >\n'.format(declare_part_id)
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="code" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(declare_coll_id)
        xml_header += declare_xml
        xml_header += '\t\t\t</sixx.object>\n'
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="functionCodePart" sixx.type="CodeUserBlockFunctuinCodePart" sixx.env="Arduino" >\n'.format(func_part_id)
        xml_header += '\t\t\t<sixx.object sixx.id="{}" sixx.name="code" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(func_coll_id)
        xml_header += functions_xml
        xml_header += '\t\t\t</sixx.object>\n'
        xml_header += '\t\t</sixx.object>\n'
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="userLibraries" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(libs_id)
        xml_header += '\t\t<sixx.object sixx.name="notCanManyUse" sixx.type="False" sixx.env="Core" />\n'
        xml_header += '\t</sixx.object>\n'
        xml_header += '</sixx.object>\n'

        return xml_header

    def generate_block(self):
        """
        Генерирует .ubi файл из отпарсенного кода.
        
        Процесс генерации:
        1. Извлекает код из функций setup() и loop()
        2. Заменяет имена переменных на их псевдонимы в коде
        3. Создает XML структуру в формате SIXX с:
           - Входными параметрами (inputs)
           - Выходными параметрами (outputs)
           - Настраиваемыми параметрами (parameters)
           - Внутренними переменными (variables)
           - Директивами #include и #define
           - Дополнительными декларациями объектов
           - Пользовательскими функциями
           - Кодом setup и loop
        4. Сохраняет файл с запоминанием последней директории
        
        Показывает диалог сохранения файла и информационное сообщение
        об успешном сохранении или ошибке.
        """
        try:
            code = self.code_input.toPlainText()
            setup_code = self.extract_function_body(code, 'setup')
            loop_code = self.extract_function_body(code, 'loop')

            for var_name, var_info in self.variables.items():
                if var_info['alias'] != var_name:
                    loop_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], loop_code)
                    setup_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], setup_code)

            xml_content = self.create_ubi_xml_sixx(setup_code, loop_code)

            # Запоминаем последнюю директорию (никогда не system32)
            if (self.last_save_dir and os.path.exists(self.last_save_dir) and
                    "system32" not in os.path.normpath(self.last_save_dir).lower()):
                save_dir = self.last_save_dir
            else:
                # Первый запуск - используем Рабочий стол
                try:
                    save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    if not os.path.exists(save_dir):
                        save_dir = os.path.join(os.path.expanduser("~"), "Рабочий стол")
                    if not os.path.exists(save_dir):
                        save_dir = os.path.expanduser("~")
                except:
                    save_dir = os.path.expanduser("~")

            block_name = self.block_name_entry.text()
            default_filename = os.path.join(save_dir, "{}.ubi".format(block_name))

            filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Сохранить блок",
                default_filename,
                "FLProg Block (*.ubi);;All files (*.*)"
            )

            if filename:
                if not filename.endswith('.ubi'):
                    filename += '.ubi'

                with open(filename, 'w', encoding='utf-16') as f:
                    f.write(xml_content)

                # Сохраняем директорию для следующего раза (не system32)
                new_dir = os.path.dirname(filename)
                if new_dir and "system32" not in new_dir.lower():
                    self.last_save_dir = new_dir

                QtWidgets.QMessageBox.information(
                    self,
                    "Успех",
                    "Блок успешно сохранен в формате SIXX:\n{}".format(filename)
                )

        except Exception as e:
            import traceback
            error_msg = "Ошибка при сохранении:\n{}\n\nПодробности:\n{}".format(str(e), traceback.format_exc())
            QtWidgets.QMessageBox.critical(self, "Ошибка", error_msg)


    def generate_block_to_file(self, filename):
        """CLI-версия генерации блока: сохраняет .ubi без диалогов и окон"""
        try:
            code = self.code_input.toPlainText()
            setup_code = self.extract_function_body(code, 'setup')
            loop_code = self.extract_function_body(code, 'loop')

            for var_name, var_info in self.variables.items():
                if var_info['alias'] != var_name:
                    loop_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], loop_code)
                    setup_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], setup_code)

            xml_content = self.create_ubi_xml_sixx(setup_code, loop_code)

            if not filename.endswith('.ubi'):
                filename += '.ubi'

            with open(filename, 'w', encoding='utf-16') as f:
                f.write(xml_content)

            return True, filename
        except Exception as e:
            import traceback
            return False, "Ошибка при сохранении:\n{}\n\nПодробности:\n{}".format(str(e), traceback.format_exc())


def main_cli():
    """
    Главная функция для запуска приложения в GUI или CLI режиме.
    
    Если запущено без аргументов - открывает графический интерфейс.
    Если указан параметр --input - работает в CLI режиме:
    - Загружает Arduino скетч
    - Парсит код
    - Генерирует .ubi файл
    - Выводит результат в консоль
    
    CLI параметры:
        --input, -i: Путь к .ino файлу (обязательный для CLI режима)
        --output, -o: Путь для сохранения .ubi (опционально)
        --name, -n: Название блока (опционально)
        --description, -d: Описание блока (опционально)
    
    Примеры использования:
        python script.py                          # GUI режим
        python script.py -i sketch.ino             # CLI режим
        python script.py -i sketch.ino -o out.ubi # CLI с указанием выхода
    """
    parser = argparse.ArgumentParser(
        description="Arduino to FLProg converter (GUI + CLI). "
                    "Без аргументов запускается графический интерфейс."
    )
    parser.add_argument(
        "--input", "-i",
        help="Путь к Arduino скетчу (.ino) для конвертации в .ubi"
    )
    parser.add_argument(
        "--output", "-o",
        help="Путь для сохранения .ubi файла (по умолчанию: имя скетча + .ubi в той же папке)"
    )
    parser.add_argument(
        "--name", "-n",
        help="Название блока (если не указано — используется значение по умолчанию или из GUI-поля)"
    )
    parser.add_argument(
        "--description", "-d",
        help="Описание блока (если не указано — берётся из верхнего комментария или из GUI-поля)"
    )

    args = parser.parse_args()

    # Если не указаны CLI-параметры, запускаем обычный GUI
    if not args.input:
        app = QtWidgets.QApplication(sys.argv)
        window = ArduinoToFLProgConverter()
        window.show()
        sys.exit(app.exec_())

    # CLI-режим
    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Ошибка: файл '{input_path}' не найден")
        sys.exit(1)

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла '{input_path}': {e}")
        sys.exit(1)

    # Создаём невидимое приложение Qt и конвертер
    app = QtWidgets.QApplication(sys.argv)
    converter = ArduinoToFLProgConverter()

    # Заполняем поля
    converter.code_input.setPlainText(code)

    # Название блока: приоритет --name, иначе имя файла без расширения
    if args.name:
        converter.block_name_entry.setText(args.name)
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        converter.block_name_entry.setText(base_name)
    if args.description:
        converter.block_description_entry.setPlainText(args.description)

    # Парсим код (заполнит переменные, функции и при отсутствии --description подхватит верхний комментарий)
    converter.parse_code()

    # Определяем выходной путь
    if args.output:
        output_path = args.output
    else:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".ubi"

    ok, info = converter.generate_block_to_file(output_path)
    if ok:
        print(f"Блок успешно сохранен в формате SIXX:\n{info}")
        sys.exit(0)
    else:
        print(info)
        sys.exit(1)


if __name__ == "__main__":
    main_cli()


