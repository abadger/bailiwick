import threading
import time

from bailiwick import context

context._local_store.ctx.freeze()

def worker(number):
    print('I am %s' % number)
    print('Start %s: %s' % (number, context._local_store.ctx['message']))
    context._local_store.ctx['message'] = 'Set from %s' % number
    print('End %s: %s' % (number, context._local_store.ctx['message']))


def with_local_context():
    new_ctx = context.Context()
    new_ctx['message'] = 'Set from a local context'
    with context.local_context(new_ctx):
        time.sleep(5)
    return


def standard():
    for i in range(0, 10):
        time.sleep(1)
        print(context.ctx['message'])


if __name__ == '__main__':
    threads = []
    t = threading.Thread(target=with_local_context)
    threads.append(t)
    t.start()
    t2 = threading.Thread(target=standard)
    threads.append(t2)
    t2.start()
