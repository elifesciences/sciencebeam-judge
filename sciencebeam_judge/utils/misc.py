import re


def remove_dot_after_initials(person_name: str) -> str:
    return re.sub(
        r'([A-Z])\.\s?',
        r'\1 ',
        person_name
    )


def remove_space_between_initials(person_name: str) -> str:
    return re.sub(
        r'(?<=[A-Z])(\s)(?=[A-Z]\b)',
        r'',
        person_name
    )


def normalize_person_name(person_name: str) -> str:
    return remove_space_between_initials(
        remove_dot_after_initials(person_name)
    )
