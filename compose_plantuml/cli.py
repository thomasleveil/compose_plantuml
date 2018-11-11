#!/usr/bin/env python3
import argparse

from . import ComposePlantuml


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--link-graph', action='store_const', const=True,
        help='prints a link graph', default=False, )
    parser.add_argument(
        '--boundaries', action='store_const', const=True,
        help='prints the system boundaries',
        default=False,
    )
    parser.add_argument(
        '--port_boundaries', action='store_const', const=True,
        help='prints the port system boundaries',
        default=False,
    )
    parser.add_argument(
        '--volume_boundaries', action='store_const', const=True,
        help='prints the port system boundaries',
        default=False,
    )
    parser.add_argument(
        '--traefik_boundaries', action='store_const', const=True,
        help='prints the Traefik rules system boundaries',
        default=False,
    )
    parser.add_argument(
        '--notes', action='store_const', const=True,
        help='utilize notes for displaying additional information',
        default=False,
    )
    parser.add_argument(
        '--group', action='store_const', const=True,
        help='group similar properties together',
        default=False,
    )
    parser.add_argument('files', nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def execute(data, args):
    plantuml = ComposePlantuml()
    parsed = plantuml.parse(data)
    output = ''

    if args.link_graph:
        output += plantuml.link_graph(parsed, notes=args.notes)
    if args.boundaries:
        output += plantuml.boundaries(parsed, args.group, notes=args.notes)
    if args.port_boundaries:
        output += plantuml.boundaries(parsed, args.group, notes=args.notes, ports=True, volumes=False, traefik=False)
    if args.volume_boundaries:
        output += plantuml.boundaries(parsed, args.group, notes=args.notes, ports=False, volumes=True, traefik=False)
    if args.traefik_boundaries:
        output += plantuml.boundaries(parsed, args.group, notes=args.notes, ports=False, volumes=False, traefik=True)

    return output
