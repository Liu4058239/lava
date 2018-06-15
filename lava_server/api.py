# Copyright (C) 2010, 2011 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
# Author: Michael Hudson-Doyle <michael.hudson@linaro.org>
#
# This file is part of LAVA Server.
#
# LAVA Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Server.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import sys
import yaml

from django.http import Http404

from django.core.exceptions import PermissionDenied
from lava_scheduler_app.views import get_restricted_job
from lava_scheduler_app.models import Device, DeviceType
from linaro_django_xmlrpc.models import errors, Mapper, SystemAPI

if sys.version_info[0] == 2:
    # Python 2.x
    import xmlrpclib
elif sys.version_info[0] == 3:
    # For Python 3.0 and later
    import xmlrpc.client as xmlrpclib


class LavaSystemAPI(SystemAPI):
    """
    Extend the default SystemAPI with a 'whoami' method.
    """

    def whoami(self):
        """
        Name
        ----
        `whoami` ()

        Description
        -----------
        Find the authenticated user, if any, or None.

        Arguments
        ---------
        None

        Return value
        ------------
        Name of the authenticated user, if any, or None.
        """
        if self.user:
            return self.user.username
        else:
            return None

    def version(self):
        """
        Name
        ----
        `system.version` ()

        Description
        -----------
        Return the lava-server version string

        Arguments
        ---------
        None

        Return value
        ------------
        lava-server version string
        """

        changelog = '/usr/share/doc/lava-server/changelog.Debian.gz'
        if os.path.exists(changelog):
            deb_version = subprocess.check_output((
                'dpkg-query', '-W', "-f=${Version}\n",
                "lava-server")).strip().decode('utf-8')
            return deb_version
        return ''

    # Update the integer return value when adding arguments to
    # existing functions anywhere in the XML-RPC API or
    # deleting functions.
    def api_version(self):
        """
        Name
        ----
        `system.api_version` ()

        Description
        -----------
        Return the lava-server XML-RPC API version string.
        Clients can check this string to know whether to
        use particular arguments to available functions.

        Note: For older instances which do not support this
        call in the first place, check for this call in the
        output of system.listMethods()

        if 'system.api_version' in connection.system.listMethods():
            api_version = int(connection.system.api_version())
                if api_version >= 2:
                    # safe to run the new API here.
        else:
            # use the old API

        Arguments
        ---------
        None

        Return value
        ------------
        lava-server XML-RPC API version integer
        """
        return 2


    def user_can_view_jobs(self, job_list, username=None):
        """
        Name
        ----
        user_can_view_jobs (`job_list`)

        Administrators only:
        user_can_view_jobs (`job_list`, `username`)

        Description
        -----------
        Check the access permissions on a list of jobs.
        Admins can specify a username as the second argument to run
        the query on behalf of that user.

        Arguments
        ---------
        job_list: list
            list of job ids to query
        username: string
            username of the user to query (admins only)

        Return value
        ------------
        Returns a dictionary where the key is a string of the job_id from
        the job_list, if it exists in the queried instance. The value is a boolean
        for whether the user can access that job.
        {
          '1234': True,
          '1543': False
        }
        If the job number does not exist, that job will be omitted from the
        returned dictionary.
        This function requires authentication with a username and token.

        Example
        -------
        server.system.user_can_view_jobs([1, 2, 3, 4, 99999, 4000])
        {'1': True, '4000': True, '3': True, '2': True, '4': True}

        # if using the username and token of an admin, a different user can be queried:
        server.system.user_can_view_jobs([1, 2, 3, 4, 99999, 4000], 'firstname.lastname')
        {'1': True, '4000': False, '3': True, '2': True, '4': False}

        """
        self._authenticate()
        if not isinstance(job_list, list):
            raise xmlrpclib.Fault(
                errors.BAD_REQUEST,
                "job list argument must be a list")
        username = self._switch_user(username)
        retval = {}
        for job_id in job_list:
            try:
                get_restricted_job(username, job_id)
            except Http404:
                continue
            except PermissionDenied:
                retval[str(job_id)] = False
                continue
            retval[str(job_id)] = True
        return retval

    def user_can_view_bundles(self, bundle_list, username=None):
        """
        Name
        ----
        user_can_view_bundles (`bundle_list`)

        Removal of V1 support
        --------------------
        This function has been disabled. It is retained as a stub for older
        versions of clients. Please update your tool to use LAVA V2.

        """
        return False

    def user_can_view_devices(self, device_list, username=None):
        """
        Name
        ----
        user_can_view_devices (`device_list`)

        Administrators only:
        user_can_view_devices (`device_list`, `username`)

        Description
        -----------
        Check the access permissions on a list of devices.
        Admins can specify a username as the second argument to run
        the query on behalf of that user.

        Arguments
        ---------
        device_list: list
            list of device hostnames to query
        username: string
            username of the user to query (admins only)

        Return value
        ------------
        Returns a nested dictionary where the top level key is the device type, the value is
        a list of dictionaries. The key of the second dictionary is a hostname from the device_list
        which exists in the queried instance. The value is a boolean
        for whether the user can access that device.
        If the device is visible, also includes a boolean denoting whether the specified
        device is a pipeline device which can run jobs designed in the dispatcher refactoring.
        If a pipeline device, also includes a boolean denoting whether the specified pipeline
        device exclusively accepts YAML submissions - JSON submissions are rejected if this
        device is marked as exclusive.
        {
            'mustang': [
                {
                    'mustang01': {
                        'visible': True
                        }
                }
            ],
            'panda': [
                {
                    'panda05': {
                        'visible': True
                        }
                    }
            ]
        }

        If the device type is hidden, that type and the nested dictionary for that type
        will be omitted.
        Retired devices will be omitted.
        If the device does not exist, that device will be omitted from the
        returned dictionary.
        This function requires authentication with a username and token.

        Example
        -------

        server.system.user_can_view_devices(['kvm014', 'kvm02'])
        {'qemu':
            [
                {'kvm014': {
                    'exclusive': True,
                    'visible': True,
                    'is_pipeline': True
                    }
                },
                {'kvm02': {
                    'exclusive': True,
                    'visible': True,
                    'is_pipeline': True}
                }
            ]
        }

        # if using the username and token of an admin, a different user can be queried:
        server.system.user_can_view_devices(
            ['mustang01', 'wandboard07', 'imx53-01', 'cubietruck02', 'black01'],
            'firstname.lastname'
        )

        """
        self._authenticate()
        if not isinstance(device_list, list):
            raise xmlrpclib.Fault(
                errors.BAD_REQUEST,
                "device list argument must be a list")
        username = self._switch_user(username)
        retval = {}
        for hostname in device_list:
            try:
                device = Device.objects.get(hostname=hostname)
            except Device.DoesNotExist:
                continue
            device_type = device.device_type
            if device_type.owners_only and not device.is_owned_by(username):
                continue
            retval.setdefault(device_type.name, [])
            visible = device.is_visible_to(username)
            if visible:
                retval[device_type.name].append({
                    hostname: {
                        'is_pipeline': True,
                        'visible': visible,
                        'exclusive': True
                    }
                })
            else:
                retval[device_type.name].append({
                    hostname: {'visible': visible}
                })
        return retval

    def user_can_submit_to_types(self, type_list, username=None):
        """
        Name
        ----
        user_can_submit_to_types (`type_list`)

        Administrators only:
        user_can_submit_to_types (`type_list`, `username`)

        Description
        -----------
        Check the access permissions on a list of device types.
        Admins can specify a username as the second argument to run
        the query on behalf of that user.

        Arguments
        ---------
        type_list: list
            list of device types to query
        username: string
            username of the user to query (admins only)

        Return value
        ------------
        Returns a dictionary where the key is a string of the device_type from
        the type_list, if it exists in the queried instance. The value is a boolean
        for whether the user can submit to any devices of the specified type.
        {
          'panda': True,
          'mustang': False
        }
        If the device type number does not exist, that type will be omitted from the
        returned dictionary.
        This function requires authentication with a username and token.

        Example
        -------
        server.system.user_can_submit_to_types(
            ['mustang', 'panda', 'qemu', 'kvm', 'cubie2']
        )
        {'cubie2': True, 'mustang': False, 'kvm': True, 'qemu': True, 'panda': True}

        # if using the username and token of an admin, a different user can be queried:
        server.system.user_can_submit_to_types(
            ['mustang', 'panda', 'qemu', 'kvm', 'cubie2'],
            'firstname.lastname'
        )

        """
        self._authenticate()
        if not isinstance(type_list, list):
            raise xmlrpclib.Fault(
                errors.BAD_REQUEST,
                "type list argument must be a list")
        username = self._switch_user(username)
        if not username.has_perm('lava_scheduler_app.add_testjob'):
            raise xmlrpclib.Fault(
                errors.FORBIDDEN,
                "User '%s' does not have permissiont to submit jobs." % username
            )
        retval = {}
        for type_name in type_list:
            try:
                device_type = DeviceType.objects.get(name=type_name)
            except DeviceType.DoesNotExist:
                continue
            devices = Device.objects.filter(device_type=device_type)
            access = []
            for device in devices:
                access.append(device.can_submit(username))
            retval[device_type.name] = any(access)
        return retval

    def pipeline_network_map(self, switch=None):
        """
        Name
        ----
        pipeline_network_map(switch=None):

        Description
        -----------

        Collate all the vland information from pipeline devices to create a complete map,
        then return YAML data for all switches or a specified switch.

        This function requires authentication with a username and token.

        Arguments
        ---------
        switch: string
            hostname or IP of the switch to map. If None, data is returned for all switches.

        Return value
        ------------
        Returns a YAML file of the form:

        switches:
          '192.168.0.2':
          - port: 5
            device:
              interface: eth0
              sysfs: "/sys/devices/pci0000:00/0000:00:19.0/net/eth0"
              mac: "f0:de:f1:46:8c:21"
              hostname: bbb1

        """
        self._authenticate()
        # get all device dictionaries, build the entire map.
        dictionaries = [
            (device.hostname, device.load_configuration()) for device in Device.objects.all()
        ]
        network_map = {'switches': {}}
        for (hostname, params) in dictionaries:
            if 'interfaces' not in params:
                continue
            for interface in params['interfaces']:
                for map_switch, port in params['map'][interface].items():
                    port_list = []
                    device = {
                        'interface': interface,
                        'mac': params['mac_addr'][interface],
                        'sysfs': params['sysfs'][interface],
                        'hostname': hostname
                    }
                    port_list.append({'port': port, 'device': device})
                    switch_port = network_map['switches'].setdefault(map_switch, [])
                    # Any switch can only have one entry for one port
                    if port not in switch_port:
                        switch_port.extend(port_list)

        if switch:
            if switch in network_map['switches']:
                return yaml.dump(network_map['switches'][switch])
            else:
                return xmlrpclib.Fault(
                    404, "No switch '%s' was found in the network map of supported devices." % switch)
        return yaml.dump(network_map)


class LavaMapper(Mapper):

    def register_introspection_methods(self):
        """
        Register LavaSystemAPI as 'system' object.

        LavaSystemAPI adds a 'whoami' system method above what the default
        has.
        """
        self.register(LavaSystemAPI, 'system')
