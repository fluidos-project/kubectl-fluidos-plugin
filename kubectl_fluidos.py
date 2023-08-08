#! /usr/bin/env python
import logging
import os
import sys
import yaml
from enum import Enum, auto


class InputFormat(Enum):
    K8S = auto()
    MSPL = auto()



def _is_YAML(data: str) -> bool:
    raise NotImplementedError()


def _is_XML(data: str) -> bool:
    raise NotImplementedError()


def _check_input_format(input_data: str) -> InputFormat:
    if _is_YAML(input_data):
        return InputFormat.K8S
    elif _is_XML(input_data):
        return InputFormat.MSPL
    raise ValueError("Unkown format")


def _has_intent_defined(input_data: str) -> bool:
    return NotImplementedError


def _extract_input_data(arguments: list[str]) -> str:
    raise NotImplementedError


def main() -> int:
    logging.info("Starting FLUIDOS kubectl extension")

    data = _extract_input_data(sys.argv)

    logging.trace(f"Extracted:\n---\n{data}\n---")


    input_format = _check_input_format(data)

    if input_format == InputFormat.MSPL:
        # INVOKE MSPL orchestrator
        raise NotImplementedError()
    elif input_format == InputFormat.K8S:
        if _has_intent_defined(data):
            raise NotImplementedError()

    # if nothing else applies, fallback to vanilla kubectl apply behavior
    return os.system("kubectl apply " + " ".join(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())