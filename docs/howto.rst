Look to py:mod:`decimal` for ideas on Contexts

*********************
Use cases for Context
*********************

Why use a context?

The first time I thought about contexts was when I used a library written in C.  The library was
GPGME: https://www.gnupg.org/documentation/manuals/gpgme/Contexts.html#Contexts

The context was created and configured by the user.  Then it was passed in to every cryptographic
function to give the function more information about how it should behave in this particular
instance.

According to the documentation, the context serves two functions: It allows configuring
a cryptographic operation (for instance, if you wanted the results of all your crypto operations to
be returned as ascii-armored text instead of binary data, you could turn on the ascii armor value of
the context and then every operation which used that context would know that its output should be
ascii armored.)  It also is supposed to hold intermediate state.  I don't see anything in the
function docs about what intermediate state would be held (it doesn't have a streaming interface,
for instance, so it isn't holding on to intermediate data while verifying data)

Another use of a context: An arbitrary data structure that can be passed into functions:
https://marshmallow.readthedocs.io/en/stable/why.html#context-aware-serialization

I've only used the configuration portion.  It seemed like instead of passing explicit parameters, you
would create a context with the settings you wanted and then pass that to the function.  That seemed
somewhat backwards to me: it hid the parameters at one remove.

In OOP languages, I think an object is better for this type of configuration than a context::

Comparison:

class Context():
    def __init__(self):
        self.ascii_armor = False

ctxt = Context()
ctxt.ascii_armor(True)

encrypted_text = encrypt_function(ctxt, plaintext)

class Encryptor():
    def __init__(self, ascii_armor=False):
        self.ascii_armor = ascii_armor

    def encrypt_function(self):
        pass

encryptor = Encryptor(ascii_armor=True)
encrypted = encryptor.encrypt_function(plaintext)


What about for intermediate state?

Objects can be used here as well.  The hashes in Python's hashlib module are prime examples.  For
instance:

# Theoretical API using a context
class Context():
    def __init__(self):
        self._private_data_to_hash = []

    def _add_data(self, data):
        self._private_data_to_hash.append(data)

    def _get_data(self, data):
        return ''.join(self._private_data_to_hash)

ctxt = Context(algorithm='sha1')
while open('test.txt') as f:
    for chunk in f:
        streaming_sha_function(ctxt, chunk)
hash = ctxt.get_hash()

# The actual hashlib API:
hasher = hashlib.sha1()
while open('test.txt') as f:
    for chunk in f:
        hasher.update(chunk)
hash = hasher.get_digest()


Using a Factory instead:


Case study: the Decimal API:

Python has a Decimal class in the stdlib.  This is based on an IBM specification which uses
a context.
https://docs.python.org/3/library/decimal.html

The context is used to specify how precision, rounding, and errors are dealt with for arithmetic
operations and some conversion operations on Decimals.  It makes it easy to do the following:
* Set a policy for performing arithmetic operations once and using it throughout the program. (via
  a thread global)
* Allowing a different policy for a specific call (via passing a context to the function)
* Allowing a different policy for a section of code (via a context manager)

The flexibility of Decimal is actually because it has multiple ways of setting and using the context
(Although there's only one type of Context object, each of the use cases above use a different
method of setting the context for the operation.)

If you want to make changes to the defaults, you have to create a Context object.  The Context
object is just a lightweight data storage structure.  It has no logic of its own.

Why is a context preferred here?  The desire to use operators.  We can't store the defaults on the
decimal object because the context is actually for performing binary operations.

So, for instance, you figure out that a = 1/3 with precision 100.  By setting the precision on 1.  But
then you have a second step of a / b and want a final answer with only precision of 10.  You'd have
to create a new a or change the precision of a.  Conceptually, this is about the precision of
resultants, not the precision of the Decimal itself.

The factory object would work if you create an object which performs arithmetic on Decimal Objects
and returns new Decimals:

class DecimalOp:
    def __init__(self, precision=None):
        if precision is None:
            self.precision = _global_precision_default
        else:
            self.precision = precision

op = DecimalOp(precision=3)
print(repr(DecimalOp.divide(1, 3)))
Decimal('0.333')

but it means we can't use operators to succinctly express the arithmetic operations.  (ie: we lose
the ability to do :code:`Decimal(1) / Decimal(3)`.  So it ends up being clunkier than the
context-driven API.


In any language, a configurable Factory can replace a Context.

For instance, the Python decimal class uses a context for constructing Decimals.  However,
a DecimalFactory class could do the same thing.

Contexts can still be useful for global values


What kind of data goes in a Context?
====================================

How does context data differ from global constants?
---------------------------------------------------

Globals hold values that are useful throughout your program.  They should only be used for things
which are constant to mitigate many of the problems with globals.  Putting them in a namespace (in
Python, a python module is typically used to create a namespace)::

    # File: constants.py
    DEFAULT_USERNAME = 'root'

    # File: program.py
    from . import constants as C

    print(sudo(command=['whooami'], username=C.DEFAULT_USERNAME))


Contexts are similar to globals as they hold things that may be useful throughout your program.
Holding values that are constant for a subsection of a program.  However, the values don't have to
be constant for the life of the program.  For instance, a program could initialize some data from an
external source and then save them into a context::

    # File: program.py
    import argparse
    from . import constants as C

    def parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--username', default=C.DEFAULT_USERNAME)
        return parser.parser_args(args)


    ctx_data = {'cli_args': parse_args(sys.argv[1:]),
                'password': getpass.getpass('password')}
    set_ctx(ctx_data)


Global Defaults
===============

::
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', action='store', dest='data', type='str')

    args = parser.parse_args(['test-case.py', '--data', 'this is a test'])


    from context import ContextData, set_global_context
    ctx_data = ContextData.make_context_data({'cli_args': args})

    set_global_context(ctx_data)


Using a Schema
~~~~~~~~~~~~~~

::
    import voluptuous as v
    from context import ContextData

    ctx_data = ContextData({'cli_args': sys.argv[1:],
                            'some_settable_data': 'this is a test'})
    ctx_data.freeze()
    with ctx_data.MakeContext() as ctx:




Context API

* Use a context manager
* thread-safe

