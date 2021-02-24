import pytest

import bailiwick.collections as bc
import bailiwick.errors


DATA_TUPLE = (('data', 0), (1, 'a'), ('data2', 'test'))
DATA_DICT = {'data': 0, 1: 'a', 'data2': 'test'}


@pytest.fixture
def default_freezer():
    return bc.DefaultFreezer()


class TestFreezer:
    pass
