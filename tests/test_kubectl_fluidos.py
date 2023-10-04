# coding: utf-8
'''
------------------------------------------------------------------------------
Copyright 2016 Esri
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

import codecs
import pkg_resources
from io import StringIO

from kubectl_fluidos import fluidos_kubectl_extension, _is_XML, _is_YAML


def test_xml_validation():
    xml = """<?xml version="1.0"?>
<data>
    <country name="Liechtenstein">
        <rank>1</rank>
        <year>2008</year>
        <gdppc>141100</gdppc>
        <neighbor name="Austria" direction="E"/>
        <neighbor name="Switzerland" direction="W"/>
    </country>
    <country name="Singapore">
        <rank>4</rank>
        <year>2011</year>
        <gdppc>59900</gdppc>
        <neighbor name="Malaysia" direction="N"/>
    </country>
    <country name="Panama">
        <rank>68</rank>
        <year>2011</year>
        <gdppc>13600</gdppc>
        <neighbor name="Costa Rica" direction="W"/>
        <neighbor name="Colombia" direction="E"/>
    </country>
</data>
"""

    assert _is_XML(xml)
    assert not _is_XML(None)
    assert not _is_XML("")

    text = """grandparent:
  parent:
    child:
      name: Bobby
    sibling:
      name: Molly
"""
    assert not _is_XML(text)


def test_validate_yaml():
    text = """grandparent:
  parent:
    child:
      name: Bobby
    sibling:
      name: Molly
"""
    assert _is_YAML(text)
    assert not _is_YAML(None)


def test_input_defined_as_stdin():
    with pkg_resources.resource_stream(__name__, "dataset/test-deployment-single.yaml") as stream:
        text = codecs.getreader("utf-8")(stream).read()

    def validation(a, b):
        return 123456

    return_value = fluidos_kubectl_extension(["kubectl-fluidos"], StringIO(text), on_apply=validation)

    assert return_value == 123456


def test_input_from_parameter():
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-deployment-single.yaml")

    def validation(a, b):
        return 123456

    return_value = fluidos_kubectl_extension(["kubectl-fluidos", "-f", doc_file], StringIO(), on_apply=validation)

    assert return_value == 123456
    

def test_validate_fallsback_to_appy():
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-deployment-single.yaml")

    def apply(a, b):
        return 123456

    def drl(a, b):
        return 9876342

    def mspl(a, b):
        return 000000

    return_value = fluidos_kubectl_extension(["kubectl-fluidos", "-f", doc_file], StringIO(), on_apply=apply, on_k8s_w_intent=drl, on_mlps=mspl)

    assert return_value == 123456


def test_yaml_with_intent_invokes_drl():
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-deployment-single-w-intent.yaml")

    def apply(a, b):
        return 123456

    def drl(a):
        return 9876342

    def mspl(a):
        return 000000

    return_value = fluidos_kubectl_extension(["kubectl-fluidos", "-f", doc_file], StringIO(), on_apply=apply, on_k8s_w_intent=drl, on_mlps=mspl)

    assert return_value == 9876342


def test_xml_invokes_mspl_by_default():
    doc_file = pkg_resources.resource_filename(__name__, "dataset/test-mspl.xml")

    def apply(a, b):
        return 123456

    def drl(a):
        return 9876342

    def mspl(a):
        return 000000

    return_value = fluidos_kubectl_extension(["kubectl-fluidos", "-f", doc_file], StringIO(), on_apply=apply, on_k8s_w_intent=drl, on_mlps=mspl)

    assert return_value == 000000
