from typing import List


class PlusMinus:
    PLUS = '+'
    MINUS = '-'


PLUS_OR_MINUS = {PlusMinus.PLUS, PlusMinus.MINUS}


def comma_separated_str_to_list(s: str) -> List[str]:
    s = s.strip()
    if not s:
        return []
    return [item.strip() for item in s.split(',')]


def plus_minus_comma_separated_str_to_list(s: str, default_value: List[str]) -> List[str]:
    user_list = comma_separated_str_to_list(s)
    if not user_list or not user_list[0] or user_list[0][0] not in PLUS_OR_MINUS:
        return user_list
    result = default_value.copy()
    mode = None
    for user_item in user_list:
        if not user_item:
            continue
        if user_item[0] in PLUS_OR_MINUS:
            mode = user_item[0]
            value = user_item[1:]
        else:
            value = user_item
        if mode == PlusMinus.PLUS:
            result.append(value)
        if mode == PlusMinus.MINUS:
            result.remove(value)
    return result
