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
from typing import Any, Optional
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.config import ConfigException
from requests import post
from requests.exceptions import InvalidURL

from kubectl_fluidos.common import k8sArgParser


logger = logging.getLogger(__name__)


def mlpsArgParser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument("--mlps-hostname", required=False, type=str)
    parser.add_argument("--mlps-port", required=False, type=int)
    parser.add_argument("--mlps-schema", required=False, type=int)
    parser.add_argument("--mlps-url", required=False, type=str)

    return parser


@dataclass
class MLPSProcessorConfiguration:
    hostname: str = "localhost"
    port: int = 8002
    schema: str = "http"
    url: Optional[str] = None

    def get_url(self) -> str:
        if self.url:
            return self.url
        else:
            return f"{self.schema}://{self.hostname}:{self.port}/meservice"

    @staticmethod
    def build_configuration(args: list[str]) -> MLPSProcessorConfiguration:
        namespace, remaining_args = mlpsArgParser().parse_known_args(args)

        if namespace.mlps_url is not None:
            return MLPSProcessorConfiguration(url=namespace.mlps_url)
        elif namespace.mlps_hostname or namespace.mlps_port or namespace.mlps_schema:
            return MLPSProcessorConfiguration(
                hostname=namespace.mlps_hostname if namespace.mlps_hostname else "localhost",
                port=namespace.mlps_port if namespace.mlps_port else 8002,
                schema=namespace.mlps_schema if namespace.mlps_schema else "http"
            )

        try:
            """
                if "config_file" in kwargs.keys():
            load_kube_config(**kwargs)
        elif "kube_config_path" in kwargs.keys():
            kwargs["config_file"] = kwargs.pop("kube_config_path", None)
            load_kube_config(**kwargs)
        elif exists(expanduser(KUBE_CONFIG_DEFAULT_LOCATION)):
            load_kube_config(**kwargs)
            """

            k8s_args, remaining_args = k8sArgParser().parse_known_args(remaining_args)
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

            return MLPSProcessorConfiguration(
                hostname=MLPSProcessorConfiguration._extract_hostname(c.host),
                port=8002,
                schema="http"
            )
        except ConfigException as e:
            logger.debug(f"Unable to load k8s configuration: {e}")

        # if nothing worked, return defaults
        return MLPSProcessorConfiguration()

    @staticmethod
    def _extract_hostname(url: str) -> str:
        from urllib.parse import urlparse

        parsed_url = urlparse(url)

        if parsed_url.hostname is not None:
            return parsed_url.hostname

        raise ValueError("Unable to extract hostname properly")


class MLPSProcessor:
    def __init__(self, configuration: MLPSProcessorConfiguration = MLPSProcessorConfiguration()):
        self.configuration = configuration

    def __call__(self, data) -> int:
        try:
            response = post(self.configuration.get_url(), headers=self._build_headers(), data=data)
            if response.status_code == 200:
                return 0
        except InvalidURL as e:
            logger.info(f"Error connecting to the orchestration service {e.response}")
            return 1

        if int(response.status_code / 100) == 4:
            logger.error(f"Unable to retrieve correct resource {response.status_code=}")

        if int(response.status_code / 100) == 5:
            logger.error(f"Error in the service {response.status_code=}")

        return 1

    def _build_headers(self) -> dict[str, Any]:
        return {
            "Content-Type": "application/xml"
        }
