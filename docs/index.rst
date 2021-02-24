Advantages of contexts
======================

Disadvantages of contexts
=========================

What to use a context for
=========================

What not to use a context for
=============================

How to use contexts
===================

The recommended way to use contexts is to:

* Create a context for your application
* Set default values for all fields in that context
* When your program starts, read overrides from various user provided locations (command line,
  config files, the environment, etc)
* Create a new context with the user provided overrides
* Use a context manager to use the new context to override the default
* Anytime you need to use a value from the context, get it using bailiwick.get_context() and then
  retrieve the value from that.
* Never change a value in a context after startup.  If your application is such that it spawns
  separate workers which each should have their own contexts, treat it the same as program startup
  where each worker reads in its overrides and then uses the context manager to load those
  overrides.

.. code-block:: python

    # context.py
    from bailiwick import ContextDict, create_context

    # Create a context with a name
    app_ctx = create_context('library')

    # Set default values on the context
    app_ctx['timeout'] = 20
    app_ctx['retries'] = 3
    app_ctx]'proxy'] = ''
    app_ctx['server'] = 'https://localhost/'
    app_ctx['logging_config'] = {'version': '1.0',
                                 'outputs': {'stderr': {'output': 'twiggy.outputs.StreamOutput'}},
                                 'emitters': 'problems': {'level': 'WARNING',
                                                          'output_name': 'stderr'
                                                          }
                                 }

    # Freeze the context.  By default, contexts are initialized when the program starts and then
    # are made immutable for the rest of the program's life.
    app_ctx.freeze()

    # Create new contexts based on args, cfg, and other data sources
    def create_context(args, cfg):
        new_ctx = ContextDict()

        # Load the user set values from 
        new_ctx['proxy'] = args.proxy or cfg.proxy or os.environ.get('https_proxy'. '')
        new_ctx['server'] = args.server or cfg.server
        new_ctx['logging_config'] = cfg.logging_config

.. code-block:: python

    # main.py
    from . context import app_ctx


    def main():
        args = parse_args(sys.argv[1:])
        
