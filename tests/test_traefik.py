from yaml import load

from compose_plantuml import TraefikParser
from tests.conftest import Spec

__spec_files__ = './traefik/spec_*.yml'


def test_specs(spec: Spec):
    spec.run_assertions()


def test_traefik_rules_single():
    traefik = TraefikParser(load("""
        version: "2"
        services:
            service:
                labels:
                    traefik.frontend.rule: Host:patate.com
    """))
    assert ["Host:patate.com"] == traefik.rules
    assert [(0, ('service', ' '))] == traefik.connections
    assert '''\
interface "Host:patate.com" as traefik_rule_0
traefik_rule_0 ~~0 [service] : " "''' == traefik.uml()
    assert '''\
package Traefik {
interface "Host:patate.com" as traefik_rule_0
}
traefik_rule_0 ~~0 [service] : " "''' == traefik.uml(group=True)


def test_traefik_rules_multiple():
    traefik = TraefikParser(load("""
        version: "2"
        services:
            service1:
                labels:
                    traefik.frontend.rule: Host:patate.com
            service2:
                labels:
                    traefik.frontend.rule: Host:bar.com
    """))
    assert ["Host:bar.com", "Host:patate.com"] == traefik.rules
    assert {
               (0, ('service2', ' ')),
               (1, ('service1', ' ')),
           } == set(traefik.connections)


def test_traefik_rules_single_with_segment():
    traefik = TraefikParser(load("""
        version: "2"
        services:
            service:
                labels:
                    traefik.foo.frontend.rule: Host:patate.com
    """))
    assert ["Host:patate.com"] == traefik.rules
    assert [
               (0, ('service', 'foo')),
           ] == traefik.connections


def test_traefik_rules_single_with_multiple_segments():
    traefik = TraefikParser(load("""
        version: "2"
        services:
            service:
                labels:
                    traefik.foo.frontend.rule: Host:foo.com
                    traefik.bar.frontend.rule: Host:bar.com
            service2:
                labels:
                    traefik.foo.frontend.rule: Host:foo.com
                    traefik.bar.frontend.rule: Host:bar.com
    """))
    assert [
               "Host:bar.com",
               "Host:foo.com",
           ] == traefik.rules
    assert {
               (1, ('service', 'foo')),
               (0, ('service', 'bar')),
               (1, ('service2', 'foo')),
               (0, ('service2', 'bar')),
           } == set(traefik.connections)
    assert '''\
interface "Host:bar.com" as traefik_rule_0
interface "Host:foo.com" as traefik_rule_1
traefik_rule_0 ~~0 [service2] : "bar"
traefik_rule_0 ~~0 [service] : "bar"
traefik_rule_1 ~~0 [service2] : "foo"
traefik_rule_1 ~~0 [service] : "foo"''' == traefik.uml()

    assert '''\
package Traefik {
interface "Host:bar.com" as traefik_rule_0
interface "Host:foo.com" as traefik_rule_1
}
traefik_rule_0 ~~0 [service2] : "bar"
traefik_rule_0 ~~0 [service] : "bar"
traefik_rule_1 ~~0 [service2] : "foo"
traefik_rule_1 ~~0 [service] : "foo"''' == traefik.uml(group=True)


def test_traefik_rules_single_mixed():
    traefik = TraefikParser(load("""
        version: "2"
        services:
            service:
                labels:
                    traefik.frontend.rule: Host:hello.com,Path:/hello
                    traefik.foo.frontend.rule: Host:patate.com
    """))
    assert ["Host:hello.com,Path:/hello", "Host:patate.com"] == traefik.rules
    assert {
               (0, ('service', ' ')),
               (1, ('service', 'foo')),
           } == set(traefik.connections)
    assert '''\
interface "Host:hello.com,Path:/hello" as traefik_rule_0
interface "Host:patate.com" as traefik_rule_1
traefik_rule_0 ~~0 [service] : " "
traefik_rule_1 ~~0 [service] : "foo"''' == traefik.uml()
