from tests.conftest import Spec

__spec_files__ = './link_graph/spec_*.yml'


def test_specs(spec: Spec):
    spec.run_assertions()
