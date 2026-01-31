"""
================================================================================
ino2ubi — Конвертер Arduino скетчей (.ino) в блоки FLProg (.ubi)
================================================================================

Точка входа приложения. Поддерживает GUI и CLI режимы.

Использование:
    python arduino_to_flprog_GLOBAL_COMPLETE.py              # GUI
    python arduino_to_flprog_GLOBAL_COMPLETE.py -i file.ino  # CLI
"""

import argparse
import os
import sys

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

    if not args.input:
        app = QtWidgets.QApplication(sys.argv)
        window = ArduinoToFLProgConverter()
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
