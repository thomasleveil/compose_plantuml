#!/usr/bin/env python3
from yaml import load


class ComposePlantuml:

    def __init__(self):
        pass

    def parse(self, data):
        return load(data)

    def link_graph(self, compose):
        result = 'skinparam componentStyle uml2\n'

        for component in sorted(self.components(compose)):
            result += '[{0}]\n'.format(component)
        for source, destination in sorted(self.links(compose)):
            result += '[{0}] --> [{1}]\n'.format(source, destination)
        for source, destination in sorted(self.dependencies(compose)):
            result += '[{0}] ..> [{1}] : depends on\n'.format(source, destination)
        return result.strip()

    def boundaries(self, compose, group=False):
        result = 'skinparam componentStyle uml2\n'

        result += 'cloud system {\n'
        for component in sorted(self.components(compose)):
            if self.has_service_external_ports(compose, component) or self.has_service_volumes(compose, component):
                result += '  [{0}]\n'.format(component)
        result += '}\n'
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

        port_uml = ''
        port_links = ''
        for service, host, container in sorted(self.ports(compose)):
            port = host
            if container is not None:
                port = '{0} : {1}'.format(host, container)
            port_links += '[{0}] --> {1}\n'.format(service, port)
            port_uml += 'interface {0}\n'.format(port)
        result += self.group('ports', port_uml) if group else ''
        result += port_links

        for volume in sorted(self.volumes(compose)):
            for service, volume_path in sorted(self.service_using_path(compose, volume)):
                name = volume_path
                if '{0}.{1}'.format(volume, volume_path) in volume_registry:
                    name = volume_registry['{0}.{1}'.format(volume, volume_path)]
                result += '[{0}] --> {1}\n'.format(service, name)
        return result.strip()

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
        return [component for component in compose.get('services', [])]

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
                port = str(port)
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
