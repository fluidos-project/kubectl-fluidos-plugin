# coding: utf-8
'''
------------------------------------------------------------------------------
Copyright 2023 IBM Research
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

from dataclasses import dataclass
from logging import Logger
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.config import ConfigException

from kubectl_fluidos.common import k8sArgParser

logger = Logger(__name__)


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
        self.configuration = configuration

    def __call__(self, data) -> int:
        raise NotImplementedError()
