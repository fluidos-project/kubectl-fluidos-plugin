from argparse import ArgumentParser


def k8sArgParser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument("--kubeconfig", required=False, default="")
    parser.add_argument("--context", required=False, default="")
    parser.add_argument("--cluster", required=False, default="")
    parser.add_argument("--namespace", required=False, default="")
    parser.add_argument("--username", required=False, default="")
    parser.add_argument("--password", required=False, default="")

    return parser
