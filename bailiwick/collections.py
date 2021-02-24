# coding: utf-8
# Author: Toshio Kuratomi <a.badger@gmail.com>
# License: LGPLv3+
# Copyright: Toshio Kuratomi, 2021

import typing as t

from collections.abc import Container, Mapping, Sequence, Set
from itertools import chain

from .errors import MustBeFrozen


class FreezeRuleDoesNotMatch(Exception):
    """Freezers raise this if a rule does not match."""


def string_freezer(obj: t.Any) -> str:
    if not isinstance(obj, str):
        raise FreezeRuleDoesNotMatch
    return obj


def bytes_freezer(obj: t.Any) -> bytes:
    if not isinstance(obj, bytes):
        raise FreezeRuleDoesNotMatch
    return obj


def identity_freezer(obj: t.Any) -> t.Any:
    return obj


class DefaultFreezer:
    def __init__(self, pre_rules: t.Optional[t.Sequence] = None,
                 post_rules: t.Optional[t.Sequence] = None) -> None:
        self.pre_rules: t.Sequence = pre_rules or tuple()
        self._rules: t.Sequence = (string_freezer, bytes_freezer, self.mapping_freezer,
                                   self.sequence_freezer, self.set_freezer)

        self.post_rules: t.Sequence = post_rules or tuple()

    def mapping_freezer(self, obj: t.Any) -> 'ContextDict':
        if not isinstance(obj, Mapping):
            raise FreezeRuleDoesNotMatch

        new_dict = {}
        for key, value in new_dict.items():
            if isinstance(value, Container):
                value = self.__call__(value)
            new_dict[key] = value

        new_dict = ContextDict.new(new_dict, freezer=self)
        new_dict._frozen = True
        return new_dict

    def _make_contained_containers_immutable(self, obj: t.Union[Sequence, Set]) -> t.List:
        new_list = []
        for value in obj:
            if isinstance(value, Container):
                value = self.__call__(value)
            new_list.append(value)
        return new_list

    def sequence_freezer(self, obj: t.Any) -> tuple:
        if not isinstance(obj, Sequence):
            raise FreezeRuleDoesNotMatch

        return tuple(self._make_contained_containers_immutable(obj))

    def set_freezer(self, obj: t.Any) -> frozenset:
        if not isinstance(obj, Set):
            raise FreezeRuleDoesNotMatch

        return frozenset(self._make_contained_containers_immutable(obj))

    def __call__(self, obj: t.Any) -> t.Any:
        """Recursively convert a container and objects inside into immutable data types."""
        for rule in chain(self.pre_rules, self._rules, self.post_rules):
            try:
                return rule(obj)
            except FreezeRuleDoesNotMatch:
                continue

        return obj


class ContextDict(Mapping):
    def __init__(self, *args, **kwargs) -> None:
        self._store: t.Mapping = dict(*args, **kwargs)
        self._must_be_frozen: bool = True
        self.freezer: t.Callable[[t.Any], t.Any] = DefaultFreezer()
        self._frozen: bool = False

    @classmethod
    def new(cls, ctx_data: t.Optional[t.Mapping] = None,
            must_be_frozen: bool = True,
            freezer: t.Optional[t.Callable[[t.Any], t.Any]] = None) -> 'ContextDict':

        if ctx_data is None:
            ctx_data = {}

        ctx = ContextDict(ctx_data)

        if freezer is not None:
            ctx.freezer = freezer

        ctx._must_be_frozen = must_be_frozen
        ctx._frozen = False

        return ctx

    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        self.freezer(self._store)
        self._frozen = True

    def __getitem__(self, key: t.Hashable) -> t.Any:
        if not self.frozen:
            if self._must_be_frozen:
                raise MustBeFrozen('This ContextDict must be frozen before accessing'
                                   ' its members.')
        return self._store[key]

    def __iter__(self) -> t.Any:
        return self._store.__iter__()

    def __len__(self) -> int:
        return self._store.__len__()

    def __hash__(self) -> int:
        if self.frozen:
            return hash(frozenset(self.items()))
        raise MustBeFrozen('A ContextDict must be frozen before it can be hashed')

    def __eq__(self, other: t.Any) -> bool:
        try:
            if self.__hash__() == hash(other):
                return True
        except TypeError:
            pass

        return False

    def __repr__(self) -> str:
        return (f'ContextDict({repr(self._store)}, must_be_frozen={self._must_be_frozen},'
                f' freezer={self.freezer})')

    def union(self, overriding_mapping: t.Mapping) -> 'ContextDict':
        """
        Create a new ContextDict as a combination of the original and an overriding_mapping.

        .. note:: The new context is unfrozen but only entries in the overriding mapping could be
            mutable.
        """
        new_ctx = ContextDict(self._store, **overriding_mapping)
        new_ctx._must_be_frozen = self._must_be_frozen
        new_ctx.freezer = self.freezer
        return new_ctx
