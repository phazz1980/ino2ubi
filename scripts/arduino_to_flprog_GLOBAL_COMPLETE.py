"""
================================================================================
ino2ubi — Конвертер Arduino скетчей (.ino) в блоки FLProg (.ubi)
================================================================================

Точка входа приложения. Поддерживает GUI и CLI режимы.

Структура проекта:
    launcher.py                           — launcher для exe (только при сборке)
    arduino_to_flprog_GLOBAL_COMPLETE.py  — точка входа (GUI/CLI)
    gui.py                                — графический интерфейс PyQt5
    generator.py                          — генерация SIXX XML для FLProg
    parser.py                             — парсинг Arduino кода
    constants.py                          — константы, версия, маппинг типов
    README.md                             — документация и справка (F1 в GUI)

Использование:
    python arduino_to_flprog_GLOBAL_COMPLETE.py              # GUI
    python arduino_to_flprog_GLOBAL_COMPLETE.py -i file.ino  # CLI
"""

import argparse
import logging
import os
import sys


def _setup_logging():
    """Лог в папку с программой (ino2ubi.log) для отладки падений."""
    if logging.root.handlers:
        return
    app_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(app_dir, "ino2ubi.log")
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            encoding="utf-8",
        )
    except TypeError:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )


def _excepthook(etype, value, tb):
    """Логировать необработанные исключения перед падением."""
    _log.critical("Uncaught exception", exc_info=(etype, value, tb))
    sys.__excepthook__(etype, value, tb)


_setup_logging()
_log = logging.getLogger(__name__)
sys.excepthook = _excepthook

from PyQt5 import QtWidgets

from gui import ArduinoToFLProgConverter


def main_cli():
    """Запуск приложения в GUI или CLI режиме."""
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
        help="Путь для сохранения .ubi файла (по умолчанию: имя скетча + .ubi)"
    )
    parser.add_argument(
        "--name", "-n",
        help="Название блока"
    )
    parser.add_argument(
        "--description", "-d",
        help="Описание блока"
    )

    args = parser.parse_args()
    _log.info("main_cli: start, input=%s", getattr(args, "input", None))

    if not args.input:
        _log.debug("main_cli: GUI mode")
        app = QtWidgets.QApplication(sys.argv)
        _log.debug("main_cli: creating window")
        window = ArduinoToFLProgConverter()
        _log.debug("main_cli: showing window, entering event loop")
        window.show()
        sys.exit(app.exec_())

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

    app = QtWidgets.QApplication(sys.argv)
    converter = ArduinoToFLProgConverter()

    converter.code_input.setPlainText(code)

    if args.name:
        converter.block_name_entry.setText(args.name)
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        converter.block_name_entry.setText(base_name)

    if args.description:
        converter.block_description_entry.setPlainText(args.description)

    converter.parse_code()

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
