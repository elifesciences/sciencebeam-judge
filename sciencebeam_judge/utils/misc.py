import regex


# Note: `\p{Lu}` is refering to the upper case character class

def remove_dot_after_initials(person_name: str) -> str:
    return regex.sub(
        r'([\p{Lu}])\.\s?',
        r'\1 ',
        person_name
    ).strip()


def remove_space_between_initials(person_name: str) -> str:
    return regex.sub(
        r'(?<=[\p{Lu}])(\s)(?=[\p{Lu}]\b)',
        r'',
        person_name
    )


def normalize_person_name(person_name: str) -> str:
    return remove_space_between_initials(
        remove_dot_after_initials(person_name)
    )
