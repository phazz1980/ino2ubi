"""
Точка входа из корня проекта: добавляет папку scripts в PYTHONPATH
и запускает приложение из scripts/arduino_to_flprog_GLOBAL_COMPLETE.py.
Используется при запуске из корня (python launcher.py) и при сборке exe.
"""

import os
import runpy
import sys


def main():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    scripts_dir = os.path.join(base_dir, "scripts")
    if not os.path.isdir(scripts_dir):
        sys.stderr.write("Ошибка: папка 'scripts' не найдена.\n")
        sys.exit(1)

    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    main_script = os.path.join(scripts_dir, "arduino_to_flprog_GLOBAL_COMPLETE.py")
    if not os.path.isfile(main_script):
        sys.stderr.write("Ошибка: не найден scripts/arduino_to_flprog_GLOBAL_COMPLETE.py\n")
        sys.exit(1)

    sys.argv[0] = main_script
    runpy.run_path(main_script, run_name="__main__")


if __name__ == "__main__":
    main()
