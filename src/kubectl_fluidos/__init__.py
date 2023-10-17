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

import os
import sys
from typing import Any
from typing import Callable
from typing import Optional
from typing import TextIO
import yaml

import logging

from .modelbased import ModelBasedOrchestratorConfiguration
from .modelbased import ModelBasedOrchestratorProcessor
from .mspl import MPSLProcessor
from .mspl import MSPLProcessorConfiguration

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from xml.etree import ElementTree
from enum import Enum
from enum import auto


logger = logging.getLogger(__name__)


class InputFormat(Enum):
    K8S = auto()
    MSPL = auto()


INTENT_K8S_KEYWORD = "fluidos-intent-"  # label to be confirmed


def _is_YAML(data: str) -> bool:
    try:
        _ = _to_YAML(data)
        return True
    except Exception as e:
        logger.info(str(e))
    return False


def _is_XML(data: str) -> bool:
    try:
        _ = ElementTree.fromstring(data)
        return True
    except Exception as e:
        logger.info(str(e))
    return False


def _to_YAML(data: str) -> dict[str, Any]:
    return yaml.load(data, Loader=Loader)


def _check_input_format(input_data: str) -> (InputFormat, Optional[dict[str, Any]]):
    if _is_XML(input_data):
        return (InputFormat.MSPL, None)
    elif _is_YAML(input_data):
        return (InputFormat.K8S, _to_YAML(input_data))
    raise ValueError("Unknown format")


def _has_intent_defined(spec: dict[str, Any]) -> bool:
    annotations: dict[str, str] = spec.get("metadata", dict()).get("annotations", dict())
    key: str

    for key in annotations.keys():
        if key.startswith(INTENT_K8S_KEYWORD):
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
    if type(spec) is dict:
        return spec.get("kind", None) == "Deployment"
    return False


def _behavior_not_defined() -> int:
    raise NotImplementedError()


def _default_apply(args: list[str], stdin: str) -> int:
    return os.system("kubectl apply " + " ".join(args))


def fluidos_kubectl_extension(argv: list[str], stdin: TextIO, *, on_apply: Callable[[list[str], str], int] = _default_apply, on_mlps: Callable[..., int] = _behavior_not_defined, on_k8s_w_intent: Callable[..., int] = _behavior_not_defined) -> int:
    logger.info("Starting FLUIDOS kubectl extension")

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
                logger.info("Invoking MSPL Service Handler")
                return on_mlps(data)
            elif input_format == InputFormat.K8S:
                if _has_intent_defined(spec):
                    logger.info("Invoking K8S with Intent Service Handler")
                    return on_k8s_w_intent(data)

        except ValueError:
            logger.info("Unknown format, fallback to apply")
    else:
        logger.info("Skipping because multiple specification available")

    # if nothing else applies, fallback to vanilla kubectl apply behavior
    logger.info("Invoking kubectl apply")
    return on_apply(argv[-1:], stdin_data)


def main():
    raise SystemExit(
        fluidos_kubectl_extension(
            sys.argv,
            sys.stdin,
            on_mlps=lambda x: MPSLProcessor(MSPLProcessorConfiguration.build_configuration(sys.argv))(x),
            on_k8s_w_intent=lambda x: ModelBasedOrchestratorProcessor(ModelBasedOrchestratorConfiguration.build_configuration(sys.argv))(x)
        )
    )


if __name__ == "__main__":
    main()
