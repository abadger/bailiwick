import pytest

import bailiwick.collections as bc
import bailiwick.errors


def _create_test_dict():
    test_cases = []
    case = {'one': 1}
    result = bc.ContextDict(case)
    result._frozen = True
    test_cases.append((case, result))

    case = bc.ContextDict({'one': 1, 'dict': {1: 'one'}})
    case._frozen = True
    subresult = bc.ContextDict({1: 'one'})
    subresult._frozen = True
    result = bc.ContextDict({'one': 1, 'dict': subresult})
    result._frozen = True
    test_cases.append((case, result))

    return test_cases


def _create_test_data():
    test_cases = []

    case = {'one': [1, {2, 'two'}, {'three': 3}, [4, 5]]}
    subresult = bc.ContextDict({'three': 3})
    subresult._frozen = True
    result = bc.ContextDict({'one': (1, frozenset((2, 'two')), subresult, (4, 5))})
    result._frozen = True
    test_cases.append((case, result))

    case = 1
    result = 1
    test_cases.append((case, result))

    return test_cases


TEST_DATA = _create_test_data()

TEST_DICT = _create_test_dict()

TEST_SEQUENCE = (
    ([1, 'two', 3.0], (1, 'two', 3.0)),
    ((1, 'two', 3.0), (1, 'two', 3.0)),
    ((1, 'two', [3.0, b'four', [5, 6]]), (1, 'two', (3.0, b'four', (5, 6)))),
)

TEST_SET = (
    ({'zoo', 'elephant', 'giraffe'}, frozenset(('zoo', 'elephant', 'giraffe'))),
    (frozenset((1, 2, 3)), frozenset((1, 2, 3))),
    ({1, frozenset((2, 3))}, frozenset((1, frozenset((2, 3))))),
)


@pytest.fixture
def default_freezer():
    return bc.DefaultFreezer()


class TestIndividualFreezers:
    def test_string_freezer_string(self):
        assert bc.string_freezer('test') == 'test'

    def test_string_freezer_other(self):
        with pytest.raises(bc.FreezeRuleDoesNotMatch):
            assert bc.string_freezer(b'test') == 1

    def test_bytes_freezer_bytes(self):
        assert bc.bytes_freezer(b'test') == b'test'

    def test_bytes_freezer_other(self):
        with pytest.raises(bc.FreezeRuleDoesNotMatch):
            assert bc.bytes_freezer('test') == 1

    def test_identity_freezer_scalar(self):
        assert bc.identity_freezer('test') == 'test'

    def test_identity_freezer_container(self):
        assert bc.identity_freezer([1, 2, {'one': 1}, 3]) == [1, 2, {'one': 1}, 3]


class TestDefaultFreezer:
    def test_constructor_default(self):
        freezer = bc.DefaultFreezer()

        assert freezer.pre_rules == ()
        assert len(freezer._rules) > 0
        assert freezer.post_rules == ()

    def test_constructor_with_rules(self):
        freezer = bc.DefaultFreezer(pre_rules=[bc.identity_freezer],
                                    post_rules=[bc.string_freezer, bc.bytes_freezer])

        assert freezer.pre_rules == [bc.identity_freezer]
        assert len(freezer._rules) > 0
        assert freezer.post_rules == [bc.string_freezer, bc.bytes_freezer]

    @pytest.mark.parametrize('obj, expected', TEST_DICT)
    def test_mapping_freezer(self, obj, expected, default_freezer):
        assert default_freezer.mapping_freezer(obj) == expected

    def test_mapping_freezer_not_map(self, default_freezer):
        with pytest.raises(bc.FreezeRuleDoesNotMatch):
            default_freezer.mapping_freezer(['not a map'])

    @pytest.mark.parametrize('obj, expected', TEST_SEQUENCE)
    def test_sequence_freezer(self, obj, expected, default_freezer):
        assert default_freezer.sequence_freezer(obj) == expected

    def test_sequence_freezer_not_sequence(self, default_freezer):
        with pytest.raises(bc.FreezeRuleDoesNotMatch):
            default_freezer.sequence_freezer({1, 2, 3})

    @pytest.mark.parametrize('obj, expected', TEST_SET)
    def test_set_freezer(self, obj, expected, default_freezer):
        assert default_freezer.set_freezer(obj) == expected

    def test_set_freezer_not_set(self, default_freezer):
        with pytest.raises(bc.FreezeRuleDoesNotMatch):
            default_freezer.set_freezer(['not a set'])


@pytest.mark.parametrize('obj, expected', TEST_DATA)
def test_calling_default_freezer(obj, expected, default_freezer):
    assert default_freezer(obj) == expected
