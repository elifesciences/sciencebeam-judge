from typing import Dict, List, Union

from .utils.config import parse_config_as_dict


def parse_evaluation_config(filename_or_fp) -> Dict[str, Dict[str, str]]:
    return parse_config_as_dict(filename_or_fp)


def get_scoring_type_by_field_map_from_config(
        config_map: Dict[str, Dict[str, str]]) -> Dict[str, Union[str, List[str]]]:
    return config_map.get('scoring_type', {})
