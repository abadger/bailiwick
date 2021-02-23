# coding: utf-8
# Author: Toshio Kuratomi <a.badger@gmail.com>
# License: LGPLv3+
# Copyright: Toshio Kuratomi, 2021

class DuplicateContext(Exception):
    """Tried to create a context that already exists."""


class MustBeFrozen(Exception):
    """An operation on a :class:`bailiwick.context.ContextDict` requires it to be frozen."""
