"""
Графический интерфейс (GUI) для ino2ubi — конвертера Arduino в блоки FLProg.
"""

import os
import re
import sys
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui

from constants import VERSION
from parser import parse_arduino_code, extract_function_body
from generator import create_ubi_xml_sixx


def _resource_dir():
    """Каталог с ресурсами: при сборке exe — sys._MEIPASS, иначе — каталог gui.py."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


class ArduinoToFLProgConverter(QtWidgets.QMainWindow):
    """
    Главный класс приложения для конвертации Arduino кода в блоки FLProg.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ino2ubi v{}".format(VERSION))
        self.resize(1400, 850)
        self._set_window_icon()
        self.variables = {}
        self.functions = {}
        self.global_section_raw = ""
        self.global_includes = []
        self.global_defines = {}
        self.extra_declarations = []
        self._safe_home = self._get_safe_home_dir()
        self.last_save_dir = self._safe_home
        self.create_widgets()

    def _get_safe_home_dir(self):
        """Начальная папка для диалогов: никогда не system32."""
        home = os.path.expanduser("~")
        if not home:
            home = os.environ.get("USERPROFILE", "")
        if not home:
            home = os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")
        home = os.path.abspath(home) if home else ""
        try:
            cwd = os.path.abspath(os.getcwd())
            if "system32" in cwd.lower() or "system64" in cwd.lower():
                pass
            elif home and os.path.isdir(home):
                pass
            else:
                home = cwd if os.path.isdir(cwd) else "."
        except Exception:
            home = home or "."
        return home if (home and os.path.isdir(home)) else "."

    def _set_window_icon(self):
        """Устанавливает иконку окна из icon.ico."""
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
            if not icon.isNull():
                self.setWindowIcon(icon)

    def create_widgets(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

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

        self.enable_input_checkbox = QtWidgets.QCheckBox("Вход En (условие выполнения кода в Loop: if(En))")
        self.enable_input_checkbox.setChecked(False)
        settings_layout.addWidget(self.enable_input_checkbox, 2, 0, 1, 2)

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
        self.code_input.insertPlainText(QtWidgets.QApplication.clipboard().text())

    def copy_code(self):
        cursor = self.code_input.textCursor()
        if cursor.hasSelection():
            QtWidgets.QApplication.clipboard().setText(cursor.selectedText())

    def cut_code(self):
        cursor = self.code_input.textCursor()
        if cursor.hasSelection():
            QtWidgets.QApplication.clipboard().setText(cursor.selectedText())
            cursor.removeSelectedText()

    def select_all_code(self):
        self.code_input.selectAll()

    def _load_help_text(self):
        """Загружает справку из README.md (в exe — из папки распаковки PyInstaller)."""
        candidates = [
            os.path.join(_resource_dir(), "README.md"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        ]
        if getattr(sys, "frozen", False) and getattr(sys, "executable", None):
            candidates.append(os.path.join(os.path.dirname(sys.executable), "README.md"))
        for readme_path in candidates:
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                continue
        return (
            "# Справка — ino2ubi\n\n"
            "Файл справки (README.md) не найден.\n\n"
            "**Назначение:** конвертация Arduino скетчей (.ino) в пользовательские блоки (.ubi) для FLProg.\n\n"
            "**Использование:** вставьте или загрузите код, задайте имя и описание блока, нажмите «Сгенерировать .ubi».\n\n"
            "Полная документация — в файле README.md рядом с программой."
        )

    def show_help(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Справка — ino2ubi")
        dialog.resize(700, 550)
        layout = QtWidgets.QVBoxLayout(dialog)
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        help_text = self._load_help_text()
        try:
            text.setMarkdown(help_text)
        except AttributeError:
            text.setPlainText(help_text)
        text.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(text)
        btn_close = QtWidgets.QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec_()

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "О программе",
            (
                "<h3>ino2ubi</h3>"
                "<p>Конвертация Arduino скетчей (.ino) в пользовательские блоки (.ubi) для FLProg.</p>"
                "<p><b>Версия:</b> {}</p>"
                "<p><b>Требования:</b> Python 3.x, PyQt5</p>"
                "<p>Справка: меню <b>Справка → Справка...</b> или клавиша <b>F1</b></p>"
            ).format(VERSION)
        )

    def clear_code(self):
        self.code_input.clear()

    def load_arduino_file(self):
        start_dir = self.last_save_dir if os.path.isdir(self.last_save_dir) else self._safe_home
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите Arduino файл", start_dir, "Arduino files (*.ino);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.code_input.setPlainText(f.read())
                base_name = os.path.splitext(os.path.basename(filename))[0]
                self.block_name_entry.setText(base_name)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", "Не удалось загрузить файл: {}".format(e))

    def parse_code(self):
        """Парсит Arduino код и обновляет таблицы."""
        code = self.code_input.toPlainText()
        self.var_tree.clear()
        self.variables = {}
        self.func_tree.clear()
        self.functions = {}
        self.global_section_raw = ""
        self.global_includes = []
        self.global_defines = {}
        self.extra_declarations = []

        result = parse_arduino_code(code)

        if result['leading_comment']:
            self.block_description_entry.setPlainText(result['leading_comment'])

        self.variables = result['variables']
        self.functions = result['functions']
        self.global_section_raw = result['global_section_raw']
        self.global_includes = result['global_includes']
        self.global_defines = result['global_defines']
        self.extra_declarations = result['extra_declarations']

        for func_name, func_info in self.functions.items():
            params_display = func_info['params'] if func_info['params'] else "(нет)"
            body_preview = func_info['body'][:50] + "..." if len(func_info['body']) > 50 else func_info['body']
            item = QtWidgets.QTreeWidgetItem([func_name, func_info['return_type'], params_display, body_preview])
            self.func_tree.addTopLevelItem(item)

        for var_name, var_info in self.variables.items():
            default_display = var_info.get('default') or ""
            item = QtWidgets.QTreeWidgetItem([
                var_name, var_info['type'], var_info['role'], var_info['alias'], default_display
            ])
            self.var_tree.addTopLevelItem(item)

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
        """Открывает диалог редактирования переменной."""
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

        role_combo = QtWidgets.QComboBox()
        role_combo.addItems(["variable", "input", "output", "parameter"])
        role_combo.setCurrentText(var_info['role'])
        role_combo.setToolTip(
            "variable - внутренняя переменная блока\n"
            "input - входной параметр (получает данные извне)\n"
            "output - выходной параметр (передаёт данные наружу)\n"
            "parameter - настраиваемый параметр блока"
        )
        settings_layout.addRow("Роль в блоке:", role_combo)

        alias_edit = QtWidgets.QLineEdit(var_info['alias'])
        alias_edit.setPlaceholderText("Введите псевдоним переменной")
        alias_edit.setToolTip("Имя переменной, которое будет использоваться в блоке FLProg")
        settings_layout.addRow("Псевдоним:", alias_edit)

        default_edit = QtWidgets.QLineEdit(var_info.get('default', '') or '')
        default_edit.setPlaceholderText("Введите значение по умолчанию")
        default_edit.setToolTip("Начальное значение переменной (для parameter и variable)")
        settings_layout.addRow("Значение по умолчанию:", default_edit)

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
            description_text.setText(role_descriptions.get(role_combo.currentText(), ""))

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
                QtWidgets.QMessageBox.warning(dialog, "Ошибка", "Псевдоним не может быть пустым!")
                return

            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_alias):
                QtWidgets.QMessageBox.warning(
                    dialog, "Ошибка",
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

    def generate_block(self):
        """Генерирует .ubi файл."""
        try:
            code = self.code_input.toPlainText()
            setup_code = extract_function_body(code, 'setup')
            loop_code = extract_function_body(code, 'loop')

            for var_name, var_info in self.variables.items():
                if var_info['alias'] != var_name:
                    loop_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], loop_code)
                    setup_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], setup_code)

            block_name = self.block_name_entry.text()
            block_description = self.block_description_entry.toPlainText().strip() or "Автоматически сгенерированный блок"

            xml_content = create_ubi_xml_sixx(
                block_name=block_name,
                block_description=block_description,
                variables=self.variables,
                functions=self.functions,
                global_includes=self.global_includes,
                global_defines=self.global_defines,
                extra_declarations=self.extra_declarations,
                setup_code=setup_code,
                loop_code=loop_code,
                enable_input=self.enable_input_checkbox.isChecked()
            )

            if (self.last_save_dir and os.path.exists(self.last_save_dir) and
                    "system32" not in os.path.normpath(self.last_save_dir).lower()):
                save_dir = self.last_save_dir
            else:
                try:
                    save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    if not os.path.exists(save_dir):
                        save_dir = os.path.join(os.path.expanduser("~"), "Рабочий стол")
                    if not os.path.exists(save_dir):
                        save_dir = os.path.expanduser("~")
                except Exception:
                    save_dir = os.path.expanduser("~")

            default_filename = os.path.join(save_dir, "{}.ubi".format(block_name))

            filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Сохранить блок", default_filename,
                "FLProg Block (*.ubi);;All files (*.*)"
            )

            if filename:
                if not filename.endswith('.ubi'):
                    filename += '.ubi'

                with open(filename, 'w', encoding='utf-16') as f:
                    f.write(xml_content)

                new_dir = os.path.dirname(filename)
                if new_dir and "system32" not in new_dir.lower():
                    self.last_save_dir = new_dir

                QtWidgets.QMessageBox.information(
                    self, "Успех",
                    "Блок успешно сохранен в формате SIXX:\n{}".format(filename)
                )

        except Exception as e:
            error_msg = "Ошибка при сохранении:\n{}\n\nПодробности:\n{}".format(str(e), traceback.format_exc())
            QtWidgets.QMessageBox.critical(self, "Ошибка", error_msg)

    def generate_block_to_file(self, filename):
        """CLI-версия: сохраняет .ubi без диалогов."""
        try:
            code = self.code_input.toPlainText()
            setup_code = extract_function_body(code, 'setup')
            loop_code = extract_function_body(code, 'loop')

            for var_name, var_info in self.variables.items():
                if var_info['alias'] != var_name:
                    loop_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], loop_code)
                    setup_code = re.sub(r'\b' + var_name + r'\b', var_info['alias'], setup_code)

            block_name = self.block_name_entry.text()
            block_description = self.block_description_entry.toPlainText().strip() or "Автоматически сгенерированный блок"

            xml_content = create_ubi_xml_sixx(
                block_name=block_name,
                block_description=block_description,
                variables=self.variables,
                functions=self.functions,
                global_includes=self.global_includes,
                global_defines=self.global_defines,
                extra_declarations=self.extra_declarations,
                setup_code=setup_code,
                loop_code=loop_code,
                enable_input=self.enable_input_checkbox.isChecked()
            )

            if not filename.endswith('.ubi'):
                filename += '.ubi'

            with open(filename, 'w', encoding='utf-16') as f:
                f.write(xml_content)

            return True, filename
        except Exception as e:
            return False, "Ошибка при сохранении:\n{}\n\nПодробности:\n{}".format(str(e), traceback.format_exc())
