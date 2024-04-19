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
from http import HTTPStatus
from io import StringIO
from typing import Any

import pkg_resources
import requests
from pytest import fail
from pytest_httpserver import HTTPServer
from werkzeug import Response

from kubectl_fluidos import fluidos_kubectl_extension
from kubectl_fluidos import MSPLProcessor
from kubectl_fluidos import MSPLProcessorConfiguration


def test_handler_responses(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/foobar").respond_with_json({"foo": "bar"})
    assert requests.get(httpserver.url_for("/foobar")).json() == {"foo": "bar"}


def test_build_configuration_empty_parameters_no_k8s() -> None:
    configuration: MSPLProcessorConfiguration = MSPLProcessorConfiguration.build_configuration([])

    assert configuration is not None
    assert configuration.port == 8002
    assert configuration.hostname == "localhost" or configuration.hostname == "0.0.0.0"
    assert configuration.schema == "http"


def test_basic_behavior(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/meservice", method="POST").respond_with_json({"result": "ok"})

    processor = MSPLProcessor(
        MSPLProcessorConfiguration(url=httpserver.url_for("/meservice"))
    )

    assert processor("FOOO") == 0


def test_configuration_overload_from_cl_arguments() -> None:
    configuration = MSPLProcessorConfiguration.build_configuration(["--mspl-url", "https://some_url.com/my-path"])

    assert configuration.get_url() == "https://some_url.com/my-path"

    configuration = MSPLProcessorConfiguration.build_configuration(["--mspl-hostname", "www.google.com", "--mspl-port", "12355"])

    assert configuration.get_url() == "http://www.google.com:12355/meservice"


def test_service_not_available() -> None:
    processor = MSPLProcessor(
        MSPLProcessorConfiguration(url="http://localhost:123123/meservice")
    )

    assert processor("FOOO") != 0


def test_timeout_management(httpserver: HTTPServer) -> None:
    response: Response = Response(
        response=None,
        status=HTTPStatus.BAD_REQUEST
    )
    httpserver.expect_request("/meservice", method="POST").respond_with_response(response=response)

    processor = MSPLProcessor(
        MSPLProcessorConfiguration(url="http://localhost:123123/meservice")
    )

    assert processor("FOOO") != 0


def test_pipeline(httpserver: HTTPServer) -> None:
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-mspl.xml")

    def apply(a: Any, b: Any) -> int:
        return 123456

    def drl(a: Any) -> int:
        return 9876342

    httpserver.expect_request("/meservice", method="POST").respond_with_json({
        "message": "ok"
    })

    args = ["kubectl-fluidos", "-f", doc_file, "--mspl-url", httpserver.url_for("/meservice")]

    return_value = fluidos_kubectl_extension(args, StringIO(), on_apply=apply, on_k8s_w_intent=drl, on_mlps=lambda x: MSPLProcessor(MSPLProcessorConfiguration.build_configuration(args))(x))

    assert return_value == 0


def test_error_handling() -> None:
    fail("Not implemented yet")
