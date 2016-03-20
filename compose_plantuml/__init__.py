#!/usr/bin/env python3
from yaml import load


class ComposePlantuml:

    def __init__(self):
        pass

    def parse(self, data):
        compose = load(data)

        self.require_version_2(compose)
        return compose

    def link_graph(self, compose):
        result = 'skinparam componentStyle uml2\n'

        for component in sorted(self.components(compose)):
            result += '[{0}]\n'.format(component)
        for source, destination in sorted(self.links(compose)):
            result += '[{0}] --> [{1}]\n'.format(source, destination)
        return result.strip()

    def boundaries(self, compose):
        result = 'skinparam componentStyle uml2\n'

        result += 'rectangle system {\n'
        for component in sorted(self.components(compose)):
            result += '  [{0}]\n'.format(component)
        result += '}\n'
        for service, host, container in sorted(self.ports(compose)):
            port = host
            if container is not None:
                port = '{0} : {1}'.format(host, container)
            result += '[{0}] --> {1}\n'.format(service, port)
        return result.strip()

    @staticmethod
    def components(compose):
        return [component for component in compose.get('services', [])]

    @staticmethod
    def links(compose):
        result = []

        for component_name in compose.get('services', []):
            component = compose['services'][component_name]

            for link in component.get('links', []):
                link = link if ':' not in link else link.split(':')[0]
                result.append((component_name, link))
        return result

    @staticmethod
    def ports(compose):
        result = []

        for component_name in compose.get('services', []):
            component = compose['services'][component_name]

            for port in component.get('ports', []):
                port = str(port)
                host, container = (port, None)
                if ':' in port:
                    host, container = port.split(':')
                result.append((component_name, host, container))
        return result

    @staticmethod
    def require_version_2(compose):
        if 'version' not in compose:
            raise VersionException('version not present in {0}'.format(compose))
        if int(compose['version']) != 2:
            raise VersionException('need version 2, but got {0}'.format(compose['version']))


class VersionException(Exception):

    def __init__(self, message):
        self.message = message
