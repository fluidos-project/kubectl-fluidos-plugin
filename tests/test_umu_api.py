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

from io import StringIO
import pkg_resources
from pytest_httpserver import HTTPServer
import requests
from werkzeug import Response
from http import HTTPStatus

from kubectl_fluidos import MLPSProcessor, fluidos_kubectl_extension
from kubectl_fluidos import MLPSProcessorConfiguration


def test_handler_responses(httpserver: HTTPServer):
    httpserver.expect_request("/foobar").respond_with_json({"foo": "bar"})
    assert requests.get(httpserver.url_for("/foobar")).json() == {"foo": "bar"}


def test_build_configuration_empty_parameters_no_k8s():
    configuration: MLPSProcessorConfiguration = MLPSProcessorConfiguration.build_configuration([])

    assert configuration is not None
    assert configuration.port == 8002
    assert configuration.hostname == "127.0.0.1"
    assert configuration.schema == "http"


def test_basic_behavior(httpserver: HTTPServer):
    httpserver.expect_request("/meservice", method="POST").respond_with_json({"result": "ok"})

    processor = MLPSProcessor(
        MLPSProcessorConfiguration(url=httpserver.url_for("/meservice"))
    )

    assert processor("FOOO") == 0


def test_configuration_overload_from_cl_arguments():
    configuration = MLPSProcessorConfiguration.build_configuration(["--mlps-url", "https://some_url.com/my-path"])

    assert configuration.get_url() == "https://some_url.com/my-path"

    configuration = MLPSProcessorConfiguration.build_configuration(["--mlps-hostname", "www.google.com", "--mlps-port", "12355"])

    assert configuration.get_url() == "http://www.google.com:12355/meservice"


def test_service_not_available():
    processor = MLPSProcessor(
        MLPSProcessorConfiguration(url="http://localhost:123123/meservice")
    )

    assert processor("FOOO") != 0


def test_timeout_management(httpserver: HTTPServer):
    response: Response = Response(
        response=None,
        status=HTTPStatus.BAD_REQUEST
    )
    httpserver.expect_request("/meservice", method="POST").respond_with_response(response=response)

    processor = MLPSProcessor(
        MLPSProcessorConfiguration(url="http://localhost:123123/meservice")
    )

    assert processor("FOOO") != 0


def test_pipeline(httpserver: HTTPServer):
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-mspl.xml")

    def apply(a, b):
        return 123456

    def drl(a):
        return 9876342

    httpserver.expect_request("/meservice", method="POST").respond_with_json({
        "message": "ok"
    })

    args = ["kubectl-fluidos", "-f", doc_file, "--mlps-url", httpserver.url_for("/meservice")]

    return_value = fluidos_kubectl_extension(args, StringIO(), on_apply=apply, on_k8s_w_intent=drl, on_mlps=lambda x: MLPSProcessor(MLPSProcessorConfiguration.build_configuration(args))(x))

    assert return_value == 0
    httpserver.add_assertion
