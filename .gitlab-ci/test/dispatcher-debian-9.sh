#!/bin/sh

set -e

if [ "$1" = "setup" ]
then
  set -x
  DEPS=$(./share/requires.py -p lava-dispatcher -d debian -s stretch -n)
  apt-get install --no-install-recommends --yes $DEPS
  DEPS=$(./share/requires.py -p lava-dispatcher -d debian -s stretch-backports -n)
  apt-get install --no-install-recommends --yes -t stretch-backports $DEPS
  DEPS=$(./share/requires.py -p lava-dispatcher -d debian -s stretch -n -u)
  apt-get install --no-install-recommends --yes $DEPS
  DEPS=$(./share/requires.py -p lava-dispatcher -d debian -s stretch-backports -n -u)
  apt-get install --no-install-recommends --yes -t stretch-backports $DEPS
else
  set -x
  PYTHONPATH=. py.test-3 --cache-clear -v --junitxml=dispatcher.xml lava_dispatcher/test
fi
