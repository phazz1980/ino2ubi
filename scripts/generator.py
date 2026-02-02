"""
Генератор SIXX XML для FLProg (.ubi файлы).
"""

import html
import re
import uuid

from constants import TYPE_MAPPING


def escape_code_for_sixx(text: str) -> str:
    """Экранирование кода для SIXX: html.escape + ( ) , % как в FLProg."""
    s = html.escape(text)
    s = s.replace('(', '&#40;').replace(')', '&#41;')
    s = s.replace(',', '&#44;').replace('%', '&#37;')
    return s


def get_type_class_name(var_type: str) -> str:
    """Возвращает SIXX-имя класса типа данных для FLProg."""
    return TYPE_MAPPING.get(var_type, 'IntegerDataType')


def create_sixx_data_type(
    var_type: str,
    type_id: int,
    instance_coll_id: int,
    next_id: callable
) -> str:
    """Создаёт SIXX XML для типа данных с instanceCollection."""
    type_class = get_type_class_name(var_type)
    instance_id = next_id()

    xml = '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="type" sixx.type="{} class" sixx.env="Arduino" >\n'.format(type_id, type_class)
    xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="instanceCollection" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(instance_coll_id)
    xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="{}" sixx.env="Arduino" >\n'.format(instance_id, type_class)
    xml += '\t\t\t\t\t\t</sixx.object>\n'
    xml += '\t\t\t\t\t</sixx.object>\n'
    xml += '\t\t\t\t</sixx.object>\n'
    return xml


def create_ubi_xml_sixx(
    block_name: str,
    block_description: str,
    variables: dict,
    functions: dict,
    global_includes: list,
    defines: list,
    extra_declarations: list,
    static_declarations: list,
    setup_code: str,
    loop_code: str,
    enable_input: bool = False,
) -> str:
    """Создаёт SIXX XML для FLProg блока."""
    # Убираем пробелы в конце строк кода
    setup_code = '\n'.join(line.rstrip() for line in setup_code.splitlines())
    loop_code = '\n'.join(line.rstrip() for line in loop_code.splitlines())
    if enable_input:
        loop_code = "if(En)\n{\n" + loop_code + "\n}"
    loop_code_encoded = escape_code_for_sixx(loop_code)
    setup_code_encoded = escape_code_for_sixx(setup_code)

    current_id = [0]

    def next_id():
        current_id[0] += 1
        return current_id[0]

    root_id = 0
    code_block_id = next_id()
    main_uuid_id = next_id()
    main_uuid = str(uuid.uuid4())
    blocks_coll_id = next_id()
    label_id = next_id()
    inputs_coll_id = next_id()

    instance_coll_id = 15
    comment_str_id = 18

    # Порядок входов/выходов/параметров — как в коде (по position)
    _code_order_pos = lambda v: v.get('position', 999999999)

    inputs_xml = ""
    inputs_list = [(var_name, var_info) for var_name, var_info in variables.items() if var_info['role'] == 'input']
    inputs_list.sort(key=lambda x: _code_order_pos(x[1]))

    if enable_input:
        en_adaptor_id = next_id()
        en_obj_id = next_id()
        en_id_source_id = next_id()
        en_type_id = next_id()
        en_name_id = next_id()
        en_uuid_obj_id = next_id()
        en_input_uuid = str(uuid.uuid4())
        inputs_xml += '\t\t\t<sixx.object sixx.id="{}" sixx.type="InputsOutputsAdaptorForUserBlock" sixx.env="Arduino" >\n'.format(en_adaptor_id)
        inputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="object" sixx.type="UniversalBlockInputOutput" sixx.env="Arduino" >\n'.format(en_obj_id)
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="SmallInteger" sixx.env="Core" >119328430</sixx.object>\n'.format(en_id_source_id)
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="block" sixx.idref="{}" />\n'.format(code_block_id)
        inputs_xml += create_sixx_data_type('boolean', en_type_id, instance_coll_id, next_id)
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isInput" sixx.type="True" sixx.env="Core" />\n'
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >En</sixx.object>\n'.format(en_name_id)
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="isNot" sixx.type="False" sixx.env="Core" />\n'
        inputs_xml += '\t\t\t\t\t<sixx.object sixx.name="nameCash" sixx.idref="{}" />\n'.format(en_name_id)
        inputs_xml += '\t\t\t\t</sixx.object>\n'
        inputs_xml += '\t\t\t\t<sixx.object sixx.name="comment" sixx.idref="{}" />\n'.format(comment_str_id)
        inputs_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(en_uuid_obj_id, en_input_uuid)
        inputs_xml += '\t\t\t</sixx.object>\n'

    id_base = 119329430 if enable_input else 119328430
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
        inputs_xml += create_sixx_data_type(var_info['type'], type_id, instance_coll_id, next_id)
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
    outputs_list = [(var_name, var_info) for var_name, var_info in variables.items() if var_info['role'] == 'output']
    outputs_list.sort(key=lambda x: _code_order_pos(x[1]))

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
        outputs_xml += create_sixx_data_type(var_info['type'], type_id, instance_coll_id, next_id)
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
    # Параметры: переменные + #define с role=parameter, в порядке появления в коде
    params_list = []
    for var_name, var_info in variables.items():
        if var_info['role'] == 'parameter':
            params_list.append((_code_order_pos(var_info), var_name, var_info))
    for d in (defines or []):
        if d.get('role') == 'parameter':
            default_val_define = d.get('value')
            if default_val_define is None:
                default_val_define = ''
            else:
                default_val_define = str(default_val_define)
            params_list.append((d.get('position', 999999999), d['name'], {
                'type': d.get('type', 'String'),
                'alias': d['name'],
                'default': default_val_define,
            }))
    params_list.sort(key=lambda x: x[0])
    params_list = [(name, info) for _, name, info in params_list]

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

        if var_info['type'] == 'String':
            default_val = var_info.get('default', '') or ''
        else:
            default_val = var_info.get('default', '0') or '0'

        param_type = var_info['type']
        if param_type in ('bool', 'boolean'):
            default_val = '1' if str(default_val).strip().lower() in ('true', '1') else '0'

        params_xml += '\t\t\t\t<sixx.object sixx.id="{}" sixx.type="InputsOutputsAdaptorForUserBlock" sixx.env="Arduino" >\n'.format(adaptor_id)
        params_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="object" sixx.type="UserBlockParametr" sixx.env="Arduino" >\n'.format(param_id)
        params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(param_name_id, var_info["alias"])
        params_xml += create_sixx_data_type(param_type, param_type_id, instance_coll_id, next_id)
        params_xml += '\t\t\t\t\t\t<sixx.object sixx.name="hasDefaultValue" sixx.type="True" sixx.env="Core" />\n'

        if param_type == 'String':
            params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="stringDefaultValue" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(default_val_id, html.escape(default_val))
        else:
            try:
                if param_type in ('float', 'double'):
                    params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="numberDefaultValue" sixx.type="Float" sixx.env="Core" >{}</sixx.object>\n'.format(default_val_id, default_val)
                else:
                    params_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="numberDefaultValue" sixx.type="SmallInteger" sixx.env="Core" >{}</sixx.object>\n'.format(default_val_id, default_val)
            except Exception:
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
    vars_list = [(var_name, var_info) for var_name, var_info in variables.items() if var_info['role'] == 'variable']

    # #include — как в FLProg: CodeUserBlockDeclareDefineBlock (define="#include", name="<...>")
    for inc in global_includes:
        line = (inc or '').strip().rstrip()
        if not line.startswith('#include'):
            continue
        rest = line[8:].strip().rstrip()
        decl_id = next_id()
        define_id = next_id()
        name_id = next_id()
        declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareDefineBlock" sixx.env="Arduino" >\n'.format(decl_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="define" sixx.type="String" sixx.env="Core" >&#35;include</sixx.object>\n'.format(define_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(name_id, html.escape(rest))
        declare_xml += '\t\t\t\t\t</sixx.object>\n'

    # #define (не parameter) — CodeUserBlockDeclareDefineBlock (define="#define", name, lastPart)
    for d in (defines or []):
        if d.get('role') == 'parameter':
            continue
        decl_id = next_id()
        define_id = next_id()
        name_id = next_id()
        last_part_id = next_id()
        d_name = (str(d.get('name', '')).strip().rstrip())
        d_value = (str(d.get('value', '')).strip().rstrip())
        declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareDefineBlock" sixx.env="Arduino" >\n'.format(decl_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="define" sixx.type="String" sixx.env="Core" >&#35;define</sixx.object>\n'.format(define_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(name_id, html.escape(d_name))
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(last_part_id, html.escape(d_value))
        declare_xml += '\t\t\t\t\t</sixx.object>\n'

    # static-переменные (из global, в GUI не редактируются) — CodeUserBlockDeclareStandartBlock: firstPart="static type", name, lastPart
    for line in (static_declarations or []):
        line = (line or '').strip().rstrip()
        if not line.endswith(';'):
            continue
        stmt = line[:-1].strip()
        if not re.match(r'^\s*static\s+', stmt):
            continue
        m = re.match(r'^\s*static\s+(.+?)\s+([a-zA-Z_][A-Za-z0-9_]*)\s*(.*)$', stmt, re.DOTALL)
        if not m:
            continue
        first_part = "static " + m.group(1).strip()
        name_part = m.group(2)
        rest = m.group(3).strip()
        if rest.startswith('='):
            last_part = "= {};".format(escape_code_for_sixx(rest[1:].strip()))
        else:
            last_part = ";"
        decl_id = next_id()
        decl_name_id = next_id()
        decl_last_id = next_id()
        decl_first_id = next_id()
        declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_name_id, html.escape(name_part))
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_last_id, last_part)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, html.escape(first_part))
        declare_xml += '\t\t\t\t\t</sixx.object>\n'

    # Остальные объявления (extra) — CodeUserBlockDeclareStandartBlock, порядок как в FLProg: name, lastPart, firstPart
    for line in extra_declarations:
        line = (line or '').strip().rstrip()
        if not line.endswith(';'):
            continue
        stmt = line[:-1].strip()
        decl_id = next_id()
        decl_name_id = next_id()
        decl_last_id = next_id()
        decl_first_id = next_id()
        # "SoftwareSerial newSerial = SoftwareSerial(7, 8)" -> firstPart=SoftwareSerial, name=newSerial, lastPart="= SoftwareSerial(7, 8);"
        parts = stmt.split(None, 2)
        if len(parts) >= 2:
            first_part = parts[0]
            name_part = parts[1]
            last_part_raw = parts[2] if len(parts) > 2 else ""
            if last_part_raw.startswith('='):
                last_part = "= {};".format(escape_code_for_sixx(last_part_raw[1:].strip()))
            else:
                last_part = "= {};".format(escape_code_for_sixx(last_part_raw)) if last_part_raw else ";"
        else:
            first_part = parts[0] if parts else ""
            name_part = ""
            last_part = ";"
        declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_name_id, html.escape(name_part))
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_last_id, last_part)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, html.escape(first_part))
        declare_xml += '\t\t\t\t\t</sixx.object>\n'

    for var_name, var_info in vars_list:
        decl_id = next_id()
        decl_name_id = next_id()
        decl_last_id = next_id()
        decl_first_id = next_id()

        default_val = var_info.get('default')
        if default_val:
            last_part = "= {};".format(escape_code_for_sixx(str(default_val).strip().rstrip()))
        else:
            last_part = ";"

        declare_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockDeclareStandartBlock" sixx.env="Arduino" >\n'.format(decl_id)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_name_id, (var_info.get("alias") or "").strip().rstrip())
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="lastPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_last_id, last_part)
        declare_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="firstPart" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(decl_first_id, (var_info.get("type") or "").strip().rstrip())
        declare_xml += '\t\t\t\t\t</sixx.object>\n'

    func_part_id = next_id()
    func_coll_id = next_id()
    functions_xml = ""

    for func_name, func_info in functions.items():
        func_id = next_id()
        func_body_id = next_id()
        func_proto_id = next_id()
        func_ret_type_id = next_id()
        func_name_id = next_id()
        func_params_coll_id = next_id()

        body_encoded = escape_code_for_sixx('\n'.join(line.rstrip() for line in func_info['body'].splitlines()))

        functions_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockFunction" sixx.env="Arduino" >\n'.format(func_id)
        functions_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="functionBody" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_body_id, body_encoded)
        functions_xml += '\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="parsesFunctionName" sixx.type="CodeUserBlockFunctionName" sixx.env="Arduino" >\n'.format(func_proto_id)
        functions_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="declare" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_ret_type_id, func_info["return_type"])
        functions_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(func_name_id, func_name)
        functions_xml += '\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="parametrs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(func_params_coll_id)

        for param in func_info.get('parsed_params', []):
            fparam_id = next_id()
            fparam_type_id = next_id()
            fparam_name_id = next_id()

            functions_xml += '\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.type="CodeUserBlockFunctionParametr" sixx.env="Arduino" >\n'.format(fparam_id)
            functions_xml += '\t\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="declare" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(fparam_type_id, param["type"])
            functions_xml += '\t\t\t\t\t\t\t\t<sixx.object sixx.id="{}" sixx.name="name" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(fparam_name_id, param["name"])
            functions_xml += '\t\t\t\t\t\t\t</sixx.object>\n'

        functions_xml += '\t\t\t\t\t\t</sixx.object>\n'
        functions_xml += '\t\t\t\t\t</sixx.object>\n'
        functions_xml += '\t\t\t\t\t</sixx.object>\n'

    libs_id = next_id()

    xml_header = '<sixx.object sixx.id="{}" sixx.type="BlocksLibraryElement" sixx.env="Arduino" >\n'.format(root_id)
    xml_header += '\t<sixx.object sixx.id="{}" sixx.name="typeClass" sixx.type="CodeUserBlock" sixx.env="Arduino" >\n'.format(code_block_id)
    xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="id" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(main_uuid_id, main_uuid)
    xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="blocks" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(blocks_coll_id)
    xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="label" sixx.type="String" sixx.env="Core" >{}</sixx.object>\n'.format(label_id, block_name)
    if inputs_xml:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="inputs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(inputs_coll_id)
        xml_header += inputs_xml
        xml_header += '\t\t</sixx.object>\n'
    else:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="inputs" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(inputs_coll_id)
    if outputs_xml:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="outputs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(outputs_coll_id)
        xml_header += outputs_xml
        xml_header += '\t\t</sixx.object>\n'
    else:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="outputs" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(outputs_coll_id)
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
    if params_xml:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="parametrs" sixx.type="OrderedCollection" sixx.env="Core" >\n'.format(params_coll_id)
        xml_header += params_xml
        xml_header += '\t\t</sixx.object>\n'
    else:
        xml_header += '\t\t<sixx.object sixx.id="{}" sixx.name="parametrs" sixx.type="OrderedCollection" sixx.env="Core" ></sixx.object>\n'.format(params_coll_id)
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
