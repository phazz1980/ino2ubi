"""
Парсер Arduino скетчей (.ino) для извлечения переменных, функций, директив.
"""

import re

from constants import PRIMITIVE_TYPES


def extract_function_body(code: str, func_name: str) -> str:
    """Извлекает тело функции void func_name() из кода."""
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
        return code[start_pos:pos - 1].strip()
    return ""


def extract_custom_function_body(code: str, start_pos: int) -> str:
    """Извлекает тело пользовательской функции по начальной позиции (после '{')."""
    brace_count = 1
    pos = start_pos
    while pos < len(code) and brace_count > 0:
        if code[pos] == '{':
            brace_count += 1
        elif code[pos] == '}':
            brace_count -= 1
        pos += 1
    if brace_count == 0:
        return code[start_pos:pos - 1].strip()
    return ""


def extract_global_section(code: str) -> str:
    """Извлекает глобальную секцию кода (до setup/loop)."""
    setup_match = re.search(r'void\s+setup\s*\(', code)
    loop_match = re.search(r'void\s+loop\s*\(', code)
    first_func_pos = len(code)
    if setup_match and setup_match.start() < first_func_pos:
        first_func_pos = setup_match.start()
    if loop_match and loop_match.start() < first_func_pos:
        first_func_pos = loop_match.start()
    return code[:first_func_pos].strip()


def extract_leading_comment(code: str) -> str | None:
    """Возвращает текст комментария в начале скетча (//... или /* ... */), если он есть."""
    i = 0
    n = len(code)

    while i < n and code[i].isspace():
        i += 1

    if i >= n:
        return None

    if code.startswith("/*", i):
        end = code.find("*/", i + 2)
        if end == -1:
            comment_body = code[i + 2:].strip()
        else:
            comment_body = code[i + 2:end].strip()
        return comment_body or None

    if code.startswith("//", i):
        lines = []
        pos = i
        while pos < n:
            line_end = code.find("\n", pos)
            if line_end == -1:
                line_end = n
            line = code[pos:line_end]
            if line.strip().startswith("//"):
                clean = re.sub(r'^\s*//\s*', '', line).rstrip()
                lines.append(clean)
                pos = line_end + 1
            else:
                break
        comment_body = "\n".join(lines).strip()
        return comment_body or None

    return None


def parse_function_params(params_str: str) -> list[dict]:
    """Парсит строку параметров функции в список словарей с type и name."""
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


def parse_functions(code: str) -> dict:
    """Парсит все пользовательские функции (кроме setup и loop)."""
    func_pattern = r'(void|int|long|bool|boolean|float|double|byte|char|String|uint8_t|int16_t|uint16_t|int32_t|uint32_t)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{'
    matches = list(re.finditer(func_pattern, code))
    functions = {}

    for match in matches:
        func_name = match.group(2)
        if func_name in ['setup', 'loop']:
            continue

        return_type = match.group(1).strip()
        params_str = match.group(3).strip()
        body_start = match.end()
        func_body = extract_custom_function_body(code, body_start)
        parsed_params = parse_function_params(params_str)

        func_pos = match.start()
        setup_pos = len(code)
        loop_pos = len(code)
        if setup_match := re.search(r'void\s+setup\s*\(', code):
            setup_pos = setup_match.start()
        if loop_match := re.search(r'void\s+loop\s*\(', code):
            loop_pos = loop_match.start()
        first_func_pos = min(setup_pos, loop_pos)

        location = "до setup/loop" if func_pos < first_func_pos else "после loop"

        functions[func_name] = {
            'return_type': return_type,
            'params': params_str,
            'parsed_params': parsed_params,
            'body': func_body,
            'location': location
        }

    return functions


def parse_global_section(
    global_section: str,
    functions: dict
) -> tuple[dict, list, dict, list]:
    """
    Парсит глобальную секцию кода.
    Возвращает: (variables, global_includes, global_defines, extra_declarations)
    """
    # Убираем функции, определённые до setup/loop
    section = global_section
    for func_name, func_info in functions.items():
        if func_info['location'] == "до setup/loop":
            func_pattern = r'(void|int|long|bool|boolean|float|double|byte|char|String)\s+{}\s*\([^)]*\)\s*\{{[^}}]*\}}'.format(func_name)
            section = re.sub(func_pattern, '', section, flags=re.DOTALL)

    # Парсим директивы #include и #define
    include_pattern = r'^\s*#include[^\n]*$'
    global_includes = re.findall(include_pattern, section, re.MULTILINE)

    define_pattern = r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$'
    global_defines = {
        name: value.strip()
        for (name, value) in re.findall(define_pattern, section, re.MULTILINE)
    }

    # Парсим глобальные переменные
    variables = {}
    extra_declarations = []
    var_pattern = r'\b(?:const\s+)?([A-Za-z_][A-Za-z0-9_:<>]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*([^;]+))?;'
    matches = re.finditer(var_pattern, section)

    for match in matches:
        full_decl = match.group(0).strip()
        var_type = match.group(1).strip()
        var_name = match.group(2)
        var_value = match.group(3).strip() if match.group(3) else None

        line_start = section.rfind('\n', 0, match.start()) + 1
        line_end = section.find('\n', match.start())
        if line_end == -1:
            line_end = len(section)
        line_text = section[line_start:line_end]

        role = 'variable'
        if re.search(r'//\s*in\b', line_text):
            role = 'input'
        elif re.search(r'//\s*out\b', line_text):
            role = 'output'
        elif re.search(r'//\s*par\b', line_text):
            role = 'parameter'

        if var_type in PRIMITIVE_TYPES:
            variables[var_name] = {
                'type': var_type,
                'default': var_value,
                'role': role,
                'alias': var_name
            }
        else:
            extra_declarations.append(full_decl)

    return variables, global_includes, global_defines, extra_declarations


def parse_arduino_code(code: str) -> dict:
    """
    Парсит полный Arduino скетч.
    Возвращает словарь:
    - leading_comment: str | None
    - variables: dict
    - functions: dict
    - global_section_raw: str
    - global_includes: list
    - global_defines: dict
    - extra_declarations: list
    """
    leading_comment = extract_leading_comment(code)
    functions = parse_functions(code)
    global_section_raw = extract_global_section(code)

    variables, global_includes, global_defines, extra_declarations = parse_global_section(
        global_section_raw, functions
    )

    return {
        'leading_comment': leading_comment,
        'variables': variables,
        'functions': functions,
        'global_section_raw': global_section_raw,
        'global_includes': global_includes,
        'global_defines': global_defines,
        'extra_declarations': extra_declarations,
    }
