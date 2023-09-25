#! /usr/bin/env python
from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import sys
from typing import Any, Callable, Optional, TextIO
import yaml
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.config import ConfigException
from requests import post

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from xml.etree import ElementTree
from enum import Enum, auto


class InputFormat(Enum):
    K8S = auto()
    MSPL = auto()


@dataclass
class MLPSProcessorConfiguration:
    hostname: str = "localhost"
    port: int = 8002
    schema: str = "http"

    @staticmethod
    def build_configuration(args: list[str]) -> MLPSProcessorConfiguration:
        """
            if "config_file" in kwargs.keys():
        load_kube_config(**kwargs)
    elif "kube_config_path" in kwargs.keys():
        kwargs["config_file"] = kwargs.pop("kube_config_path", None)
        load_kube_config(**kwargs)
    elif exists(expanduser(KUBE_CONFIG_DEFAULT_LOCATION)):
        load_kube_config(**kwargs)
        """
        try:
            config.load_config()

            try:
                c = Configuration().get_default_copy()
            except AttributeError:
                c = Configuration()
                c.assert_hostname = False
            Configuration.set_default(c)
        except ConfigException:
            print("Nothing to do here")

        return MLPSProcessorConfiguration(
            hostname=MLPSProcessorConfiguration._extract_hostname(c.host),
            port=8002,
            schema="http"
        )

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
        response = post(f"{self.configuration.schema}://{self.configuration.hostname}:{self.configuration.port}/meservice", headers=self._build_headers(), data=data)
        if response.status_code == 200:
            return 0

        if int(response.status_code / 100) == 4:
            logging.error(f"Unable to retrieve correct resource {response.status_code=}")

        if int(response.status_code / 100) == 5:
            logging.error(f"Error in the service {response.status_code=}")

        return 1

    def _build_headers(self) -> dict[str, Any]:
        return {
            "Content-Type": "application/xml"
        }


INTENT_K8S_KEYWORD = "quality_intent"  # label to be confirmed


def _is_YAML(data: str) -> bool:
    try:
        _ = _to_YAML(data)
        return True
    except Exception as e:
        logging.info(str(e))
    return False


def _is_XML(data: str) -> bool:
    try:
        _ = ElementTree.fromstring(data)
        return True
    except Exception as e:
        logging.info(str(e))
    return False


def _to_YAML(data: str) -> dict[str, Any]:
    return yaml.load(data, Loader=Loader)


def _check_input_format(input_data: str) -> (InputFormat, Optional[dict[str, Any]]):
    if _is_XML(input_data):
        return (InputFormat.MSPL, None)
    elif _is_YAML(input_data):
        return (InputFormat.K8S, _to_YAML(input_data))
    raise ValueError("Unknown format")


def _has_container_intent_defined(container_template: dict[str, Any]) -> bool:
    return "resources" in container_template and INTENT_K8S_KEYWORD in container_template["resources"]


def _has_intent_defined(data: dict[str, Any]) -> bool:
    # big assumption, of where intents are specified within a deployment
    for container_template in data["spec"]["template"]["spec"]["containers"]:
        # assume it is specified as resource request
        if _has_container_intent_defined(container_template):
            return True

    return False


def _read_file_argument_content(filename: str) -> str:
    with open(filename) as input_file:
        return input_file.read()


def _attempt_reading_from_stdio(stdin: TextIO) -> str:
    if stdin.isatty():
        return ''
    else:
        return stdin.read()


def _extract_input_data(arguments: list[str], stdin: TextIO) -> tuple[list[str], Optional[str]]:
    input_data: list[str] = [
        _read_file_argument_content(arguments[idx + 1]) for idx, arg in enumerate(arguments) if (arg == "-f" or arg == "--filename") and idx + 1 < len(arguments)
    ]

    if len(input_data):
        return (input_data, None)

    stdin_data = _attempt_reading_from_stdio(stdin)

    if stdin_data and len(stdin_data):
        return ([], None)

    raise ValueError("No input provided")


def _is_deployment(spec: dict[str, Any]) -> bool:
    if type(spec) == dict:
        return spec.get("kind", None) == "Deployment"
    return False


def _behavior_not_defined() -> int:
    raise NotImplementedError()


def _default_apply(args: list[str], stdin: str) -> int:
    return os.system("kubectl apply " + " ".join(args))


def fluidos_kubectl_extension(argv: list[str], stdin: TextIO, *, on_apply: Callable[[list[str], str], int] = _default_apply, on_mlps: Callable[..., int] = _behavior_not_defined, on_k8s_w_intent: Callable[..., int] = _behavior_not_defined) -> int:
    logging.info("Starting FLUIDOS kubectl extension")

    try:
        file_data, stdin_data = _extract_input_data(argv, stdin)  # this needs to be fixed, we cannot assume kubectl apply is receiving data from stdin if it has been consumed here
    except ValueError:
        print("error: must specify one of -f and -k", file=sys.stderr)
        return 1

    data: Optional[str] = None

    if stdin_data:
        data = stdin_data
    if file_data and 0 < len(file_data) < 2:
        data = file_data[0]

    if data:
        # we assume to handle only one file/spec, for the moment at least
        try:
            input_format, spec = _check_input_format(data)

            if input_format == InputFormat.MSPL:
                # INVOKE MSPL orchestrator
                logging.info("Invoking MSPL Service Handler")
                return on_mlps(data)
            elif input_format == InputFormat.K8S:
                if _is_deployment(spec) and _has_intent_defined(spec):
                    logging.info("Invoking K8S with Intent Service Handler")
                    return on_k8s_w_intent(argv[-1:])

        except ValueError:
            logging.info("Unknown format, fallback to apply")
    else:
        logging.info("Skipping because multiple specification available")

    # if nothing else applies, fallback to vanilla kubectl apply behavior
    logging.info("Invoking kubectl apply")
    return on_apply(argv[-1:], stdin_data)


def main():
    raise SystemExit(
        fluidos_kubectl_extension(
            sys.argv,
            sys.stdin,
            on_mlps=lambda x: MLPSProcessor(MLPSProcessor.build_configuration(sys.argv))(x))
    )


if __name__ == "__main__":
    main()
