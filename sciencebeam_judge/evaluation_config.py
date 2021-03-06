from typing import Dict, List

from sciencebeam_utils.utils.string import parse_list

from .utils.string import parse_dict
from .utils.config import parse_config_as_dict


def parse_evaluation_config(filename_or_fp) -> Dict[str, Dict[str, str]]:
    return parse_config_as_dict(filename_or_fp)


def parse_scoring_type_overrides(
        scoring_type_overrides_str: str) -> Dict[str, List[str]]:
    return {
        key: parse_list(value)
        for key, value in parse_dict(scoring_type_overrides_str).items()
    }


def get_scoring_types_by_field_map_from_config(
        config_map: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    scoring_type_config = config_map.get('scoring_type', {})
    return {
        key: parse_list(value)
        for key, value in scoring_type_config.items()
    }
