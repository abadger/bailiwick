import re
from collections.abc import Mapping, MutableMapping

import pytest

import bailiwick.collections as bc
import bailiwick.errors


DATA_TUPLE = (('data', 0), (1, 'a'), ('data2', 'test'))
DATA_DICT = {'data': 0, 1: 'a', 'data2': 'test'}


@pytest.fixture
def ctx_dict():
    return bc.ContextDict.new(DATA_DICT)


class TestContextDictConstructor:
    def test_constructor_default(self):
        ctx_dict = bc.ContextDict()

        assert isinstance(ctx_dict, Mapping)
        assert isinstance(ctx_dict, bc.ContextDict)
        assert ctx_dict.frozen is False
        assert isinstance(ctx_dict.freezer, bc.DefaultFreezer)
        assert len(ctx_dict) == 0

    @pytest.mark.parametrize('initializer', (DATA_TUPLE, DATA_DICT))
    def test_constructor_with_initial_value(self, initializer):
        ctx_dict = bc.ContextDict(initializer)

        assert ctx_dict.frozen is False
        assert isinstance(ctx_dict.freezer, bc.DefaultFreezer)
        assert len(ctx_dict) == 3

        assert ctx_dict._store['data'] == 0
        assert ctx_dict._store[1] == 'a'
        assert ctx_dict._store['data2'] == 'test'

    def test_alt_constructor_default(self):
        ctx_dict = bc.ContextDict.new()

        assert isinstance(ctx_dict, Mapping)
        assert isinstance(ctx_dict, bc.ContextDict)
        assert ctx_dict.frozen is False
        assert isinstance(ctx_dict.freezer, bc.DefaultFreezer)
        assert len(ctx_dict) == 0

    @pytest.mark.parametrize('initializer', (DATA_TUPLE, DATA_DICT))
    def test_alt_constructor_with_initial_value(self, initializer):
        ctx_dict = bc.ContextDict.new(initializer, must_be_frozen=False)

        assert ctx_dict.frozen is False
        assert isinstance(ctx_dict.freezer, bc.DefaultFreezer)
        assert len(ctx_dict) == 3

        assert ctx_dict['data'] == 0
        assert ctx_dict[1] == 'a'
        assert ctx_dict['data2'] == 'test'


class TestContextDictFeatures:
    def test_freeze_reports_frozen(self, ctx_dict):
        assert ctx_dict.frozen is False

        ctx_dict.freeze()

        assert ctx_dict.frozen

    def test_freeze_prevents_changes(self, ctx_dict):
        ctx_dict['new'] = True

        ctx_dict.freeze()

        with pytest.raises(TypeError):
            ctx_dict['another'] = True

    def test_freeze_makes_immutable(self, ctx_dict):
        assert isinstance(ctx_dict._store, MutableMapping)

        ctx_dict.freeze()

        assert not isinstance(ctx_dict._store, MutableMapping)
        assert isinstance(ctx_dict._store, Mapping)

    def test_union_add(self, ctx_dict):
        new_dict = ctx_dict.union({'spam': 'eggs'})

        assert new_dict.frozen is False
        assert isinstance(new_dict.freezer, bc.DefaultFreezer)
        assert len(new_dict) == 4

        assert new_dict._store['data'] == 0
        assert new_dict._store[1] == 'a'
        assert new_dict._store['data2'] == 'test'
        assert new_dict._store['spam'] == 'eggs'

    def test_union_override(self, ctx_dict):
        new_dict = ctx_dict.union({'data2': False})

        assert new_dict.frozen is False
        assert isinstance(new_dict.freezer, bc.DefaultFreezer)
        assert len(new_dict) == 3

        assert new_dict._store['data'] == 0
        assert new_dict._store[1] == 'a'
        assert new_dict._store['data2'] is False

    def test_union_unfrozen(self, ctx_dict):
        ctx_dict.freeze()
        new_dict = ctx_dict.union({'spam': 'eggs', 'data2': False})

        assert new_dict.frozen is False
        assert isinstance(new_dict.freezer, bc.DefaultFreezer)
        assert len(new_dict) == 4

        assert new_dict._store['data'] == 0
        assert new_dict._store[1] == 'a'
        assert new_dict._store['data2'] is False
        assert new_dict._store['spam'] == 'eggs'


class TestMappingFeatures:
    def test_get_items_unfrozen(self, ctx_dict):
        with pytest.raises(bailiwick.errors.MustBeFrozen):
            assert ctx_dict['data'] == 0

    def test_get_items_frozen(self, ctx_dict):
        ctx_dict.freeze()
        assert ctx_dict['data'] == 0

    def test_get_items_freezing_optional(self):
        ctx_dict = bc.ContextDict.new(DATA_DICT, must_be_frozen=False)

        assert ctx_dict['data'] == 0
        ctx_dict.freeze()
        assert ctx_dict['data'] == 0

    def test_iterate(self, ctx_dict):
        results = set()
        for key in ctx_dict:
            results.add(key)

        assert results == set(DATA_DICT.keys())

    def test_len(self, ctx_dict):
        assert len(ctx_dict) == 3

        ctx_dict['another'] = 'one'

        assert len(ctx_dict) == 4

    def test_hash_frozen(self, ctx_dict):
        ctx_dict.freeze()
        assert hash(ctx_dict) == hash(frozenset(ctx_dict.items()))

    def test_hash_unfrozen(self, ctx_dict):
        with pytest.raises(bailiwick.errors.MustBeFrozen):
            hash(ctx_dict)

    def test_equality_unfrozen(self, ctx_dict):
        assert ctx_dict == DATA_DICT
        assert DATA_DICT == ctx_dict
        assert ctx_dict == bc.ContextDict(DATA_TUPLE)

    def test_equality_frozen(self, ctx_dict):
        ctx_dict.freeze()
        assert ctx_dict == DATA_DICT
        assert DATA_DICT == ctx_dict
        assert ctx_dict == bc.ContextDict(DATA_TUPLE)

    def test_repr(self, ctx_dict):
        output = repr(ctx_dict)
        print(output)

        repr_re = re.compile(r'^ContextDict\({([^}]*)}, must_be_frozen=True,'
                             r' freezer=<bailiwick.collections.DefaultFreezer'
                             r' object at 0x[^>]*>\)$')
        match = repr_re.match(output)

        assert match
        assert "'data': 0" in match.group(1)
        assert "1: 'a'" in match.group(1)
        assert "'data2': 'test'" in match.group(1)
        assert match.group(1).count(':') == 3


class TestMutableMappingFeatures:
    def test_delitem_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(TypeError):
            del ctx_dict[1]

    def test_delitem_unfrozen(self, ctx_dict):
        del ctx_dict[1]
        assert len(ctx_dict) == 2

    def test_setitem_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(TypeError):
            ctx_dict['three'] = 3

        with pytest.raises(TypeError):
            ctx_dict[1] = 'one'

    def test_setitem_unfrozen(self, ctx_dict):
        ctx_dict['three'] = 3
        ctx_dict[1] = 'one'

        assert len(ctx_dict) == 4
        assert ctx_dict._store[1] == 'one'
        assert ctx_dict._store['three'] == 3

    def test_clear_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(AttributeError):
            ctx_dict.clear()

    def test_clear_unfrozen(self, ctx_dict):
        ctx_dict.clear()

        assert len(ctx_dict) == 0

    def test_pop_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(AttributeError):
            ctx_dict.pop()

    def test_pop_unfrozen(self, ctx_dict):
        assert ctx_dict.pop(1) == 'a'
        assert len(ctx_dict) == 2
        assert 1 not in ctx_dict._store

    def test_popitem_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(AttributeError):
            ctx_dict.popitem()

    def test_popitem_unfrozen(self, ctx_dict):
        key, value = ctx_dict.popitem()

        assert len(ctx_dict) == 2
        assert key not in ctx_dict._store
        assert key in DATA_DICT
        assert DATA_DICT[key] == value

    def test_setdefault_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(AttributeError):
            ctx_dict.setdefault('three', 3)

    def test_setdefault_unfrozen(self, ctx_dict):
        assert ctx_dict.setdefault('three', 3) == 3
        assert ctx_dict._store['three'] == 3

        assert ctx_dict.setdefault('three', 4) == 3
        assert ctx_dict._store['three'] == 3

    def test_update_frozen(self, ctx_dict):
        ctx_dict.freeze()
        with pytest.raises(AttributeError):
            ctx_dict.update({'three': 3})

    def test_update_unfrozen(self, ctx_dict):
        ctx_dict.update({'three': 3})

        assert len(ctx_dict) == 4
        assert ctx_dict._store['three'] == 3
