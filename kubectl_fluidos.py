#! /usr/bin/env python
import logging
import os
import sys
from typing import Any, Callable, Optional, TextIO
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from xml.etree import ElementTree
from enum import Enum, auto


class InputFormat(Enum):
    K8S = auto()
    MSPL = auto()


INTENT_K8S_KEYWORD = "quality_intent"



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
    return stdin.read()


def _extract_input_data(arguments: list[str], stdin: TextIO) -> tuple[list[str], Optional[str]]:
    input_data: list[str] = [
        _read_file_argument_content(arguments[idx + 1]) for idx, arg in enumerate(arguments) if (arg == "-f" or arg == "--filename") and idx + 1 < len(arguments)
    ]

    if len(input_data):
        return input_data

    stdin_data = _attempt_reading_from_stdio(stdin)

    if len(stdin_data):
        return [stdin_data]

    return None


def _is_deployment(spec: dict[str, Any]) -> bool:
    if type(spec) == dict:
        return spec.get("kind", None) == "Deployment"
    return False


def _behavior_not_defined() -> int:
    raise NotImplementedError()


def _default_apply(args: list[str], stdin: bytes) -> int:
    return os.system("kubectl apply " + " ".join(args))


def fluidos_kubectl_extension(argv: list[str], stdin: TextIO, *, on_apply: Callable[..., int] = _default_apply, on_mlps: Callable[..., int] = _behavior_not_defined, on_k8s_w_intent: Callable[..., int] = _behavior_not_defined) -> int:
    logging.info("Starting FLUIDOS kubectl extension")

    data = _extract_input_data(argv, stdin) # this needs to be fixed, we cannot assume kubectl apply is receiving data from stdin if it has been consumed here

    if 0 < len(data) < 2:
        # we assume to handle only one file/spec, for the moment at least
        try:
            input_format, spec = _check_input_format(data[0])

            if input_format == InputFormat.MSPL:
                # INVOKE MSPL orchestrator
                logging.info("Invoking MSPL Service Handler")
                return on_mlps(sys.argv[-1:])
            elif input_format == InputFormat.K8S:
                if _is_deployment(spec) and _has_intent_defined(spec):
                    logging.info("Invoking K8S with Intent Service Handler")
                    return on_k8s_w_intent(sys.argv[-1:])

        except ValueError:
            logging.info("Unknown format, fallback to apply")
    else:
        logging.info("Skipping because multiple specification available")

    # if nothing else applies, fallback to vanilla kubectl apply behavior
    logging.info("Invoking kubectl apply")
    return on_apply(sys.argv[-1:], spec)


def main():
    raise SystemExit(
        fluidos_kubectl_extension(sys.argv, sys.stdin)
    )

if __name__ == "__main__":
    main()