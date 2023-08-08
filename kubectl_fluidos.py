#! /usr/bin/env python
import os
import sys

def main() -> int:
    print(sys.argv)
    

    return os.system("kubectl apply " + " ".join(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())