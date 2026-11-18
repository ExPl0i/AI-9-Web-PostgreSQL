"""Готовый модуль: тексты ошибок на русском языке для единого формата ошибок (задание З5).

Писать и менять этот файл не нужно. Функции используются в обработчиках исключений main.py.

FastAPI сообщает об ошибке проверки списком словарей (exc.errors()), например:
    {"type": "greater_than", "loc": ("body", "distance"), "msg": "Input should be greater than 0",
     "input": -5, "ctx": {"gt": 0.0}}
Функция describe превращает такой словарь в {"field": "distance", "error": "должно быть больше 0"}.
"""

NOT_JSON = "тело запроса – не JSON"

# Вид ошибки (поле type) -> текст. В фигурных скобках – значения из поля ctx.
MESSAGES = {
    "missing": "обязательное поле",
    "greater_than": "должно быть больше {gt}",
    "greater_than_equal": "должно быть не меньше {ge}",
    "less_than": "должно быть меньше {lt}",
    "less_than_equal": "должно быть не больше {le}",
    "float_parsing": "должно быть числом",
    "float_type": "должно быть числом",
    "int_parsing": "должно быть целым числом",
    "int_type": "должно быть целым числом",
    "int_from_float": "должно быть целым числом",
    "enum": "допустимые значения: {expected}",
    "string_type": "должно быть строкой",
    "string_too_short": "не короче {min_length} символов",
    "string_too_long": "не длиннее {max_length} символов",
    "model_attributes_type": "тело запроса должно быть объектом JSON",
    "dict_type": "тело запроса должно быть объектом JSON",
    "model_type": "тело запроса должно быть объектом JSON",
}
DATE_MESSAGE = "дата в виде ГГГГ-ММ-ДД, которая есть в календаре"

# Тексты для ошибок, которые FastAPI отправляет сам (ответы 404 и 405 на неизвестный адрес или метод).
HTTP_MESSAGES = {
    "Not Found": "нет такого адреса",
    "Method Not Allowed": "этот адрес не поддерживает метод {method}",
}


def _number(value):
    """0.0 -> '0', 1.2 -> '1.2': целые значения границ пишем без дробной части."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def error_field(loc) -> str | None:
    """Имя поля по месту ошибки: ('body', 'distance') -> 'distance', ('query', 'surface') -> 'surface'.

    Если места нет или в конце стоит не имя (например, позиция в неверном JSON), поле – None.
    """
    if len(loc) >= 2 and isinstance(loc[-1], str):
        return loc[-1]
    return None


def russian_message(error: dict) -> str:
    """Текст ошибки на русском языке по ее виду; для неизвестного вида – исходный английский текст."""
    kind = error.get("type", "")
    if kind.startswith("date"):
        return DATE_MESSAGE
    template = MESSAGES.get(kind)
    if template is None:
        return error.get("msg", "неверное значение")
    ctx = {key: _number(value) for key, value in (error.get("ctx") or {}).items()}
    if "expected" in ctx:
        ctx["expected"] = ctx["expected"].replace("'", "").replace(" or ", ", ")
    try:
        return template.format(**ctx)
    except KeyError:
        return error.get("msg", "неверное значение")


def describe(error: dict) -> dict:
    """Одна ошибка проверки -> {"field": ..., "error": ...}."""
    return {"field": error_field(error.get("loc", ())), "error": russian_message(error)}


def describe_all(errors) -> list[dict]:
    """Все ошибки проверки -> список {"field": ..., "error": ...} в том же порядке."""
    return [describe(error) for error in errors]


def is_json_error(errors) -> bool:
    """True, если тело запроса вообще не удалось разобрать как JSON (тогда ответ 400, а не 422)."""
    return any(error.get("type") == "json_invalid" for error in errors)


def http_error_text(detail, method: str) -> str:
    """Текст для HTTPException: стандартные английские тексты FastAPI заменяются русскими."""
    template = HTTP_MESSAGES.get(str(detail))
    if template is None:
        return str(detail)
    return template.format(method=method)
