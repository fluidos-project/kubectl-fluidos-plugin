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
from pytest_kubernetes.providers.base import AClusterManager

from kubectl_fluidos import fluidos_kubectl_extension
from kubectl_fluidos.modelbased import ModelBasedOrchestratorConfiguration
from kubectl_fluidos.modelbased import ModelBasedOrchestratorProcessor


def test_basic_creation(k8s: AClusterManager) -> None:
    k8s.create()

    crd_path = pkg_resources.resource_filename(__name__, "utility/fluidos-deployment-crd.yaml")
    k8s.apply(crd_path)

    assert len(k8s.kubectl(["get", "fd"])["items"]) == 0

    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-deployment-single-w-intent.yaml")

    return_value = fluidos_kubectl_extension(["kubectl-fluidos", "-f", doc_file], StringIO(),
                                             on_k8s_w_intent=lambda x: ModelBasedOrchestratorProcessor(ModelBasedOrchestratorConfiguration.build_configuration([
                                                 "--kubeconfig", str(k8s.kubeconfig.absolute())
                                             ]))(x)
                                             )

    assert 0 == return_value

    kctl_ret = k8s.kubectl(["get", "fd"])

    assert kctl_ret
    assert len(kctl_ret["items"]) == 1
    assert kctl_ret["items"][0]["metadata"]["name"] == "dataset-operator"

    k8s.delete()


def test_error_if_no_CRD_defined(k8s: AClusterManager) -> None:
    k8s.create()

    processor = ModelBasedOrchestratorProcessor(ModelBasedOrchestratorConfiguration.build_configuration(["--kubeconfig", str(k8s.kubeconfig.absolute())]))

    with pkg_resources.resource_stream(__name__, "dataset/test-deployment-single-w-intent.yaml") as input_data:
        ret = processor(input_data.read())

    assert ret != 0

    k8s.delete()


def test_error_if_malformed_request(k8s: AClusterManager) -> None:
    k8s.create()
    crd_path = pkg_resources.resource_filename(__name__, "utility/fluidos-deployment-crd.yaml")
    k8s.apply(crd_path)

    processor = ModelBasedOrchestratorProcessor(ModelBasedOrchestratorConfiguration.build_configuration(["--kubeconfig", str(k8s.kubeconfig.absolute())]))

    with pkg_resources.resource_stream(__name__, "dataset/test-mspl.xml") as input_data:
        ret = processor(input_data.read())

    assert ret != 0

    k8s.delete()
