# coding: utf-8
# Author: Toshio Kuratomi <a.badger@gmail.com>
# License: LGPLv3+
# Copyright: Toshio Kuratomi, 2021

import contextvars
import typing as t

from .context_dict import ContextDict
from .errors import DuplicateContext


#: Storage for all of our contexts.
_CONTEXT = contextvars.ContextVar('_bailiwick_contexts')
_CONTEXT.set({})

__all__ = ('create_context', 'get_context')


def create_context(ctx_name: str, ctx_data: t.Optional[t.Mapping] = None,
                   must_be_frozen: bool = True,
                   freezer: t.Optional[t.Callable] = None) -> ContextDict:
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
    current_context = _CONTEXT.get('_bailiwick_contexts')
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
    return _CONTEXT.get('_bailiwick_contexts')[ctx_name]
