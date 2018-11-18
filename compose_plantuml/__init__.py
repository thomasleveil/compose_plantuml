#!/usr/bin/env python3
import re
from collections import namedtuple
from functools import wraps

from yaml import load


def uml_lines(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        lines = func(*args, **kwds)
        return "\n".join(lines)

    return wrapper


class ComposePlantuml:

    def __init__(self):
        pass

    def parse(self, data):
        return load(data)

    def link_graph(self, compose, notes=False):
        result = 'skinparam componentStyle uml2\n'

        for component in sorted(self.components(compose)):
            result += '[{0}]\n'.format(component)
        for source, destination in sorted(self.links(compose)):
            result += '[{0}] --> [{1}]\n'.format(source, destination)
        for source, destination in sorted(self.dependencies(compose)):
            result += '[{0}] ..> [{1}] : depends on\n'.format(source, destination)
        if notes:
            for component_name in sorted(self.components(compose)):
                component = self.component(compose, component_name)
                if 'labels' in component:
                    labels = []
                    for key, value in component['labels'].items():
                        labels.append('{0}={1}'.format(key, value))
                    result += 'note top of [{0}]\n  {1}\nend note\n'.format(component_name, '\n  '.join(labels))
        return result.strip()

    def boundaries(self, compose, group=False, ports=True, volumes=True, traefik=True, notes=False):
        traefik_parser = TraefikParser(compose)
        result = 'skinparam componentStyle uml2\n'

        result += 'cloud system {\n'
        for component in sorted(self.components(compose)):
            relevant = False
            if ports and self.has_service_external_ports(compose, component):
                relevant = True
            if volumes and self.has_service_volumes(compose, component):
                relevant = True
            if traefik and traefik_parser.has_service_traefik_rule(component):
                relevant = True
            if not relevant:
                continue
            result += '  [{0}]\n'.format(component)
            if not notes:
                continue
            if not self.labels(compose, component):
                continue
            labels = []
            for key, value in self.labels(compose, component).items():
                labels.append('{0}={1}'.format(key, value))
            result += '  note top of [{0}]\n    {1}\n  end note\n'.format(component, '\n    '.join(labels))
        result += '}\n'
        if volumes:
            volume_registry = {}

            volume_uml = ''
            for volume in sorted(self.volumes(compose)):
                if not self.is_volume_used(compose, volume):
                    continue
                volume_uml += 'database {0}'.format(volume) + ' {\n'
                for path in sorted(self.volume_usage(compose, volume)):
                    id = self.volume_identifier(volume, path)

                    if id in volume_registry:
                        continue
                    volume_registry[id] = 'volume_{0}'.format(len(volume_registry.keys()) + 1)
                    volume_uml += '  [{0}] as {1}\n'.format(path, volume_registry[id])

                volume_uml += '}\n'
            result += self.group('volumes', volume_uml) if group else volume_uml

        if ports:
            port_uml = ''
            port_links = ''
            for service, host, container in sorted(self.ports(compose)):
                port = host
                if container is not None:
                    port = '{0} : {1}'.format(host, container)
                host = host.replace('/', '')
                port = port.replace('/', '')
                port_links += '[{0}] --> {1}\n'.format(service, port)
                port_uml += 'interface {0}\n'.format(host)
            result += self.group('ports', port_uml) if group else ''
            result += port_links

        if volumes:
            for volume in sorted(self.volumes(compose)):
                for service, volume_path in sorted(self.service_using_path(compose, volume)):
                    name = volume_path
                    if '{0}.{1}'.format(volume, volume_path) in volume_registry:
                        name = volume_registry['{0}.{1}'.format(volume, volume_path)]
                    result += '[{0}] --> {1}\n'.format(service, name)

        if traefik:
            result += traefik_parser.uml(group)

        return result.strip()

    @staticmethod
    def labels(compose, service):
        service = ComposePlantuml.component(compose, service)
        if 'labels' not in service:
            return None
        if type(service['labels']) is str:
            key, value = service['labels'].split(':')
            return {key: value}
        return service['labels']

    @staticmethod
    def group(name, content):
        if len(content) == 0:
            return ''
        return 'package {0} '.format(name) + '{\n  ' + '\n  '.join(content.split('\n')).strip() + '\n}\n'

    @staticmethod
    def is_volume_used(compose, volume):
        components = compose if 'version' not in compose else compose.get('services', {})

        for _, component in components.items():
            for volume_name in component.get('volumes', {}):
                if volume_name.startswith('{0}:'.format(volume)):
                    return True
        return False

    @staticmethod
    def is_service_used(compose, service):
        components = compose if 'version' not in compose else compose.get('services', {})

        for _, component in components.items():
            for link in component.get('links', []):
                link = link if ':' not in link else link.split(':')[0]
                if link == service:
                    return True

            for dependency in component.get('depends_on', []):
                if dependency == service:
                    return True
        return False

    @staticmethod
    def has_service_external_ports(compose, service):
        components = compose if 'version' not in compose else compose.get('services', {})

        for name, component in components.items():
            if service != name:
                continue
            return 'ports' in component
        return False

    @staticmethod
    def has_service_volumes(compose, service):
        components = compose if 'version' not in compose else compose.get('services', {})

        for name, component in components.items():
            if service != name:
                continue
            if 'volumes' not in component:
                return False
            for volume in component['volumes']:
                if volume.startswith('/'):
                    continue
                if ':' in volume:
                    return True
        return False

    @staticmethod
    def volume_identifier(volume, path):
        return '{0}.{1}'.format(volume, path)

    @staticmethod
    def components(compose):
        if 'version' not in compose:
            return [component for component in compose]
        return [component for component in compose.get('services', {})]

    @staticmethod
    def component(compose, name):
        root = compose if 'version' not in compose else compose['services']

        assert name in root
        return root[name]

    @staticmethod
    def links(compose):
        result = []
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            for link in component.get('links', []):
                link = link if ':' not in link else link.split(':')[0]
                result.append((component_name, link))
        return result

    @staticmethod
    def dependencies(compose):
        result = []
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            for dependency in component.get('depends_on', []):
                result.append((component_name, dependency))
        return result

    @staticmethod
    def ports(compose):
        result = []
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            for port in component.get('ports', []):
                port = str(port).replace('-', '..')
                host, container = (port, None)
                if ':' in port:
                    host, container = port.split(':')
                result.append((component_name, host, container))
        return result

    @staticmethod
    def volumes(compose):
        if 'version' not in compose:
            return []  # TODO: support for version 1
        volumes = compose.get('volumes', {})

        return list(volumes.keys())

    @staticmethod
    def volume_usage(compose, volume):
        result = []
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            for volume_name in component.get('volumes', {}):
                if not volume_name.startswith('{0}:'.format(volume)):
                    continue
                result.append(volume_name.split(':')[1])
        return result

    @staticmethod
    def service_using_path(compose, volume):
        result = []
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            for volume_name in component.get('volumes', {}):
                if not volume_name.startswith('{0}:'.format(volume)):
                    continue
                result.append((component_name, volume_name.split(':')[1]))
        return result


TraefikRule = namedtuple('TraefikRule', ['service', 'rule', 'segment'])


class TraefikParser:
    re_traefik_rule = re.compile(r'''^traefik\.(?:(?P<segment_name>[^.]+)\.)?frontend.rule$''')

    def __init__(self, compose):
        self.rules = None
        self.connections = None
        self.services = set()
        self._take_inventory(compose)

    def _take_inventory(self, compose):
        _rules = set()
        _connections = set()

        for rule_info in TraefikParser._rules_extractor(compose):
            _rules.add(rule_info.rule)
            _connections.add((rule_info.rule, (rule_info.service, rule_info.segment)))
            self.services.add(rule_info.service)

        self.rules = sorted(list(_rules))
        self.connections = []
        for rule, destination in _connections:
            self.connections.append((self.rules.index(rule), destination))

    @staticmethod
    def _rules_extractor(compose):
        components = compose if 'version' not in compose else compose.get('services', {})

        for component_name, component in components.items():
            labels_dict = (component or {}).get('labels', {})
            if not isinstance(labels_dict, dict):
                raise ValueError("Incorrect yml format. `labels:` should be a dict. Got <{}> {!r}".format(
                    labels_dict.__class__.__name__, labels_dict)
                )
            for label_key, label_value in labels_dict.items():
                m = TraefikParser.re_traefik_rule.match(label_key)
                if m:
                    rule = label_value
                    yield TraefikRule(component_name, rule, m.group('segment_name') or " ")

    def has_service_traefik_rule(self, service):
        return service in self.services

    def uml_for_rules(self):
        return ['interface "{}" as traefik_rule_{}'.format(rule, index) for index, rule in enumerate(self.rules)]

    def uml_for_connections(self):
        return sorted(['traefik_rule_{} ~~0 [{}] : "{}"'.format(rule_index, service, segment) for
                       rule_index, (service, segment) in self.connections])

    @uml_lines
    def uml(self, group=False):
        if group and len(self.uml_for_rules()):
            return ["package Traefik {"] \
                   + self.uml_for_rules() \
                   + ["}"] \
                   + self.uml_for_connections()
        else:
            return self.uml_for_rules() + self.uml_for_connections()
