import logging
from pathlib import Path

import pytest
from py._path.local import LocalPath


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logging.basicConfig(level='WARNING')
    for name in ['tests', 'sciencebeam_judge']:
        logging.getLogger(name).setLevel('DEBUG')


@pytest.fixture
def temp_dir(tmpdir: LocalPath):
    # convert to standard Path
    return Path(str(tmpdir))
