#! /usr/bin/env python
import os
import sys
import yaml
from enum import Enum, auto

class InputFormat(Enum):
    K8S = auto()
    MSPL = auto()


def _check_input_format(input_data) -> InputFormat:
    return None 


def main() -> int:
    print(sys.argv)




    return os.system("kubectl apply " + " ".join(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())