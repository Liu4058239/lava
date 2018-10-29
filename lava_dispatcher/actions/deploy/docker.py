# Copyright (C) 2017 Linaro Limited
#
# Author: Remi Duraffort <remi.duraffort@linaro.org>
#
# This file is part of LAVA Dispatcher.
#
# LAVA Dispatcher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# LAVA Dispatcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along
# with this program; if not, see <http://www.gnu.org/licenses>.

import re
import subprocess  # nosec - internal

from lava_common.exceptions import InfrastructureError, JobError
from lava_dispatcher.action import Pipeline
from lava_dispatcher.actions.deploy import DeployAction
from lava_dispatcher.actions.deploy.environment import DeployDeviceEnvironment
from lava_dispatcher.actions.deploy.overlay import OverlayAction
from lava_dispatcher.logical import Deployment
from lava_dispatcher.utils.shell import which


class DockerAction(DeployAction):

    name = "deploy-docker"
    description = "deploy docker images"
    summary = "deploy docker"

    def validate(self):
        super().validate()
        which("docker")

        # Print docker version
        try:
            out = subprocess.check_output(["docker", "version", "-f", "{{.Server.Version}}"])  # nosec - internal
            out = out.decode("utf-8", errors="replace").strip("\n")
            self.logger.debug("docker server, installed at version: %s", out)
            out = subprocess.check_output(["docker", "version", "-f", "{{.Client.Version}}"])  # nosec - internal
            out = out.decode("utf-8", errors="replace").strip("\n")
            self.logger.debug("docker client, installed at version: %s", out)
        except subprocess.CalledProcessError as exc:
            raise InfrastructureError("Unable to call '%s': %s" % (exc.cmd, exc.output))
        except OSError:
            raise InfrastructureError("Command 'docker' does not exist")

        # "image" can be a dict or a string
        image = self.parameters["image"]
        if isinstance(image, str):
            self.image_name = image
            self.local = False
        else:
            self.image_name = image["name"]
            self.local = image.get("local", False)

        # check docker image name
        # The string should be safe for command line inclusion
        if re.compile("^[a-z0-9._:/-]+$").match(self.image_name) is None:
            self.errors = "image name '%s' is invalid" % self.image_name
        self.set_namespace_data(action=self.name, label='image',
                                key='name', value=self.image_name)

    def populate(self, parameters):
        self.internal_pipeline = Pipeline(parent=self, job=self.job, parameters=parameters)
        if self.test_needs_deployment(parameters):
            self.internal_pipeline.add_action(DeployDeviceEnvironment())
        if self.test_needs_overlay(parameters):
            self.internal_pipeline.add_action(OverlayAction())

    def run(self, connection, max_end_time):
        # Pull the image
        if self.local:
            cmd = ["docker", "image", "inspect", "--format", "image exists",
                   self.image_name]
            out = self.run_command(cmd, allow_fail=False, allow_silent=False)
            if not out:
                msg = "Unable to inspect docker image '%s'" % self.image_name
                raise JobError(msg)
        else:
            cmd = ["docker", "pull", self.image_name]
            out = self.run_command(cmd, allow_fail=False, allow_silent=False)
            if not out:
                msg = "Unable to pull docker image '%s'" % self.image_name
                raise JobError(msg)

        return super().run(connection, max_end_time)


class Docker(Deployment):
    compatibility = 4
    name = 'docker'

    def __init__(self, parent, parameters):
        super().__init__(parent)
        self.action = DockerAction()
        self.action.section = self.action_type
        self.action.job = self.job
        parent.add_action(self.action, parameters)

    @classmethod
    def accepts(cls, device, parameters):
        if 'docker' not in device['actions']['deploy']['methods']:
            return False, "'docker' not in the device configuration deploy methods"
        if parameters['to'] != 'docker':
            return False, '"to" parameter is not "docker"'
        if 'image' not in parameters:
            return False, '"image" is not in the deployment parameters'
        return True, 'accepted'
