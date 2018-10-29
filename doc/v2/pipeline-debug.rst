.. index:: administrator debugging, debugging V2 instance

.. _debugging_v2:

Administrator debugging
#######################

Debugging a LAVA instance
*************************

.. _debugging_components:

Components
==========

Each of these components has a service which may need to be restarted when
making changes. Each of these services are restarted when the relevant packages
are installed.

* **lava-server** - the frontend UI and admin interface. If using apache
  use ``apache2ctl restart`` when changing any of the django files, device type
  templates or lava-server settings::

   $ sudo apache2ctl restart

* **master** - the dispatcher master, controlling the slaves using ZMQ and
  scheduling jobs. The master does the pipeline validation. Restart when
  changing the dispatcher code (as the master runs the validation check using
  the dispatcher code)::

   $ sudo service lava-master restart

* **slave** - each dispatcher slave connects to the master using ZMQ and
  follows the instructions of the master, using configuration specified by the
  master. Restart is rarely needed, usually only when changing the dispatcher
  code related to ZMQ or the loghandler::

   $ sudo service lava-slave restart

The master and slave have dedicated singleton processes which should be put
into loglevel ``DEBUG`` when investigating problems.
Restart the service after editing the service file.

* **master** ``/etc/init.d/lava-master`` currently defaults to DEBUG
  log level.

* **slave** ``/etc/init.d/lava-slave`` currently defaults to DEBUG.

.. debugging_log_files:

Log files
=========

All log files use ``logrotate``, so the information you need may be in a
``log.1`` or ``log.2.gz`` file - typically up to ``log.9.gz``. Use ``zless`` or
``zgrep`` for older log files.

* **apache** - ``/var/log/apache2/lava-server.log``

* **django** - by default ``/var/log/lava-server/django.log`` contains
  errors and warnings from django.

* **master** - ``/var/log/lava-server/lava-master.log``

* **slave** - ``/var/log/lava-dispatcher/lava-slave.log``.

* **test jobs** - ``/var/lib/lava-server/default/media/job-output/``
  individual files are in a directory named after the start time of the
  corresponding job ``<year>/<month>/<day/$ID``, e.g. ``2018/08/10/1234``.
  The directory includes the validation output ``description.yaml`` and the
  full log file ``output.yaml``.

.. _debugging_cli:

Command line debugging
======================

* **lava-server** - ``sudo lava-server manage shell``.

  .. seealso:: :ref:`developer_access_to_django_shell`

* **lava-dispatcher** - The actions of ``lava-slave`` can be replicated
  on the command line. The relevant device configuration can be obtained using
  ``lava-tool``, e.g.::

   $ lava-tool get-pipeline-device-config --stdout SERVER DEVICE_HOSTNAME

  This config can then be passed to ``lava-dispatch``, in this example in a
  file named ``device.yaml``::

   $ sudo lava-dispatch --target device.yaml --output-dir /tmp/debug/ job.yaml

  Every job is validated before starting and the validate check can be run
  directly by adding the ``--validate`` option::

   $ sudo lava-dispatch --target device.yaml --validate --output-dir /tmp/debug/ job.yaml

  The job will not start when ``--validate`` is used - if validation passes,
  the complete pipeline will be described. If errors are found, these will be
  output.

.. _debugging_configuration:

Configuration files
===================

* **lava-server** - ``/etc/lava-server/settings.conf`` - restart ``apache``
  and ``lava-server`` if this is changed. Holds details for django settings
  including the authentication methods and site customisation settings.

* **jinja2 templates** - ``/etc/lava-server/dispatcher-config/device-types``
  These files are updated from ``lava_scheduler_app/tests/device-types``
  in the codebase. The syntax is YAML with jinja2 markup. Restart the
  ``lava-master`` after changing the templates.

  * to validate changes to the templates, use::

    $ /usr/share/lava-server/validate_devices.py --instance localhost

  * to validate the combination of the template with the device
    dictionary content, use::

     $ lava-tool get-pipeline-device-config --stdout SERVER DEVICE_HOSTNAME

* **device dictionaries** - ``/etc/lava-server/dispatcher-config/devices``
  These files are specific to each instance and need to be named according to
  the ``hostname``.jinja2 of the device as configured on the same instance.

.. _check_instance:

Check LAVA instance
===================

Once a LAVA instance is installed admins can check for errors and warnings on the
deployed instance using::

  $ sudo lava-server manage check --deploy

The ``check --deploy`` command uses the Django system check framework which is a
set of static checks to detect common problems and provide hints for how to fix
them.

.. seealso:: https://docs.djangoproject.com/en/dev/ref/checks/ to know more
             about Django system check framework.

LAVA sets the following values by default::

  SECURE_CONTENT_TYPE_NOSNIFF = True
  SECURE_BROWSER_XSS_FILTER = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  CSRF_COOKIE_HTTPONLY = True
  X_FRAME_OPTIONS = 'DENY'

These values can be overridden in ``/etc/lava-server/settings.conf``

The following checks are silenced and does not show any errors or warnings:

* SECURE_HSTS_SECONDS i.e., security.W004 which is documented in https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
* SECURE_SSL_REDIRECT i.e., 'security.W008' which is documented in https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect

.. note:: Admins should consult the respective Django documentation before changing these
   values to suit the requirements of each LAVA instance.

.. seealso:: :ref:`django_localhost`
