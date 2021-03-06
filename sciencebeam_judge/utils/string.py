from typing import Dict, Tuple


def parse_key_value(expr: str) -> Tuple[str, str]:
    key, value = expr.split('=', maxsplit=1)
    return key.strip(), value.strip()


def parse_dict(expr: str, delimiter: str = '|') -> Dict[str, str]:
    if not expr:
        return {}
    d = {}
    for fragment in expr.split(delimiter):
        key, value = parse_key_value(fragment)
        d[key] = value
    return d
