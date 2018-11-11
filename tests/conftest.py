import os
import re
from collections import namedtuple
from glob import glob

import pytest
import requests
import yaml
from plantuml import deflate_and_encode
from py.xml import html, raw
from yaml.scanner import ScannerError

from compose_plantuml.cli import parse_args, execute
from compose_plantuml import ComposePlantuml


###############################################################################
#
# Utility classes
#
###############################################################################

class PlantUMLServiceDisabled(Exception):
    """
    Exception raised when we want to protect the official PlantUML server
    """
    pass


class PlantUMLService:
    """
    PlantUML client helping with the querying of a PlantUML server.

    Also protects the official PlantUML demo server against rendering queries from our test suite.
    Rendering queries will only be made if a custom PlantUML server is provided.

    """
    demo_server_base_url = 'http://www.plantuml.com/plantuml/'

    def __init__(self, base_url=None):
        # we do not want to DDoS the official PlantUML demo server
        self.download_disabled = not base_url or base_url.rstrip('/') == self.demo_server_base_url.rstrip('/')
        self.base_url = base_url

    @staticmethod
    def test_demo_url(uml):
        return PlantUMLService.build_url(PlantUMLService.demo_server_base_url, 'uml', uml)

    def test_url(self, uml):
        return self._build_url('uml', uml)

    def png_url(self, uml):
        return self._build_url('png', uml)

    def svg_url(self, uml):
        return self._build_url('svg', uml)

    def asciiart_url(self, uml):
        return self._build_url('svg', uml)

    def download_png(self, uml):
        r = self.download('png', uml)
        return r.content

    def download_svg(self, uml):
        r = self.download('svg', uml)
        return r.text

    def download_asciiart(self, uml):
        r = self.download('txt', uml)
        if 'java.lang.IllegalStateException' not in r.text:
            return r.text

    @staticmethod
    def build_url(base_url, service, uml):
        return "{}/{}/{}".format(base_url.rstrip('/'), service, deflate_and_encode(uml))

    def _build_url(self, service, uml):
        if self.base_url is None:
            return self.build_url(self.demo_server_base_url, service, uml)
        else:
            return self.build_url(self.base_url, service, uml)

    def download(self, service, uml):
        if self.download_disabled:
            raise PlantUMLServiceDisabled
        if not service:
            raise Exception("service parameter not provided")
        if not uml:
            raise ValueError("you should provide some uml to render")
        url = self.build_url(self.base_url, service, uml)
        r = requests.get(url)
        if r.status_code == 400:
            # most likely a syntax error in uml
            return r
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            pytest.fail("Unexpected error while trying to to call the PlantUML server: {!s}".format(e),
                        pytrace=False)
        return r


class Spec(namedtuple('Spec', 'compose options expected')):
    """
    Class representing a scenario extracted from a _spec yaml file_ contents.
    See tests/README.md.
    """
    _plantuml_service = None  # typing: PlantUMLService

    def run_assertions(self):
        """
        assert that calling compose_plantuml with the specified _options_ and _docker-compose.yml_ file contents
        produces the expected UML.

        if a PlantUML server is provided (see the `PLANTUML_SERVER` environment variable), this helper also
        asserts that PlantUML is able to render the resulting UML.
        """
        resulting_uml = self._call_compose_plantuml()
        self._set_record_properties(resulting_uml)
        self._assert_resulting_uml(resulting_uml)
        self._assert_rendering(resulting_uml)

    def _set_record_properties(self, resulting_uml):
        """
        set some properties into the current pytest _request_ object to make them available in the html report
        (see pytest-html plugin)

        :param resulting_uml: str
        """
        if hasattr(self, '_record_property_fixture'):
            record_property = getattr(self, '_record_property_fixture')
            record_property("spec", self)
            record_property("resulting_uml", resulting_uml)

    def _call_compose_plantuml(self):
        args = parse_args((self.options or "").split(" "))
        return execute(self.compose, args)

    def _assert_resulting_uml(self, resulting_uml):
        assert (self.expected or "").strip() == resulting_uml.strip(), resulting_uml

    def _assert_rendering(self, resulting_uml):
        # if a PlantUML server was provided, try to generate an image
        if self._plantuml_service:
            response = self._plantuml_service.download('svg', resulting_uml)
            if response.status_code == 400:
                pytest.fail(
                    "The PlantUML server was unable to render uml: \n\n{!s}".format(
                        self._plantuml_service.download_asciiart(resulting_uml)),
                    pytrace=False)


###############################################################################
#
# Custom Pytest fixtures
#
###############################################################################

@pytest.fixture
def spec(request, record_property) -> Spec:
    """
    Pytest fixture providing test scenario data and expected uml result from a _spec yaml file_ as a Spec object.
    See tests/README.md

    The Spec object has a `run_assertion()` method which actually runs the scenario and makes the appropriate assertions.

    :return: Spec
    """
    _spec = request.param
    setattr(_spec, '_record_property_fixture', record_property)
    return _spec


###############################################################################
#
# Test specs auto-discovery
#
###############################################################################

def pytest_generate_tests(metafunc):
    if 'spec' in metafunc.fixturenames:
        spec_files_pattern = metafunc.module.__spec_files__
        idlist = []
        argvalues = []

        if spec_files_pattern.startswith('/'):
            spec_files = spec_files_pattern
        else:
            spec_files = os.path.join(os.path.dirname(metafunc.module.__file__), spec_files_pattern)

        for spec_file in glob(spec_files):
            file_name = os.path.basename(spec_file)
            for specs in _generate_specs_from_yml_file(spec_file):
                for index, spec in enumerate(specs):
                    idlist.append("{}|{}|{}".format(os.path.splitext(file_name)[0], spec.options, index + 1))
                    argvalues.append(spec)
        metafunc.parametrize('spec', argvalues, ids=idlist, indirect=True)


def _generate_specs_from_yml_file(yaml_file):
    """
    Generator providing lists of scenarios from the contents of a yaml file. A scenario is itself a list of Spec
    objects (one Spec per given example)

    :param yaml_file: yaml file describing scenarios
    :return: Generator[List[Spec], None, None]
    """
    boundary = re.compile(r'^-{3,}$', re.MULTILINE)
    with open(yaml_file, 'r') as f:
        text = f.read()
    docker_compose_contents, *scenarios = boundary.split(text)
    for scenario in scenarios:
        try:
            data = yaml.safe_load(scenario)
        except ScannerError as e:
            pytest.fail(str(e), pytrace=False)
        else:
            if "examples" in data:
                scenario = []
                for example in data["examples"]:
                    try:
                        final_docker_compose_contents = _inject_example(docker_compose_contents, example)
                        excepted_uml = _inject_example(data["expected"], example)
                    except ValueError as e:
                        pytest.fail(str(e), pytrace=False)
                    else:
                        scenario.append(Spec(
                            final_docker_compose_contents,
                            data["options"],
                            excepted_uml
                        ))
                yield scenario
            else:
                yield [Spec(docker_compose_contents, data["options"], data["expected"])]


def _inject_example(text, example_data):
    """
    return the given text after replacing its placeholders with provided data

    :param text: text to alter
    :param example_data: Dict[str, str] placeholder->replacement
    :return: altered text

    >>> repr(_inject_example(None, None))
    'None'
    >>> repr(_inject_example("", None))
    "''"
    >>> _inject_example("port: <port>", {"port": "8080"})
    'port: 8080'
    >>> _inject_example("foo <port>\\nbar <label>", {"port": "8080-8099", "label": "baz"})
    'foo 8080-8099\\nbar baz'
    """
    if not text or not example_data:
        return text
    final_text = text
    for placeholder, replacement in example_data.items():
        if not isinstance(placeholder, str):
            raise ValueError("placeholder {!r} should be a string".format(placeholder))
        if not isinstance(replacement, str):
            raise ValueError("replacement {!r} should be a string".format(replacement))
        final_text = final_text.replace("<{}>".format(placeholder), replacement)
    return final_text


###############################################################################
#
# Pytest report customizations
#
###############################################################################

@pytest.mark.optionalhook
def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([html.p("PLANTUML_SERVER: {!r}".format(os.environ.get("PLANTUML_SERVER")))])


@pytest.mark.optionalhook
def pytest_html_results_table_html(report, data):
    def _generate_plantuml_svg(uml):
        if uml:
            try:
                response = plantuml_service.download('svg', uml)
                if response.status_code in (200, 400):
                    svg = response.text
                    return raw(svg)
            except PlantUMLServiceDisabled:
                pass
            return html.a('try on PlantUML demo server', href=PlantUMLService.test_demo_url(uml))

    if hasattr(report, 'user_properties'):
        user_properties = dict(getattr(report, 'user_properties'))
        if 'spec' in user_properties:
            spec = user_properties.get('spec')
            if report.passed:
                del data[:]
            data.append(
                html.div(
                    html.table(
                        html.thead(
                            html.th("docker-compose.yml"),
                            html.th("Options"),
                            html.th("PlantUML"),
                            html.th("Result")
                        ),
                        html.tr(
                            html.td(html.pre(spec.compose)),
                            html.td(html.pre(spec.options)),
                            html.td(html.pre(user_properties.get('resulting_uml'))),
                            html.td(_generate_plantuml_svg(user_properties.get('resulting_uml')))
                        )
                        , width="100%")
                )
            )


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    if pytest_html:
        report = outcome.get_result()
        user_properties = dict(report.user_properties)
        extra = getattr(report, 'extra', [])
        if report.when == 'call':
            extra.append(pytest_html.extras.url(PlantUMLService.test_demo_url(user_properties.get('resulting_uml', '')),
                                                name="try on demo PlantUML server"))
            report.extra = extra


###############################################################################
#
# Global initializations
#
###############################################################################

plantuml_service = PlantUMLService(base_url=os.environ.get('PLANTUML_SERVER'))
