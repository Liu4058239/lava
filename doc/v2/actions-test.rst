.. _test_action:

Test Action Reference
#####################

The pipeline has retained compatibility with respect to the content of
Lava-Test-Shell Test Definitions although the submission format has changed:

#. The :ref:`test_action` will **never** boot the device - a :ref:`boot_action`
   **must** be specified. Multiple test operations need to be specified as
   multiple definitions listed within the same test block.

#. The LAVA support scripts are prepared by the :ref:`deploy_action` action
   and the same scripts will be used for all test definitions until another
   ``deploy`` block is encountered.

::

  - test:
     failure_retry: 3

:ref:`test_action_definitions` are used for POSIX compliant operating
systems on the DUT. The deployed system is expected to support a POSIX
shell environment (``/bin/ash``, ``/bin/dash`` or ``/bin/bash`` are the
most common) so that LAVA can execute the LAVA Test Shell Helper
scripts.

:ref:`monitor_test_action` are used for devices which have no POSIX
shell and start the test immediately, for example IoT boards.

Currently, there is no support for executing arbitrary commands on DUTs
which cannot offer a full POSIX environment. This is being investigated
for a future release.

.. seealso:: :ref:`lava_test_helpers`

.. contents::
   :backlinks: top

.. index:: test action definitions (POSIX)

.. _test_action_definitions:

Definitions
***********

repository
==========

A publicly readable repository location.

from
====

The type of the repository is **not** guessed, it **must** be specified
explicitly. Support is available for ``bzr`` and ``git``. Support is planned
for ``url`` and ``tar``.

git
---

A remote git repository which needs to be cloned by the dispatcher.

inline
------

A simple test definition present in the same file as the job submission,
instead of from a separate file or VCS repository. This allows tests to be run
based on a single file. When combined with ``file://`` URLs to the ``deploy``
parameters, this allows tests to run without needing external access. See
:ref:`inline_test_definition_example`.

path
----

The path within that repository to the YAML file containing the test
definition.

name
----

(required) - replaces the name from the YAML.

params
------

(optional): Pass parameters to the Lava Test Shell Definition. The format is a
YAML dictionary - the key is the name of the variable to be made available to
the test shell, the value is the value of that variable.

.. code-block:: yaml

 definitions:
     - repository: https://git.linaro.org/lava-team/hacking-session.git
       from: git
       path: hacking-session-debian.yaml
       name: hacking
       params:
        IRC_USER: ""
        PUB_KEY: ""

.. code-block:: yaml

     definitions:
         - repository: git://git.linaro.org/lava-team/lava-functional-tests.git
           from: git
           path: lava-test-shell/smoke-tests-basic.yaml
           name: smoke-tests
         - repository: https://git.linaro.org/lava-team/lava-functional-tests.git
           from: git
           path: lava-test-shell/single-node/singlenode03.yaml
           name: singlenode-advanced

Skipping elements of test definitions
=====================================

When a single test definition is to be used across multiple deployment types
(e.g. Debian and OpenEmbedded), it may become necessary to only perform certain
actions within that definition in specific jobs. The ``skip_install`` support
has been migrated from V1 for compatibility. Other methods of optimising test
definitions for specific deployments may be implemented in V2 later.

The available steps which can be (individually) skipped are:

deps
----

skip running ``lava-install-packages`` for the ``deps:`` list of the
``install:`` section of the definition.

keys
----

skip running ``lava-add-keys`` for the ``keys:`` list of the ``install:``
section of the definition.

sources
-------

skip running ``lava-add-sources`` for the ``sources:`` list of the ``install:``
section of the definition.

steps
-----

skip running any of the ``steps:``of the ``install:`` section of the
definition.

all
---

identical to ``['deps', 'keys', 'sources', 'steps']``

Example syntax:

.. code-block:: yaml

 - test:
     failure_retry: 3
     name: kvm-basic-singlenode
     timeout:
       minutes: 5
     definitions:
       - repository: git://git.linaro.org/lava-team/lava-functional-tests.git
         from: git
         path: lava-test-shell/smoke-tests-basic.yaml
         name: smoke-tests
       - repository: http://git.linaro.org/lava-team/lava-functional-tests.git
         skip_install:
         - all
         from: git
         path: lava-test-shell/single-node/singlenode03.yaml
         name: singlenode-advanced

The following will skip dependency installation and key addition in
the same definition:

.. code-block:: yaml

 - test:
     failure_retry: 3
     name: kvm-basic-singlenode
     timeout:
       minutes: 5
     definitions:
       - repository: git://git.linaro.org/lava-team/lava-functional-tests.git
         from: git
         path: lava-test-shell/smoke-tests-basic.yaml
         name: smoke-tests
       - repository: http://git.linaro.org/lava-team/lava-functional-tests.git
         skip_install:
         - deps
         - keys
         from: git
         path: lava-test-shell/single-node/singlenode03.yaml
         name: singlenode-advanced

.. _inline_test_definition_example:

Inline test definition example
==============================

https://git.lavasoftware.org/lava/lava/blob/master/lava_dispatcher/test/sample_jobs/kvm-inline.yaml

.. code-block:: yaml

    - test:
        failure_retry: 3
        name: kvm-basic-singlenode  # is not present, use "test $N"
        definitions:
            - repository:
                metadata:
                    format: Lava-Test Test Definition 1.0
                    name: smoke-tests-basic
                    description: "Basic system test command for Linaro Ubuntu images"
                    os:
                        - ubuntu
                    scope:
                        - functional
                    devices:
                        - panda
                        - panda-es
                        - arndale
                        - vexpress-a9
                        - vexpress-tc2
                run:
                    steps:
                        - lava-test-case linux-INLINE-pwd --shell pwd
                        - lava-test-case linux-INLINE-uname --shell uname -a
                        - lava-test-case linux-INLINE-vmstat --shell vmstat
                        - lava-test-case linux-INLINE-ifconfig --shell ifconfig -a
                        - lava-test-case linux-INLINE-lscpu --shell lscpu
                        - lava-test-case linux-INLINE-lsusb --shell lsusb
                        - lava-test-case linux-INLINE-lsb_release --shell lsb_release -a
              from: inline
              name: smoke-tests-inline
              path: inline/smoke-tests-basic.yaml


Additional support
==================

The V2 dispatcher supports some additional elements in Lava Test Shell which
will not be supported in the older V1 dispatcher.

Result checks
-------------

LAVA collects results from internal operations as well as from the submitted
test definitions, these form the ``lava`` test suite results. The full set of
results for a job are available at:

.. code-block:: none

 results/1234

LAVA records when a submitted test definition starts execution on the test
device. If the number of test definitions which started is not the same as the
number of test definitions submitted (allowing for the ``lava`` test suite
results), a warning will be displayed on this page.

TestSets
--------

A TestSet is a group of lava test cases which will be collated within the LAVA
Results. This allows queries to look at a set of related test cases within a
single definition.

.. code-block:: yaml

  name: testset-def
    run:
        steps:
            - lava-test-set start first_set
            - lava-test-case date --shell ntpdate-debian
            - ls /
            - lava-test-case mount --shell mount
            - lava-test-set stop
            - lava-test-case uname --shell uname -a

This results in the ``date`` and ``mount`` test cases being included into a
``first_set`` TestSet, independent of other test cases. The TestSet is
concluded with the ``lava-test-set stop`` command, meaning that the ``uname``
test case has no test set, providing a structure like:

.. code-block:: yaml

 results:
   first_set:
     date: pass
     mount: pass
   uname: pass

.. code-block:: python

 {'results': {'first_set': {'date': 'pass', 'mount': 'pass'}, 'uname': 'pass'}}

Each TestSet name must be valid as a URL, which is consistent with the
requirements for test definition names and test case names in the V1
dispatcher.

For TestJob ``1234``, the ``uname`` test case would appear as:

.. code-block:: none

 results/1234/testset-def/uname

The ``date`` and ``mount`` test cases are referenced via the TestSet:

.. code-block:: none

 results/1234/testset-def/first_set/date
 results/1234/testset-def/first_set/mount

A single test definition can start and stop different TestSets in sequence, as
long as the name of each TestSet is unique for that test definition.

.. index:: test action monitors

.. _monitor_test_action:

Monitors
********

Test jobs using Monitors **must**:

#. Be carefully designed to automatically execute after boot.

#. Emit a unique ``start`` string:

   #. Only once per boot operation.
   #. Before any test operation starts.

#. Emit a unique ``end`` string:

   #. Only once per boot operation.
   #. After all test operations have completed.

#. Provide a regular expression which matches all expected test output
   and maps the output to results **without** leading to excessively
   long test case names.

``start`` and ``end`` strings will match part of a line but make sure
that each string is long enough that it can only match once per boot.

If ``start`` does not match, the job will timeout with no results.

If ``end`` does not match, the job will timeout but the results (of
the current boot) will already have been reported.

name
====

The name of the :ref:`test suite <results_test_suite>`.

.. code-block:: yaml

 - name: tests
      start: BOOTING ZEPHYR
      end: PROJECT EXECUTION SUCCESSFUL
      pattern: '(?P<test_case_id>\d+ *- [^-]+) (?P<measurement>\d+) tcs = [0-9]+ nsec'
      fixupdict:
        PASS: pass
        FAIL: fail

If the device output is of the form:

.. code-block:: none

 ***** BOOTING ZEPHYR OS v1.7.99 - BUILD: Apr 18 2018 10:00:55 *****
 |-----------------------------------------------------------------------------|
 |                            Latency Benchmark                                |
 |-----------------------------------------------------------------------------|
 |  tcs = timer clock cycles: 1 tcs is 12 nsec                                 |
 |-----------------------------------------------------------------------------|
 | 1 - Measure time to switch from ISR back to interrupted thread              |
 | switching time is 107 tcs = 1337 nsec                                       |
 |-----------------------------------------------------------------------------|

 ...

 PROJECT EXECUTION SUCCESSFUL

The above regular expression can result in test case names like:

.. code-block:: none

 1_measure_time_to_switch_from_isr_back_to_interrupted_thread_switching_time_is

The raw data will be logged as:

.. code-block:: none

 test_case_id: 1 - Measure time to switch from ISR back to interrupted thread              |
 | switching time is

.. caution:: Notice how the regular expression has not closed the match
   at the end of the "line" but has continued on to the first
   non-matching character. The test case name then concatenates all
   whitespace and invalid characters to a single underscore.

.. code-block:: python

 r'(?P<test_case_id>\d+ *- [^-]+) (?P<measurement>\d+) tcs = [0-9]+ nsec'

The test_case_id will be formed from the match of the expression ``\d+
*- [^-]+`` followed by a single space - but **only** if the rest of the
expression matches as well.

The measurement will be taken from the match of the expression ``\d+``
preceded by a single space and followed by the **exact** string ``tcs =
`` which itself must be followed by a number of digits, then a single
space and finally the **exact** string ``nsec`` - but only if the rest
of the expression also matches.

.. seealso:: `Regular Expression HOWTO for Python3 <https://docs.python.org/3/howto/regex.html>`_
