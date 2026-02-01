"""
ino2ubi — минимальный launcher для exe.
Запускает arduino_to_flprog_GLOBAL_COMPLETE.py из той же папки.
Остальные модули (gui, parser, generator, constants) загружаются как скрипты.
"""

import logging
import os
import runpy
import sys


def _show_error(msg):
    """Показать окно ошибки на Windows без зависимости от Qt."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "ino2ubi", 0x10)
    except Exception:
        pass


def main():
    if getattr(sys, "frozen", False):
        script_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    # Лог в папку с программой для отладки падений
    log_file = os.path.join(script_dir, "ino2ubi.log")
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
    log = logging.getLogger("launcher")
    log.info("launcher: start, script_dir=%s", script_dir)

    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    main_script = os.path.join(script_dir, "arduino_to_flprog_GLOBAL_COMPLETE.py")
    if not os.path.isfile(main_script):
        log.error("main script not found: %s", main_script)
        _show_error(
            "Не найден файл arduino_to_flprog_GLOBAL_COMPLETE.py\n\n"
            "Положите exe и .py файлы в одну папку."
        )
        sys.exit(1)

    sys.argv[0] = main_script
    log.info("launcher: running main_script")
    try:
        runpy.run_path(main_script, run_name="__main__")
        log.info("launcher: main_script exited normally")
    except Exception as e:
        log.exception("launcher: main_script crashed: %s", e)
        raise


if __name__ == "__main__":
    main()
