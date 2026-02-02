"""
Константы для ino2ubi — конвертера Arduino скетчей в блоки FLProg.
"""

# Версия приложения
VERSION = "1.7.2"

# GitHub-репозиторий для проверки обновлений (owner/repo)
GITHUB_REPO = "phazz1980/ino2ubi"

# Примитивные типы Arduino, отображаемые в таблице переменных
PRIMITIVE_TYPES = {
    'int', 'long', 'unsigned long', 'bool', 'boolean', 'float', 'double',
    'byte', 'char', 'String', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t'
}

# Порядок типов для выбора типа define в GUI (все типы переменных Arduino)
DEFINE_TYPE_CHOICES = [
    'int', 'long', 'unsigned long', 'float',
    'byte', 'char', 'String', 'bool', 'boolean',
]

# Маппинг типов Arduino на SIXX-типы FLProg
TYPE_MAPPING = {
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
