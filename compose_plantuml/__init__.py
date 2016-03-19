#!/usr/bin/env python3
from yaml import load


class ComposePlantuml:

    def __init__(self):
        pass

    def print_links_from_file(self, path):
        with open(path, 'r') as file:
            self.print_links(file.read())

    def print_links(self, data):
        compose = load(data)

        self.require_version_2(compose)

        for component in sorted(self.components(compose)):
            print('[{0}]'.format(component))
        for source, destination in sorted(self.links(compose)):
            print('[{0}] --> [{1}]'.format(source, destination))

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
    def require_version_2(compose):
        if 'version' not in compose:
            raise VersionException('version not present in {0}'.format(compose))
        if int(compose['version']) != 2:
            raise VersionException('need version 2, but got {0}'.format(compose['version']))


class VersionException(Exception):

    def __init__(self, message):
        self.message = message
