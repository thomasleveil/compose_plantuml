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
        if 'version' not in compose:
            return [component for component in compose]
        return [component for component in compose.get('services', [])]

    @staticmethod
    def links(compose):
        result = []
        components = compose if 'version' not in compose else compose.get('services', [])

        for component_name, component in components.items():
            for link in component.get('links', []):
                link = link if ':' not in link else link.split(':')[0]
                result.append((component_name, link))
        return result

    @staticmethod
    def ports(compose):
        result = []
        components = compose if 'version' not in compose else compose.get('services', [])

        for component_name, component in components.items():
            for port in component.get('ports', []):
                port = str(port)
                host, container = (port, None)
                if ':' in port:
                    host, container = port.split(':')
                result.append((component_name, host, container))
        return result
