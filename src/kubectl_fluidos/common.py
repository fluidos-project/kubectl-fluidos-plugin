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
from argparse import ArgumentParser


def k8sArgParser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument("--kubeconfig", required=False, default="")
    parser.add_argument("--context", required=False, default="")
    parser.add_argument("--cluster", required=False, default="")
    parser.add_argument("--namespace", required=False, default="default")
    parser.add_argument("--username", required=False, default="")
    parser.add_argument("--password", required=False, default="")

    return parser
