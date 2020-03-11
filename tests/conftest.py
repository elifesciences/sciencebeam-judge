import logging

import pytest


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logging.basicConfig(level='WARNING')
    for name in ['tests', 'sciencebeam_judge']:
        logging.getLogger(name).setLevel('DEBUG')
