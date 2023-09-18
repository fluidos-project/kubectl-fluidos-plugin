from pytest_httpserver import HTTPServer
import requests

from kubectl_fluidos import MLPSProcessor
from kubectl_fluidos import MLPSProcessorConfiguration


def test_handler_responses(httpserver: HTTPServer):
    httpserver.expect_request("/foobar").respond_with_json({"foo": "bar"})
    assert requests.get(httpserver.url_for("/foobar")).json() == {"foo": "bar"}


def test_build_configuration_empty_parameters():
    configuration: MLPSProcessorConfiguration = MLPSProcessor.build_configuration([])

    assert configuration is not None
    assert configuration.port == 8002
    assert configuration.hostname == "127.0.0.1"
    assert configuration.schema == "http"


def test_basic_behavior(httpserver: HTTPServer):
    httpserver.expect_request("/meservice").respond_with_json({"result": "ok"})

    processor = MLPSProcessor(
        httpserver.url_for()
    )

    assert processor() == 0
