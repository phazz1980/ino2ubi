"""
Парсер Arduino скетчей (.ino) для извлечения переменных, функций, директив.
"""

import re

from constants import PRIMITIVE_TYPES, DEFINE_TYPE_CHOICES


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
) -> tuple[dict, list, list, list]:
    """
    Парсит глобальную секцию кода.
    Возвращает: (variables, global_includes, defines, extra_declarations)
    defines — список словарей {name, value, role} с ролями "global" | "parameter".
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

    def infer_define_type(value: str) -> str:
        """Определяет тип define по значению: кавычки -> String, true/false -> boolean, с запятой/точкой -> float, число -> long."""
        if not value:
            return 'String'
        s = value.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return 'String'
        if s.lower() in ('true', 'false'):
            return 'boolean'
        if ',' in s or '.' in s:
            try:
                float(s.replace(',', '.', 1))
                return 'float'
            except ValueError:
                pass
        try:
            int(s)
            return 'long'
        except ValueError:
            pass
        return 'String'

    # #define обрабатываются как переменные с двумя ролями: global и parameter; value — значение по умолчанию
    defines = []
    line_offset = 0
    for line in section.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('#define'):
            line_offset += len(line) + 1
            continue
        m = re.match(r'#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$', stripped)
        if not m:
            line_offset += len(line) + 1
            continue
        name, rest = m.group(1), m.group(2).strip()
        role = 'parameter' if re.search(r'//\s*par\b', rest) else 'global'
        value = rest.split('//')[0].strip() if '//' in rest else rest
        define_type = infer_define_type(value)
        defines.append({'name': name, 'value': value, 'role': role, 'type': define_type, 'position': line_offset})
        line_offset += len(line) + 1

    # Парсим глобальные переменные (поддержка множественных деклараций через запятую)
    variables = {}
    extra_declarations = []

    primitive_types = sorted(PRIMITIVE_TYPES, key=len, reverse=True)
    primitive_type_patterns = [
        re.sub(r'\s+', r'\\s+', re.escape(type_name)) for type_name in primitive_types
    ]
    primitive_type_regex = r'|'.join(primitive_type_patterns)

    def normalize_type(type_name: str) -> str:
        return re.sub(r'\s+', ' ', type_name.strip())

    def split_top_level(text: str, delimiter: str) -> list[str]:
        parts = []
        buf = []
        paren = bracket = brace = 0
        in_string = False
        string_char = ''
        escape = False
        for ch in text:
            if in_string:
                buf.append(ch)
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                buf.append(ch)
                continue
            if ch == '(':
                paren += 1
            elif ch == ')':
                paren = max(paren - 1, 0)
            elif ch == '[':
                bracket += 1
            elif ch == ']':
                bracket = max(bracket - 1, 0)
            elif ch == '{':
                brace += 1
            elif ch == '}':
                brace = max(brace - 1, 0)
            if (
                ch == delimiter
                and paren == 0
                and bracket == 0
                and brace == 0
            ):
                part = ''.join(buf).strip()
                if part:
                    parts.append(part)
                buf = []
            else:
                buf.append(ch)
        tail = ''.join(buf).strip()
        if tail:
            parts.append(tail)
        return parts

    def split_initializer(decl: str) -> tuple[str, str | None]:
        paren = bracket = brace = 0
        in_string = False
        string_char = ''
        escape = False
        for idx, ch in enumerate(decl):
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                continue
            if ch == '(':
                paren += 1
            elif ch == ')':
                paren = max(paren - 1, 0)
            elif ch == '[':
                bracket += 1
            elif ch == ']':
                bracket = max(bracket - 1, 0)
            elif ch == '{':
                brace += 1
            elif ch == '}':
                brace = max(brace - 1, 0)
            if (
                ch == '='
                and paren == 0
                and bracket == 0
                and brace == 0
            ):
                name_part = decl[:idx].strip()
                value_part = decl[idx + 1:].strip()
                return name_part, value_part or None
        return decl.strip(), None

    def extract_name(name_part: str) -> str | None:
        match = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', name_part)
        return match[-1] if match else None

    def split_statements(text: str) -> list[tuple[str, int]]:
        statements = []
        buf = []
        paren = bracket = brace = 0
        in_string = False
        string_char = ''
        escape = False
        start_idx = 0
        for idx, ch in enumerate(text):
            if in_string:
                buf.append(ch)
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == string_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                buf.append(ch)
                continue
            if ch == '(':
                paren += 1
            elif ch == ')':
                paren = max(paren - 1, 0)
            elif ch == '[':
                bracket += 1
            elif ch == ']':
                bracket = max(bracket - 1, 0)
            elif ch == '{':
                brace += 1
            elif ch == '}':
                brace = max(brace - 1, 0)
            if ch == ';' and paren == 0 and bracket == 0 and brace == 0:
                statement = ''.join(buf).strip()
                if statement:
                    statements.append((statement, start_idx))
                buf = []
                start_idx = idx + 1
            else:
                buf.append(ch)
        return statements

    def mask_directives(text: str) -> str:
        def repl(match: re.Match) -> str:
            return ' ' * (match.end() - match.start())
        return re.sub(r'^[ \t]*#.*$', repl, text, flags=re.MULTILINE)

    def mask_comments(text: str) -> str:
        def repl(match: re.Match) -> str:
            return ' ' * (match.end() - match.start())
        text = re.sub(r'/\*.*?\*/', repl, text, flags=re.DOTALL)
        text = re.sub(r'//[^\n]*', repl, text)
        return text

    masked_section = mask_comments(mask_directives(section))

    for statement, start_idx in split_statements(masked_section):
        stmt = statement.strip()
        if not stmt or stmt.startswith('#'):
            continue

        # Исключаем прототипы функций
        if re.search(r'\w+\s*\([^)]*\)\s*$', stmt) and '=' not in stmt:
            continue

        line_start = section.rfind('\n', 0, start_idx) + 1
        line_end = section.find('\n', start_idx)
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

        # Убираем базовые квалификаторы хранения
        stmt_no_qual = re.sub(r'^\s*(?:(?:static|const|volatile)\s+)+', '', stmt)

        primitive_match = re.match(
            r'^(?P<type>{})\b\s+(?P<decls>.+)$'.format(primitive_type_regex),
            stmt_no_qual
        )

        if primitive_match:
            var_type = normalize_type(primitive_match.group('type'))
            decls = primitive_match.group('decls').strip()
            for decl in split_top_level(decls, ','):
                name_part, value_part = split_initializer(decl)
                var_name = extract_name(name_part)
                if not var_name:
                    continue
                variables[var_name] = {
                    'type': var_type,
                    'default': value_part,
                    'role': role,
                    'alias': var_name,
                    'position': start_idx
                }
            continue

        # Остальные декларации сохраняем как есть (в т.ч. многострочные typedef struct/enum)
        if re.match(r'^[A-Za-z_][A-Za-z0-9_:<>]*\s+.+$', stmt, re.DOTALL):
            extra_declarations.append(stmt + ';')

    return variables, global_includes, defines, extra_declarations


def parse_arduino_code(code: str) -> dict:
    """
    Парсит полный Arduino скетч.
    Возвращает словарь:
    - leading_comment: str | None
    - variables: dict
    - functions: dict
    - global_section_raw: str
    - global_includes: list
    - defines: list[{name, value, role}] — #define как переменные с ролями global | parameter
    - extra_declarations: list
    """
    leading_comment = extract_leading_comment(code)
    functions = parse_functions(code)
    global_section_raw = extract_global_section(code)

    variables, global_includes, defines, extra_declarations = parse_global_section(
        global_section_raw, functions
    )

    return {
        'leading_comment': leading_comment,
        'variables': variables,
        'functions': functions,
        'global_section_raw': global_section_raw,
        'global_includes': global_includes,
        'defines': defines,
        'extra_declarations': extra_declarations,
    }
