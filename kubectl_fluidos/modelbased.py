# coding: utf-8
'''
------------------------------------------------------------------------------
Copyright 2023 IBM Research Europe
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
'''
from __future__ import annotations
from argparse import ArgumentParser

from dataclasses import dataclass
import logging
from typing import Any
from kubernetes import config
from kubernetes import client
from kubernetes import utils
from kubernetes.client import Configuration
from kubernetes.config import ConfigException
import yaml

from kubectl_fluidos.common import k8sArgParser

logger = logging.getLogger(__name__)


@dataclass
class ModelBasedOrchestratorConfiguration:
    pass

    @staticmethod
    def build_configuration(args: list[str]) -> ModelBasedOrchestratorConfiguration:
        try:
            k8s_args, remaining_args = k8sArgParser().parse_known_args(args)
            # missing expanding load configuration from provided command line options

            loading_args = {}

            if k8s_args.kubeconfig:
                loading_args["config_file"] = k8s_args.kubeconfig

            config.load_config(**loading_args)

            try:
                c = Configuration().get_default_copy()
            except AttributeError:
                c = Configuration()
                c.assert_hostname = False
            Configuration.set_default(c)

            return ModelBasedOrchestratorConfiguration()
        except ConfigException:
            print("Nothing to do here")

        raise RuntimeError("Unable to build configuration")


class ModelBasedOrchestratorProcessor:
    def __init__(self, configuration: ModelBasedOrchestratorConfiguration = ModelBasedOrchestratorConfiguration()):
        self._configuration = configuration
        self._k8s_client = client.ApiClient(self._configuration)

    def __call__(self, data: list[str]) -> int:
        logger.info("Wrapping request")
        request = _request_to_dictionary(data)
        logger.info("Sending request to k8s")
        utils.create_from_dict(self._k8s_client, data=request)


def _request_to_dictionary(data: list[str]) -> dict[str, Any]:
    request_as_yaml: dict[str, Any] = _extract_request(data)

    request_to_dictionary = {
        "apiVersion": "fluidos.eu/v1",
        "kind": "ModelBasedDeployment",
        "metadata": {
            "name": request_as_yaml["metadata"]["name"]
        },
        "spec": request_as_yaml
    }

    return request_to_dictionary


def _extract_request(data: list[str]) -> dict[str, Any]:
    parser = _modelBasedArgParser()

    namespace, remaining_args = parser.parse_known_args(data)

    with open(namespace.f, "r") as input_data:
        return yaml.safe_load(input_data)


def _modelBasedArgParser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument("-f", required=True, type=str)

    return parser
