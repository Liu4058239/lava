import logging
import os
import sys

from twisted.internet import defer, reactor

from lava_scheduler_daemon.service import BoardSet
from lava_scheduler_daemon.config import get_config

from lava_scheduler_daemon.dbjobsource import DatabaseJobSource

def daemon_main():
    source = DatabaseJobSource()

    if sys.argv[1:] == ['--use-fake']:
        dispatcher = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'fake-dispatcher')
    elif sys.argv[1:2] == ['--dispatcher'] and len(sys.argv) == 3:
        dispatcher = sys.argv[2]
    elif sys.argv[1:]:
        print >>sys.stderr, "invalid options %r" % sys.argv[1:]
        sys.exit(1)
    else:
        dispatcher = 'lava-dispatch'

    service = BoardSet(source, dispatcher, reactor)
    reactor.callWhenRunning(service.startService)

    logger = logging.getLogger('')
    config = get_config('logging')
    level = config.get("logging", "level")
    destination = config.get("logging", 'destination', None)
    if destination == '-':
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(destination)
    handler.setFormatter(
        logging.Formatter("[%(levelname)s] [%(name)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level))

    reactor.run()


def monitor_main():
    #source = DatabaseJobSource()
    d = defer.Deferred()
    d.addCallback(lambda result:reactor.stop())
    reactor.callWhenRunning(d.callback, None)
    reactor.run()
