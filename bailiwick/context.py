# Create the default context at startup.  This will be used to store default values
"""
This is a generic context library


Difference between a context and any other object
=================================================

A context holds values that configure how a set of functions will run.  Why not model this with
a single object?  I think that a single object works well when the functions and values describe
a single, small enough thing.  But sometimes the values describe a multitude of things which are
only loosely linked.  When that happens, a context may be more appropriate than trying to shoehorn
the disparate pieces together.

As an example, say you had an application which performed various actions on a git repository.
Configuring the url to a git repository, any credentials needed, and information about the
repository that might be needed for writing compatible code for different versions of the repo could
all be attributes of an object representing the repository.

Now let's say that you change your application's scope to model the entire clientside of github.
Suddenly, you need to configure git repositories, credentials to log in for github services, the
commenting features of a pull request, gists, wikis, file upload, people, organizations, github
apps, configuration of webhooks, and etc.  Somethings might be common to all of the pieces of github
but other things might only apply to one and still other things might apply to a quarter or half but
not all of the github services.  Now, when this happens, you pull in information from the command
line, environment variables, and configuration files and need to push them out.


Context's relation to globals
=============================

Contexts and globals share a lot of the same ideas, pros and cons.  The context should be available
anywhere within its boundaries for easy access just as globals are available anywhere within the program.

However, globals have many drawbacks and contexts attempt to minimize the drawbacks that they can
without sacrificing what makes them good.

Shortcomings
------------

Non-locality
~~~~~~~~~~~~

When a value is defined in one place but used many function calls away, it may not be obvious what
changes in the code at use will require changes of the code at definition and vice versa.

Lack of namespacing
~~~~~~~~~~~~~~~~~~~

Thread safety
~~~~~~~~~~~~~

Stamp Coupling
~~~~~~~~~~~~~~

Reliance on one data structure with many dependent pieces of data instead of explicit enumeration of
dependencies.  This can make code harder to modify as it is unknown which of the pieces of data are
actually used by the function and which are merely there because they were a part of the data
structure.


Benefits
--------

Easy access
~~~~~~~~~~~

Globals can be reached from anywhere within a program without being passed explicitly.  This can
make code less verbose and more resistant to breaking on changes if a value needs to be passed
through a chain of many functions to get from where it is set to where it is actually used.


Separation of inputs to calculate a value and things incidental to the calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Chunksize

Retries


Some requirements
=================


Multiple context types
-----------------------

There might be more than one type of context in a program.  A library might have a context that
manages the connection to a server and the application might have its own object which manages
a processed view of the config values, for instance.

Multiple instances of a context
-------------------------------

A program or library might want to allow multiple contexts for some purpose.  For instance,
a library that abstracts actions against git repos might contain context for the git repo but 


Default Context
----------------

Setting a default context alleviates some of the problems of stamp coupling as it means that code
can merely change the data that it knows needs to be different but leave the rest to take on the default value.

"""

import contextlib
import threading
from collections.abc import Mapping
0

class ImmutableDict(Mapping):
    pass


class ContextData(Mapping):
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self.schema = None
        self.frozen = False

    @classmethod
    def create_context(cls, schema, frozen, *args, **kwargs):
        """
        Create a ContextData with the schema.  This is the preferred factory method to use to create
        the Context. It is an alternate constructor so that the regular constructor can be
        dict-compatible.
        """
        self = cls(*args, **kwargs)
        self.schema = schema
        self._frozen = frozen
        return self

    @property
    def frozen(self):
        return self._frozen

    @frozen.setter
    def frozen(self, value):
        if value:
            # TODO: Validate against schema
            # TODO: Turn store into immutable objects
            self._frozen = True
        elif self._frozen:
            raise Exception('Once frozen, a ContextData cannot be unfrozen')

    def __getitem__(self, key):
        if self._frozen:
            return self._store.ctx_data[key]
        raise Exception('Cannot get items from Context until it is frozen')

    def __setitem__(self, key, value):
        if self._frozen:
            raise Exception('Cannot assign values to Context after it is frozen')
        self._store.ctx_data[key] = value


DEFAULT_CTX_DATA = ContextData()


class Singleton(type):
    # Whenever a class has yet to be instantiated, instantiate it.
    # Otherwise use the existing instance.
    # Need to keep track of the existing instance to make this work
    def __new__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._instance = None

    def __init__(self, *args, **kwargs):
        if self._instance:
            return self._instance
        return 


class Context(Mapping, metaclass=Singleton):
    """
    This is a wierd object

    The Context object is a wrapper around threading.local().  It gives it a Mapping interface and
    a freeze method.  It's also a Singleton.  However, since the Context is a container for the
    local() store, the local store can and does differ for each thread that it is a part of.

    Why go through this?

    * We want the default Context object to be initialized and then frozen (made immutable) so that
      nothing can be changed afterwards.  This eliminates one of the problem of global objects which
      is that you can't tell where they are modified.  The modification problem can be especially
      problematic in multithreaded code where it can cause race conditions.
    * We want calling code to have the option of defining their own Context objects instead of using
      the global Context.  This is what the threading.local() achieves.  Because of that, any object
      with multiple threads of control is able to create a new context and enable it via the context
      manager interface.  Until the thread exits that interface, it will use the new context instead
      of the default context.
    * We don't want people manually messing with the threading.local() object as they might
      accidentally overwrite the local instead of putting something inside of it.
    """
    _store = threading.local()
    _default = None

    def __init__(self, new_context=None):
        if not hasattr(self._store, '_context_stack'):
            self._store.context_stack = []

        if new_context is None:
            new_context = DEFAULT_CTX_DATA
        if not new_context.frozen:
            raise Exception('Must freeze the ContextData before using it in a Context')
        self._store.new_context = new_context

    def __iter__(self):
        return self._store.context_stack[-1].__iter__()

    def __len__(self):
        return len(self._store.context_stack[-1])

    def __getitem__(self, key):
        return self._store.context_stack[-1][key]

    def __enter__(self):
        """
        Switch to the new context
        """
        self._store.context_stack.append(self._store.new_context)
        return self._store.new_context

    def __exit__(self, type_, value, traceback):
        self._store.context_stack.pop()
