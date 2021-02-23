# coding: utf-8
# Author: Toshio Kuratomi <a.badger@gmail.com>
# License: LGPLv3+
# Copyright: Toshio Kuratomi, 2021

import contextvars
import typing as t

from collections.abc import Mapping

from .errors import DuplicateContext, MustBeFrozen


_context = contextvars.ContextVar('_bailiwick_contexts')
_context.set({})


def default_freezer(obj):
    return obj


class ContextDict(Mapping):
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self._must_be_frozen = True
        self.freezer = default_freezer
        self._frozen = False

    @classmethod
    def new(cls, ctx_data: t.Mapping,
            must_be_frozen: bool = True,
            freezer: t.Callable = default_freezer):
        ctx = ContextDict(ctx_data)
        ctx._must_be_frozen = must_be_frozen
        ctx.freezer = freezer
        ctx._frozen = False
        return ctx

    @property
    def frozen(self):
        return self._frozen

    def freeze(self):
        self.freezer(self._store)
        self._frozen = True

    def __getitem__(self, key):
        if not self.frozen:
            if self._must_be_frozen:
                raise MustBeFrozen('This ContextDict must be frozen before accessing'
                                   ' its members.')
        return self._store[key]

    def __iter__(self):
        return self._store.__iter__()

    def __len__(self):
        return self._store.__len__()

    def __hash__(self):
        if self.frozen:
            return hash(frozenset(self.items()))
        raise MustBeFrozen('A ContextDict must be frozen before it can be hashed')

    def __eq__(self, other):
        try:
            if self.__hash__() == hash(other):
                return True
        except TypeError:
            pass

        return False

    def __repr__(self):
        return (f'ContextDict({repr(self._store)}, must_be_frozen={self._must_be_frozen},'
                f' freezer={self.freezer})')

    def union(self, overriding_mapping):
        """
        Create a new ContextDict as a combination of the original and an overriding_mapping.

        .. note:: The new context is unfrozen but only entries in the overriding mapping could be
            mutable.
        """
        new_ctx = ContextDict(self._store, **overriding_mapping)
        new_ctx._must_be_frozen = self._must_be_frozen
        new_ctx.freezer = self.freezer
        new_ctx.frozen = False
        return new_ctx


def create_context(ctx_name: str, ctx_data: t.Optional[t.Mapping] = None,
                   must_be_frozen: bool = True,
                   freezer: t.Callable = default_freezer) -> ContextDict:
    """
    Create a new context.

    :arg ctx_name: The name of the context
    :kwarg ctx_data: A Mapping of data to initialize the context with.
    :kwarg must_be_frozen: By default, contexts must be frozen before they can be used.
        Set this to False to allow mutating the context and data inside of it.
    :kwarg freezer: Function to use to make the ctx_data immutable.  This should recurse any
        containers, changing from mutable data types to immutable ones.  This can be changed to an
        identity function to disable conversion to immutable types.
    """
    current_context = _context.get('_bailiwick_contexts')
    if ctx_name in current_context:
        raise DuplicateContext(f'{ctx_name} has already been used as the name of a context.'
                               ' Choose a unique name or use get_context() if you want to'
                               ' operate on the existing context.')

    current_context[ctx_name] = ContextDict.new(ctx_data=ctx_data, must_be_frozen=must_be_frozen,
                                                freezer=freezer)

    return current_context[ctx_name]


def get_context(ctx_name: str) -> ContextDict:
    """
    Retrieve a context by name.

    :arg ctx_name: The name of the context
    """
    return _context.get('_bailiwick_contexts')[ctx_name]
