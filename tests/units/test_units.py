import pytest

import bailiwick
import bailiwick.context
import bailiwick.errors


DATA = {'data': 0}


@pytest.fixture
def simple_ctx():
    ctx = bailiwick.create_context('test', DATA)
    ctx.freeze()
    yield ctx
    del bailiwick.context._CONTEXT.get()['test']


def test_create_ctx():
    app_ctx = bailiwick.create_context('app', DATA)
    app_ctx.freeze()
    assert app_ctx['data'] == 0
    del bailiwick.context._CONTEXT.get()['app']


def test_error_creating_created_ctx(simple_ctx):
    with pytest.raises(bailiwick.errors.DuplicateContext):
        new_test_ctx = bailiwick.create_context('test')


def test_get_ctx(simple_ctx):
    ctx = bailiwick.get_context('test')
    assert ctx is simple_ctx
    assert ctx['data'] == 0


def test_immutable():
    pass


